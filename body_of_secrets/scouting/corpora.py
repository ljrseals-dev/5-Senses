"""Metadata discovery for text corpora and historical digital collections."""
from __future__ import annotations

import json
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


def _get_json(url: str, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "5-Senses-Boy-Scout/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def search_huggingface_datasets(query: str, *, limit: int = 20,
                                timeout: float = 20.0) -> list[CorpusCandidate]:
    """Search dataset metadata only; no dataset files are downloaded."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    params = urllib.parse.urlencode({"search": query, "limit": limit})
    payload = _get_json(f"https://huggingface.co/api/datasets?{params}", timeout)
    if not isinstance(payload, list):
        raise ValueError("unexpected dataset catalog response")
    return [CorpusCandidate("huggingface", str(x["id"]),
                            description=", ".join(x.get("tags") or []),
                            url=f"https://huggingface.co/datasets/{x['id']}")
            for x in payload if isinstance(x, dict) and x.get("id")]


def search_internet_archive(query: str, *, limit: int = 20,
                             timeout: float = 20.0) -> list[CorpusCandidate]:
    """Search Internet Archive text metadata; this does not fetch item payloads."""
    if not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 100:
        raise ValueError("limit must be between 1 and 100")
    params = urllib.parse.urlencode({
        "q": f"({query}) AND mediatype:(texts)",
        "fl[]": ["identifier", "title", "description", "licenseurl", "mediatype"],
        "rows": limit, "page": 1, "output": "json",
    }, doseq=True)
    payload = _get_json(f"https://archive.org/advancedsearch.php?{params}", timeout)
    docs = payload.get("response", {}).get("docs", [])
    return [CorpusCandidate("internet_archive", str(x["identifier"]),
                            str(x.get("title") or ""), str(x.get("description") or ""),
                            x.get("licenseurl"),
                            f"https://archive.org/details/{x['identifier']}",
                            x.get("mediatype"))
            for x in docs if isinstance(x, dict) and x.get("identifier")]


def write_corpus_inventory(candidates: list[CorpusCandidate], destination: str | Path) -> Path:
    """Write a JSON inventory without replacing an existing inventory."""
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(path)
    payload = {"schema_version": 1, "asset_kind": "corpus_candidate",
               "warning": "Metadata is not proof of rights, completeness, or local acquisition.",
               "corpora": [asdict(item) for item in candidates]}
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
