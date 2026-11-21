"""Metadata discovery for text corpora and historical digital collections."""
from __future__ import annotations

import json
import math
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class CorpusCandidate:
    source: str
    identifier: str
    title: str = ""
    description: str = ""
    license: str | None = None
    url: str = ""
    media_type: str | None = None


def _validate_search(query: str, limit: int, timeout: float) -> None:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must not be empty")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("limit must be an integer between 1 and 100")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")


def _get_json(url: str, timeout: float) -> Any:
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be a positive finite number")
    request = urllib.request.Request(url, headers={"User-Agent": "5-Senses-Boy-Scout/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload


def search_huggingface_datasets(query: str, *, limit: int = 20,
                                timeout: float = 20.0) -> list[CorpusCandidate]:
    """Search dataset metadata only; no dataset files are downloaded."""
    _validate_search(query, limit, timeout)
    params = urllib.parse.urlencode({"search": query, "limit": limit})
    payload = _get_json(f"https://huggingface.co/api/datasets?{params}", timeout)
    if not isinstance(payload, list):
        raise ValueError("unexpected dataset catalog response")
    candidates = []
    for item in payload:
        if not isinstance(item, dict) or not isinstance(item.get("id"), str) or not item["id"].strip():
            continue
        tags = item.get("tags") or []
        if not isinstance(tags, list) or any(not isinstance(tag, str) for tag in tags):
            raise ValueError("dataset catalog tags must be a list of strings")
        candidates.append(CorpusCandidate(
            "huggingface", item["id"], description=", ".join(tags),
            url=f"https://huggingface.co/datasets/{urllib.parse.quote(item['id'], safe='/')}",
        ))
    return candidates


def search_internet_archive(query: str, *, limit: int = 20,
                             timeout: float = 20.0) -> list[CorpusCandidate]:
    """Search Internet Archive text metadata; this does not fetch item payloads."""
    _validate_search(query, limit, timeout)
    params = urllib.parse.urlencode({
        "q": f"({query}) AND mediatype:(texts)",
        "fl[]": ["identifier", "title", "description", "licenseurl", "mediatype"],
        "rows": limit, "page": 1, "output": "json",
    }, doseq=True)
    payload = _get_json(f"https://archive.org/advancedsearch.php?{params}", timeout)
    if not isinstance(payload, dict):
        raise ValueError("unexpected Internet Archive response")
    response = payload.get("response")
    if not isinstance(response, dict) or not isinstance(response.get("docs", []), list):
        raise ValueError("unexpected Internet Archive response documents")
    candidates = []
    for item in response.get("docs", []):
        if not isinstance(item, dict):
            continue
        identifier = item.get("identifier")
        if not isinstance(identifier, str) or not identifier.strip():
            continue
        title = item.get("title") or ""
        description = item.get("description") or ""
        license_url = item.get("licenseurl")
        media_type = item.get("mediatype")
        candidates.append(CorpusCandidate(
            "internet_archive", identifier, str(title), str(description),
            str(license_url) if license_url is not None else None,
            f"https://archive.org/details/{urllib.parse.quote(identifier, safe='')}",
            str(media_type) if media_type is not None else None,
        ))
    return candidates


def write_corpus_inventory(candidates: list[CorpusCandidate], destination: str | Path) -> Path:
    """Write a JSON inventory exclusively; never replace an existing file."""
    path = Path(destination)
    if path.is_symlink():
        raise ValueError(f"inventory destination must not be a symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema_version": 1, "asset_kind": "corpus_candidate",
               "warning": "Metadata is not proof of rights, completeness, or local acquisition.",
               "corpora": [asdict(item) for item in candidates]}
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
