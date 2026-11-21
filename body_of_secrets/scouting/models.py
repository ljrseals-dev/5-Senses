"""Discover and optionally acquire pretrained model artifacts.

Discovery is metadata-only. Downloads require a full immutable commit SHA and
are kept outside the source tree. Remote model code is never enabled.
"""
from __future__ import annotations

import json
import re
import shutil
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .integrity import build_manifest, write_manifest

_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$", re.IGNORECASE)


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
    def from_api(cls, item: dict[str, Any]) -> ModelCandidate:
        repo_id = item.get("id")
        if not isinstance(repo_id, str) or not repo_id.strip():
            raise ValueError("model catalog item is missing a valid id")
        tags = item.get("tags") or ()
        if not isinstance(tags, (list, tuple)) or any(not isinstance(tag, str) for tag in tags):
            raise ValueError("model catalog tags must be a list of strings")
        return cls(repo_id=repo_id, downloads=item.get("downloads"), likes=item.get("likes"),
                   pipeline_tag=item.get("pipeline_tag"), library_name=item.get("library_name"),
                   last_modified=item.get("lastModified"), tags=tuple(tags))


def search_models(query: str, *, limit: int = 20, timeout: float = 20.0) -> list[ModelCandidate]:
    """Search the public Hugging Face model catalog; no weights are downloaded."""
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must not be empty")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or timeout <= 0:
        raise ValueError("timeout must be positive")
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
    """Write a deterministic JSON inventory without overwriting or following symlinks."""
    path = Path(destination)
    if path.is_symlink():
        raise ValueError(f"inventory destination must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "asset_kind": "pretrained_model_candidate",
               "warning": "Catalog metadata is not proof of license compatibility or local availability.",
               "models": [asdict(item) for item in candidates]}
    created = False
    try:
        with path.open("x", encoding="utf-8", newline="") as stream:
            created = True
            json.dump(payload, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
    except Exception:
        if created:
            try:
                path.unlink()
            except OSError:
                pass
        raise
    return path


def acquire_model(repo_id: str, destination: str | Path, *, revision: str) -> Path:
    """Download and checksum a model snapshot pinned to a full 40-character commit SHA.

    The caller must independently review the model card and license before invoking
    this function. The snapshot is never loaded or executed by this module.
    """
    if not isinstance(repo_id, str) or not repo_id.strip():
        raise ValueError("repo_id must not be empty")
    if not isinstance(revision, str) or not _COMMIT_SHA_RE.fullmatch(revision):
        raise ValueError("revision must be a full 40-character immutable commit SHA")
    target = Path(destination)
    if target.is_symlink():
        raise ValueError(f"refusing symlink destination: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive mkdir prevents accidental reuse of an existing directory.
    target.mkdir(exist_ok=False)
    try:
        try:
            from huggingface_hub import snapshot_download
        except ImportError as exc:
            raise RuntimeError("Install optional dependency: pip install huggingface_hub") from exc

        snapshot_download(repo_id=repo_id, revision=revision, local_dir=str(target),
                          repo_type="model", local_files_only=False)
        files = sorted(path for path in target.rglob("*") if path.is_file())
        if any(path.is_symlink() for path in files):
            raise ValueError("downloaded model snapshot contains symlinks; refusing manifest")
        manifest = build_manifest(files, target)
        manifest.update({"asset_kind": "pretrained_model_snapshot",
                         "repo_id": repo_id, "revision": revision})
        write_manifest(manifest, target / "model_manifest.json")
    except Exception:
        # The destination directory was created exclusively by this call.
        shutil.rmtree(target, ignore_errors=True)
        raise
    return target
