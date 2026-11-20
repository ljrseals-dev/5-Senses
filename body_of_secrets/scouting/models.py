"""Discover and optionally acquire pretrained model artifacts.

Discovery is metadata-only. Downloads are explicit, pinned to a revision, and kept
outside the source tree. This module never executes model-provided code.
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ModelCandidate:
    repo_id: str
    downloads: int | None = None
    likes: int | None = None
    pipeline_tag: str | None = None
    library_name: str | None = None
    last_modified: str | None = None
    tags: tuple[str, ...] = ()

    @classmethod
    def from_api(cls, item: dict[str, Any]) -> "ModelCandidate":
        return cls(repo_id=str(item["id"]), downloads=item.get("downloads"),
                   likes=item.get("likes"), pipeline_tag=item.get("pipeline_tag"),
                   library_name=item.get("library_name"), last_modified=item.get("lastModified"),
                   tags=tuple(item.get("tags") or ()))


def search_models(query: str, *, limit: int = 20, timeout: float = 20.0) -> list[ModelCandidate]:
    """Search the public Hugging Face model catalog; no weights are downloaded."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    params = urllib.parse.urlencode({"search": query, "limit": limit, "sort": "downloads", "direction": -1})
    request = urllib.request.Request(f"https://huggingface.co/api/models?{params}",
                                    headers={"User-Agent": "5-Senses-Boy-Scout/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("unexpected model catalog response")
    return [ModelCandidate.from_api(item) for item in payload
            if isinstance(item, dict) and item.get("id")]


def write_model_inventory(candidates: list[ModelCandidate], destination: str | Path) -> Path:
    """Write a deterministic JSON inventory; never overwrites an existing file."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    payload = {"schema_version": 1, "asset_kind": "pretrained_model_candidate",
               "warning": "Catalog metadata is not proof of license compatibility or local availability.",
               "models": [asdict(item) for item in candidates]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def acquire_model(repo_id: str, destination: str | Path, *, revision: str) -> Path:
    """Download a pinned snapshot after explicit invocation; remote code is not enabled.

    The caller must review the model card and license before invoking this function.
    """
    if not repo_id.strip() or not revision.strip():
        raise ValueError("repo_id and an immutable revision are required")
    target = Path(destination)
    target.mkdir(parents=True, exist_ok=True)
    if any(target.iterdir()):
        raise FileExistsError(f"refusing to download into non-empty directory: {target}")
    try:
        from huggingface_hub import snapshot_download
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install huggingface_hub") from exc
    snapshot_download(repo_id=repo_id, revision=revision, local_dir=str(target),
                      local_dir_use_symlinks=False)
    return target
