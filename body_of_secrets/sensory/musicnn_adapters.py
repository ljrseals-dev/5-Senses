"""Explicit adapters from MSD MusicNN outputs into classical 5-Senses modules.

Raw model predictions remain UNKNOWN. MLP, Hopfield, and n-gram learning only
accept labels that a caller explicitly supplies as human-confirmed.
"""
from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Iterable, Mapping, Sequence

from .msd_tags import MSD_TAGS

if TYPE_CHECKING:
    from body_of_secrets.archive import Archive
    from body_of_secrets.expert import ExpertSystem
    from body_of_secrets.language import NGramModel
    from body_of_secrets.neural import HopfieldNetwork, MLP


@dataclass(frozen=True)
class TagScore:
    index: int
    label: str
    probability: float
    logit: float


@dataclass(frozen=True)
class MusicNNAnalysis:
    patch_scores: tuple[tuple[TagScore, ...], ...]
    mean_scores: tuple[TagScore, ...]
    mean_probabilities: tuple[float, ...]
    patch_count: int


@dataclass(frozen=True)
class ConfirmedTagTraining:
    confirmation_source: str
    confirmed_tags: tuple[str, ...]
    loss: float | None = None


def _validate_top_k(top_k: int) -> None:
    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise TypeError("top_k must be an integer")
    if not 1 <= top_k <= len(MSD_TAGS):
        raise ValueError("top_k must be between 1 and 50")


def _scores(
    probabilities: Sequence[float],
    logits: Sequence[float],
    top_k: int,
) -> tuple[TagScore, ...]:
    _validate_top_k(top_k)
    if len(probabilities) != len(MSD_TAGS) or len(logits) != len(MSD_TAGS):
        raise ValueError("expected exactly 50 probabilities and logits")
    scores = [
        TagScore(i, label, float(probabilities[i]), float(logits[i]))
        for i, label in enumerate(MSD_TAGS)
    ]
    scores.sort(key=lambda item: (-item.probability, item.index))
    return tuple(scores[:top_k])


def predict_msd_tags(model: object, patches: object, *, top_k: int = 10) -> MusicNNAnalysis:
    """Run local model inference and average sigmoid probabilities across patches."""
    _validate_top_k(top_k)
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise ImportError("install body-of-secrets[musicnn] to run MSD inference") from exc

    try:
        parameter = next(
            (
                module.weight
                for module in model.modules()  # type: ignore[attr-defined]
                if isinstance(module, (torch.nn.Conv2d, torch.nn.Linear))
            ),
            None,
        )
        if parameter is None:
            parameter = next(model.parameters())  # type: ignore[attr-defined]
    except (AttributeError, StopIteration) as exc:
        raise TypeError("model must be a parameterized MusicNN model") from exc

    batch = torch.as_tensor(patches, dtype=parameter.dtype, device=parameter.device)
    if batch.ndim == 2:
        batch = batch.unsqueeze(0)
    if batch.ndim != 3 or batch.shape[0] < 1 or batch.shape[2] != 96:
        raise ValueError("patches must have shape (patches, frames, 96)")
    model.eval()  # type: ignore[attr-defined]
    with torch.inference_mode():
        raw_logits = model(batch)  # type: ignore[operator]
        if raw_logits.ndim != 2 or raw_logits.shape != (batch.shape[0], 50):
            raise ValueError("MusicNN model must return logits shaped (patches, 50)")
        logits = raw_logits.float()
        if not torch.isfinite(logits).all():
            raise ValueError("MusicNN produced non-finite logits")
        probabilities = torch.sigmoid(logits)
        patch_probs = probabilities.cpu().tolist()
        patch_logits = logits.cpu().tolist()
        mean_probs = probabilities.mean(dim=0).cpu().tolist()

    patch_scores = tuple(
        _scores(p, l, top_k) for p, l in zip(patch_probs, patch_logits)
    )
    mean_logits = [
        math.log(
            min(max(p, 1e-7), 1.0 - 1e-7)
            / (1.0 - min(max(p, 1e-7), 1.0 - 1e-7))
        )
        for p in mean_probs
    ]
    return MusicNNAnalysis(
        patch_scores=patch_scores,
        mean_scores=_scores(mean_probs, mean_logits, top_k),
        mean_probabilities=tuple(float(p) for p in mean_probs),
        patch_count=len(patch_probs),
    )


def musicnn_mlp_features(analysis: MusicNNAnalysis) -> list[float]:
    """Return the 50 mean probabilities as MLP input features, not target labels."""
    if len(analysis.mean_probabilities) != 50:
        raise ValueError("analysis must contain 50 mean probabilities")
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in analysis.mean_probabilities
    ):
        raise ValueError("analysis probabilities must be finite values in [0, 1]")
    return list(analysis.mean_probabilities)


def _confirmed_tags(tags: Iterable[str]) -> tuple[str, ...]:
    if isinstance(tags, (str, bytes)):
        raise TypeError("confirmed_tags must be an iterable of complete tag labels")
    selected = tuple(dict.fromkeys(tags))
    if any(not isinstance(tag, str) for tag in selected):
        raise TypeError("confirmed tag labels must be strings")
    unknown = sorted(set(selected) - set(MSD_TAGS))
    if unknown:
        raise ValueError(f"unknown MSD tags: {unknown}")
    if not selected:
        raise ValueError("at least one human-confirmed tag is required")
    return selected


