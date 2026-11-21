"""Tests for MusicNN-to-classical subsystem adapters."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from body_of_secrets.archive import Archive  # noqa: E402
from body_of_secrets.expert import ExpertSystem  # noqa: E402
from body_of_secrets.language import NGramModel  # noqa: E402
from body_of_secrets.neural import HopfieldNetwork, MLP  # noqa: E402
from body_of_secrets.sensory.msd_tags import MSD_TAGS  # noqa: E402
from body_of_secrets.sensory.musicnn_frontend import preprocessing_record  # noqa: E402
from body_of_secrets.sensory.musicnn_msd import MusicnnMSD  # noqa: E402
from body_of_secrets.sensory.musicnn_provenance import build_musicnn_provenance  # noqa: E402
from body_of_secrets.sensory.musicnn_adapters import (  # noqa: E402
    archive_musicnn_analysis,
    confirmed_hopfield_pattern,
    musicnn_mlp_features,
    predict_msd_tags,
    register_musicnn_caution_rule,
    train_mlp_from_confirmed_tags,
    train_ngram_from_confirmed_tags,
)


class FixedLogitModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.anchor = torch.nn.Parameter(torch.zeros(1))

    def forward(self, batch):
        return torch.zeros((batch.shape[0], 50), device=batch.device, dtype=batch.dtype)


def test_tag_vocabulary_is_exactly_50_unique_ordered_labels():
    assert len(MSD_TAGS) == 50
    assert len(set(MSD_TAGS)) == 50
    assert MSD_TAGS[0] == "rock"
    assert MSD_TAGS[-1] == "happy"


def test_prediction_returns_stable_top_k_and_all_features():
    result = predict_msd_tags(FixedLogitModel(), torch.zeros((2, 187, 96)), top_k=3)
    assert result.patch_count == 2
    assert len(result.patch_scores) == 2
    assert [score.label for score in result.mean_scores] == list(MSD_TAGS[:3])
    assert len(musicnn_mlp_features(result)) == 50
    assert musicnn_mlp_features(result) == [0.5] * 50


def test_prediction_rejects_bad_shapes_and_top_k():
    with pytest.raises(ValueError, match="patches"):
        predict_msd_tags(FixedLogitModel(), torch.zeros((1, 187, 80)))
    with pytest.raises(ValueError, match="top_k"):
        predict_msd_tags(FixedLogitModel(), torch.zeros((1, 187, 96)), top_k=0)


def test_only_human_confirmed_labels_feed_classical_learning():
    result = predict_msd_tags(FixedLogitModel(), torch.zeros((1, 187, 96)))
    mlp = MLP(n_input=50, n_hidden=8, n_output=50)
    trained = train_mlp_from_confirmed_tags(
        mlp, result, ["rock", "jazz"], confirmation_source="human-reviewed fixture"
    )
    assert trained.confirmed_tags == ("rock", "jazz")
    assert trained.loss is not None

    pattern = confirmed_hopfield_pattern(["rock", "jazz"])
    assert len(pattern) == 50
    assert pattern[MSD_TAGS.index("rock")] == 1
    assert pattern[MSD_TAGS.index("jazz")] == 1
    assert pattern[MSD_TAGS.index("pop")] == -1
    network = HopfieldNetwork(n_units=50)
    network.store([pattern])
    assert len(network.recall(pattern)) == 50

    ngram = NGramModel(n=2)
    record = train_ngram_from_confirmed_tags(
        ngram, ["rock", "jazz"], confirmation_source="human-reviewed fixture"
    )
    assert record.confirmation_source == "human-reviewed fixture"
    assert ngram.vocab == {"rock", "jazz"}


def test_unknown_or_unconfirmed_tags_cannot_train():
    result = predict_msd_tags(FixedLogitModel(), torch.zeros((1, 187, 96)))
    with pytest.raises(ValueError, match="unknown MSD tags"):
        train_mlp_from_confirmed_tags(
            MLP(50, 4, 50), result, ["not-a-tag"], confirmation_source="review"
        )
    with pytest.raises(ValueError, match="required"):
        train_ngram_from_confirmed_tags(NGramModel(), ["rock"], confirmation_source="")


def test_expert_rule_keeps_predictions_unknown():
    expert = ExpertSystem()
    assert register_musicnn_caution_rule(expert) is True
    assert register_musicnn_caution_rule(expert) is False
    result = expert.first_match("Explain MSD MusicNN tags")
    assert result is not None
    assert "[UNKNOWN]" in result.output


def test_archive_record_contains_hashes_and_unknown_status(tmp_path):
    result = predict_msd_tags(FixedLogitModel(), torch.zeros((1, 187, 96)))
    audio = tmp_path / "fixture.wav"
    audio.write_bytes(b"local test audio bytes")
    checkpoint = tmp_path / "checkpoint.pt"
    torch.save(MusicnnMSD().state_dict(), checkpoint)
    provenance = build_musicnn_provenance(
        checkpoint,
        preprocessing_record(),
        integration_commit_sha="a" * 40,
    )
    checkpoint_hash = provenance["checkpoint_sha256"]
    with Archive(tmp_path / "archive.db") as archive:
        doc_id = archive_musicnn_analysis(
            archive, result, audio, provenance=provenance
        )
        document = archive.get(doc_id)

    assert document is not None
    assert document.metadata["truth_status"] == "UNKNOWN"
    assert document.metadata["tag_quality_validated"] is False
    assert document.metadata["checkpoint_sha256"] == checkpoint_hash
    assert document.metadata["musicnn_provenance"]["integration_commit_sha"] == "a" * 40
    assert document.metadata["musicnn_provenance"]["numerical_equivalence_verified"] is False
    assert len(document.metadata["audio_sha256"]) == 64
    assert len(document.content.splitlines()) >= 53
