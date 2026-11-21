"""Metadata-only ingestion for external C++ reference corpora.

Source code is never copied by this module. Records remain on rights hold until
an explicit license review and pinned source revision are recorded.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from body_of_secrets.archive import Archive

ALLOWED_RIGHTS = {"UNVERIFIED_HOLD", "LICENSE_VERIFIED", "RESTRICTED"}


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate a versioned metadata-only corpus manifest."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1:
        raise ValueError("unsupported C++ corpus manifest schema_version")
    if payload.get("contains_source_code") is not False:
        raise ValueError("this ingestion path accepts metadata-only manifests")
    sources = payload.get("sources")
    records = payload.get("records")
    if not isinstance(sources, list) or not isinstance(records, list):
        raise ValueError("manifest requires sources and records arrays")
    source_ids = {item.get("id") for item in sources if isinstance(item, dict)}
    if len(source_ids) != len(sources):
        raise ValueError("every source must be an object with a unique id")
    seen: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each record must be an object")
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id or record_id in seen:
            raise ValueError("record IDs must be non-empty and unique")
        seen.add(record_id)
        if record.get("source_id") not in source_ids:
            raise ValueError(f"record {record_id} references an unknown source")
        if record.get("rights_status") not in ALLOWED_RIGHTS:
            raise ValueError(f"record {record_id} has an invalid rights_status")
        if record.get("source_path") is not None and not isinstance(record["source_path"], str):
            raise ValueError(f"record {record_id} source_path must be a string or null")
        if record.get("source_revision") is not None and not isinstance(record["source_revision"], str):
            raise ValueError(f"record {record_id} source_revision must be a string or null")
        if record.get("source_code") not in (None, ""):
            raise ValueError("source_code is forbidden in metadata-only corpus manifests")
    return payload


def import_manifest(archive: Archive, path: str | Path) -> list[str]:
    """Import corpus and example metadata into Archive; never fetch or copy source."""
    manifest = load_manifest(path)
    sources = {item["id"]: item for item in manifest["sources"]}
    imported: list[str] = []
    for record in manifest["records"]:
        source = sources[record["source_id"]]
        metadata = {
            "kind": "cpp_reference_example",
            "record_id": record["id"],
            "source_repo": source["repository"],
            "source_url": source["url"],
            "source_license_status": source.get("license_status", "UNVERIFIED_HOLD"),
            "source_revision_status": source.get("revision_status", "UNPINNED"),
            "source_path": record.get("source_path"),
            "source_revision": record.get("source_revision") or source.get("revision"),
            "language_standard": record.get("language_standard", []),
            "concepts": record.get("concepts", []),
            "item_number": record.get("item_number"),
            "rights_status": record["rights_status"],
            "source_code_included": False,
            "source_hash": None,
            "verification": "NOT_RUN",
        }
        content = json.dumps(
            {"metadata": metadata, "summary": record.get("summary", ""),
             "hypothesis": record.get("hypothesis", ""),
             "distinguishing_test": record.get("distinguishing_test", "")},
            indent=2, sort_keys=True,
        )
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        metadata["metadata_record_sha256"] = digest
        doc_id = "cppref_" + record["id"].replace("-", "_")
        archive.import_document(
            title=record["id"],
            content=content,
            source=source["url"],
            tags=["cpp-reference", "metadata-only", record["rights_status"].lower(),
                  *record.get("concepts", [])],
            metadata=metadata,
            doc_id=doc_id,
        )
        imported.append(doc_id)
    return imported