def train_mlp_from_confirmed_tags(
    mlp: MLP,
    analysis: MusicNNAnalysis,
    confirmed_tags: Iterable[str],
    *,
    confirmation_source: str,
) -> ConfirmedTagTraining:
    """Perform one supervised MLP step using explicit human-confirmed targets."""
    selected = _confirmed_tags(confirmed_tags)
    if not confirmation_source.strip():
        raise ValueError("confirmation_source is required for provenance")
    if mlp.n_input != 50 or mlp.n_output != 50:
        raise ValueError("MSD adapter requires an MLP with 50 inputs and 50 outputs")
    loss = mlp.train_step(
        musicnn_mlp_features(analysis),
        [1.0 if tag in selected else 0.0 for tag in MSD_TAGS],
    )
    return ConfirmedTagTraining(confirmation_source, selected, float(loss))


def confirmed_hopfield_pattern(confirmed_tags: Iterable[str]) -> list[int]:
    """Create a bipolar 50-unit pattern from human-confirmed tags only."""
    selected = set(_confirmed_tags(confirmed_tags))
    return [1 if label in selected else -1 for label in MSD_TAGS]


def train_ngram_from_confirmed_tags(
    model: NGramModel,
    confirmed_tags: Iterable[str],
    *,
    confirmation_source: str,
) -> ConfirmedTagTraining:
    """Train the n-gram model on explicit human-confirmed tag sequences only."""
    selected = _confirmed_tags(confirmed_tags)
    if not confirmation_source.strip():
        raise ValueError("confirmation_source is required for provenance")
    model.train([" ".join(selected)])
    return ConfirmedTagTraining(confirmation_source, selected)


def register_musicnn_caution_rule(expert: ExpertSystem) -> bool:
    """Register a rule that explicitly prevents model tags becoming factual claims."""
    name = "musicnn_unverified_output"
    if any(rule.name == name for rule in expert.rules):
        return False

    def caution(match: re.Match[str], text: str) -> str:
        return (
            "MSD MusicNN labels are model-generated candidate annotations, not "
            "verified facts about the recording. Numerical parity and musical "
            "tag quality have not been established. Human review and independent "
            "evidence are required. [UNKNOWN]"
        )

    expert.add_rule(
        name,
        r"\b(MSD\s+MusicNN|MusicNN\s+tags?|music\s+tag\s+predictions?)\b",
        caution,
        priority=1,
        description="Keep MusicNN outputs explicitly unverified",
    )
    return True


def archive_musicnn_analysis(
    archive: Archive,
    analysis: MusicNNAnalysis,
    audio_path: str | Path,
    *,
    provenance: Mapping[str, object],
) -> str:
    """Archive an analysis with full provenance and UNKNOWN status."""
    checkpoint_sha256 = provenance.get("checkpoint_sha256")
    integration_commit_sha = provenance.get("integration_commit_sha")
    if not isinstance(checkpoint_sha256, str) or not re.fullmatch(
        r"[0-9a-fA-F]{64}", checkpoint_sha256
    ):
        raise ValueError("provenance must contain a 64-character checkpoint SHA-256")
    if not isinstance(integration_commit_sha, str) or not re.fullmatch(
        r"[0-9a-fA-F]{40,64}", integration_commit_sha
    ):
        raise ValueError("provenance must contain an integration commit SHA")
    for hash_name in ("preprocessing_sha256", "tag_vocabulary_sha256"):
        hash_value = provenance.get(hash_name)
        if not isinstance(hash_value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", hash_value):
            raise ValueError(f"provenance must contain a valid {hash_name}")
    if not isinstance(provenance.get("preprocessing"), Mapping):
        raise ValueError("provenance must include the resolved preprocessing configuration")
    if provenance.get("truth_status") != "UNKNOWN":
        raise ValueError("MusicNN archive records must remain UNKNOWN")
    for flag in (
        "numerical_equivalence_verified",
        "preprocessing_parity_verified",
        "tag_quality_validated",
    ):
        if provenance.get(flag) is not False:
            raise ValueError(f"unverified MusicNN gate must remain false: {flag}")
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    if analysis.patch_count < 1 or len(analysis.mean_probabilities) != 50:
        raise ValueError("analysis must contain at least one patch and all 50 scores")
    if any(
        not math.isfinite(value) or not 0.0 <= value <= 1.0
        for value in analysis.mean_probabilities
    ):
        raise ValueError("analysis probabilities must be finite values in [0, 1]")
    digest = hashlib.sha256()
    with path.open("rb") as audio_file:
        for chunk in iter(lambda: audio_file.read(1024 * 1024), b""):
            digest.update(chunk)
    audio_sha256 = digest.hexdigest()

    lines = [
        "MSD MusicNN model-generated candidate tags.",
        "TRUTH_STATUS: UNKNOWN",
        "These outputs are not human-verified musical facts.",
        f"Patch count: {analysis.patch_count}",
        "",
    ]
    if len(analysis.mean_probabilities) != len(MSD_TAGS):
        raise ValueError("analysis must contain all 50 mean probabilities")
    lines.extend(
        f"{label}: {probability:.8f}"
        for label, probability in zip(MSD_TAGS, analysis.mean_probabilities)
    )
    metadata = {
        "subsystem": "ears",
        "model": "MSD MusicNN standard",
        "audio_sha256": audio_sha256,
        "checkpoint_sha256": checkpoint_sha256.lower(),
        "patch_count": analysis.patch_count,
        "truth_status": "UNKNOWN",
        "tag_quality_validated": False,
        "musicnn_provenance": dict(provenance),
    }
    return archive.import_document(
        title=f"MSD MusicNN analysis {audio_sha256[:12]}",
        content="\n".join(lines),
        source=f"sha256:{audio_sha256}",
        tags=["ears", "musicnn", "model-output", "unverified"],
        metadata=metadata,
        doc_id=(
            f"musicnn_{audio_sha256[:12]}_{checkpoint_sha256[:8]}_"
            f"{str(provenance.get('preprocessing_sha256', 'unknown'))[:8]}_"
            f"{integration_commit_sha[:8]}"
        ),
    )
