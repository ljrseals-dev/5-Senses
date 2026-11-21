"""Tests for checkpoint and run provenance."""
from __future__ import annotations

import pytest

torch = pytest.importorskip("torch")

from body_of_secrets.sensory.musicnn_frontend import preprocessing_record  # noqa: E402
from body_of_secrets.sensory.musicnn_msd import MusicnnMSD  # noqa: E402
from body_of_secrets.sensory.musicnn_provenance import (  # noqa: E402
    build_musicnn_provenance,
    inspect_checkpoint_dtypes,
)


def make_fp16_checkpoint(path):
    state = MusicnnMSD().state_dict()
    for name, tensor in list(state.items()):
        if name.endswith(("running_mean", "running_var")):
            state[name] = tensor.float()
        elif name.endswith("num_batches_tracked"):
            state[name] = tensor.to(torch.int64)
        elif tensor.is_floating_point():
            state[name] = tensor.half()
    torch.save(state, path)


def test_dtype_inventory_reports_every_batch_norm_buffer(tmp_path):
    checkpoint = tmp_path / "mixed-precision.pt"
    make_fp16_checkpoint(checkpoint)
    report = inspect_checkpoint_dtypes(checkpoint)

    assert report["tensor_count"] == 75
    assert len(report["batch_norm_running_stats"]) == 22
    assert len(report["batch_norm_num_batches_tracked"]) == 11
    assert set(report["batch_norm_running_stats"].values()) == {"float32"}
    assert set(report["batch_norm_num_batches_tracked"].values()) == {"int64"}
    assert report["dtype_tensor_counts"]["float16"] > 0
    assert len(report["checkpoint_sha256"]) == 64


def test_provenance_record_hashes_frontend_and_vocab(tmp_path):
    checkpoint = tmp_path / "mixed-precision.pt"
    make_fp16_checkpoint(checkpoint)
    record = build_musicnn_provenance(
        checkpoint,
        preprocessing_record(),
        integration_commit_sha="b" * 40,
    )

    assert record["integration_commit_sha"] == "b" * 40
    assert len(record["preprocessing_sha256"]) == 64
    assert len(record["tag_vocabulary_sha256"]) == 64
    assert record["numerical_equivalence_verified"] is False
    assert record["preprocessing_parity_verified"] is False
    assert record["tag_quality_validated"] is False
    assert record["truth_status"] == "UNKNOWN"


def test_provenance_rejects_invalid_commit_sha_and_non_json_config(tmp_path):
    checkpoint = tmp_path / "mixed-precision.pt"
    make_fp16_checkpoint(checkpoint)
    with pytest.raises(ValueError, match="commit SHA"):
        build_musicnn_provenance(
            checkpoint, preprocessing_record(), integration_commit_sha="bad"
        )
    with pytest.raises(ValueError, match="JSON-compatible"):
        build_musicnn_provenance(
            checkpoint, {"bad": object()}, integration_commit_sha="b" * 40
        )
