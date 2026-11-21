"""Reproducible, offline provenance records for MSD MusicNN inference."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Mapping

from .msd_tags import MSD_TAGS


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_sha256(value: object) -> str:
    try:
        payload = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("provenance values must be finite JSON-compatible data") from exc
    return hashlib.sha256(payload).hexdigest()


def inspect_checkpoint_dtypes(checkpoint_path: str | Path) -> dict[str, object]:
    """Safely inspect local state-dict tensor types without executing pickle code."""
    path = Path(checkpoint_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    try:
        import torch
    except ImportError as exc:  # pragma: no cover
        raise ImportError("install body-of-secrets[musicnn] to inspect checkpoints") from exc

    try:
        state = torch.load(path, map_location="cpu", weights_only=True)
    except TypeError as exc:
        raise RuntimeError("PyTorch with weights_only=True support is required") from exc
    if not isinstance(state, Mapping):
        raise TypeError("checkpoint must contain a state-dict mapping")

    counts: dict[str, int] = {}
    running_stats: dict[str, str] = {}
    tracked: dict[str, str] = {}
    for name, tensor in state.items():
        if not isinstance(name, str) or not isinstance(tensor, torch.Tensor):
            raise TypeError("checkpoint state dict must map string keys to tensors")
        dtype = str(tensor.dtype).removeprefix("torch.")
        counts[dtype] = counts.get(dtype, 0) + 1
        if name.endswith(("running_mean", "running_var")):
            running_stats[name] = dtype
        elif name.endswith("num_batches_tracked"):
            tracked[name] = dtype

    return {
        "checkpoint_sha256": _sha256_file(path),
        "checkpoint_bytes": path.stat().st_size,
        "tensor_count": len(state),
        "dtype_tensor_counts": dict(sorted(counts.items())),
        "batch_norm_running_stats": dict(sorted(running_stats.items())),
        "batch_norm_num_batches_tracked": dict(sorted(tracked.items())),
    }


def build_musicnn_provenance(
    checkpoint_path: str | Path,
    preprocessing: Mapping[str, object],
    *,
    integration_commit_sha: str,
) -> dict[str, object]:
    """Build a run record; verification flags intentionally remain false."""
    if not re.fullmatch(r"[0-9a-fA-F]{40,64}", integration_commit_sha):
        raise ValueError("integration_commit_sha must be a 40- or 64-character hex SHA")
    frontend = dict(preprocessing)
    # Validate canonical serialization before recording the configuration.
    frontend_sha = _canonical_sha256(frontend)
    checkpoint = inspect_checkpoint_dtypes(checkpoint_path)
    if checkpoint["tensor_count"] != 75:
        raise ValueError("expected the standard MSD MusicNN checkpoint with 75 tensors")
    tags_sha = _canonical_sha256(list(MSD_TAGS))

    running = checkpoint["batch_norm_running_stats"]
    tracked = checkpoint["batch_norm_num_batches_tracked"]
    if not isinstance(running, Mapping) or not isinstance(tracked, Mapping):
        raise RuntimeError("checkpoint dtype inventory is malformed")
    if len(running) != 22 or any(dtype != "float32" for dtype in running.values()):
        raise ValueError("checkpoint BatchNorm running statistics are not all FP32")
    if len(tracked) != 11 or any(dtype != "int64" for dtype in tracked.values()):
        raise ValueError("checkpoint BatchNorm tracking tensors are not 11 int64 values")

    return {
        "model": "MSD MusicNN standard",
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "checkpoint_bytes": checkpoint["checkpoint_bytes"],
        "checkpoint_tensor_count": checkpoint["tensor_count"],
        "checkpoint_dtype_tensor_counts": checkpoint["dtype_tensor_counts"],
        "batch_norm_running_stats": checkpoint["batch_norm_running_stats"],
        "batch_norm_num_batches_tracked": checkpoint["batch_norm_num_batches_tracked"],
        "preprocessing": frontend,
        "preprocessing_sha256": frontend_sha,
        "tag_vocabulary_sha256": tags_sha,
        "integration_commit_sha": integration_commit_sha.lower(),
        "weights_redistribution_status": "UNRESOLVED_NOT_REDISTRIBUTED",
        "numerical_equivalence_verified": False,
        "preprocessing_parity_verified": False,
        "tag_quality_validated": False,
        "truth_status": "UNKNOWN",
    }
