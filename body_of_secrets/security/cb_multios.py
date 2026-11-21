"""Read and explicitly import the quarantined CB-MultiOS REMATCH corpus.

This module only supports provenance-preserving Archive ingestion. It does not
promote records into Expert rules or neural training data.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_CHALLENGES = {f"REMATCH_{number}" for number in range(1, 7)}
DATASET_NAME = "5-Senses CB-MultiOS REMATCH Defensive Learning Set"


def load_rematch_records(path: str | Path) -> list[dict[str, Any]]:
    """Load and validate the six-record JSONL corpus without executing content."""
    source = Path(path)
    records: list[dict[str, Any]] = []
    seen: set[str] = set()
    with source.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid JSON on line {line_number}: {exc}") from exc
            challenge_id = record.get("challenge_id")
            if challenge_id not in EXPECTED_CHALLENGES:
                raise ValueError(f"unexpected challenge_id on line {line_number}: {challenge_id!r}")
            if challenge_id in seen:
                raise ValueError(f"duplicate challenge_id: {challenge_id}")
            if record.get("dataset") != DATASET_NAME:
                raise ValueError(f"unexpected dataset on line {line_number}")
            if record.get("mapping_status") != "upstream_explicit":
                raise ValueError(f"unverified upstream mapping status: {challenge_id}")
            if record.get("training_status") != "quarantined_not_training_ready":
                raise ValueError(f"record is not quarantined: {challenge_id}")
            provenance = record.get("provenance") or {}
            if not provenance.get("repository", "").startswith("https://github.com/trailofbits/cb-multios"):
                raise ValueError(f"missing upstream provenance: {challenge_id}")
            if not provenance.get("path", "").endswith("/README.md"):
                raise ValueError(f"missing source README path: {challenge_id}")
            mappings = record.get("cwe_mappings")
            if not isinstance(mappings, list) or not mappings:
                raise ValueError(f"missing explicit CWE mapping: {challenge_id}")
            for mapping in mappings:
                if mapping.get("mapping_source") != "upstream_challenge_readme" or mapping.get("status") != "explicit":
                    raise ValueError(f"CWE mapping lacks author provenance: {challenge_id}")
                catalogue = mapping.get("mitre_catalogue") or {}
                if not catalogue.get("title") or not catalogue.get("url", "").startswith("https://cwe.mitre.org/"):
                    raise ValueError(f"missing separate MITRE catalogue metadata: {challenge_id}")
            seen.add(challenge_id)
            records.append(record)

    if seen != EXPECTED_CHALLENGES:
        missing = sorted(EXPECTED_CHALLENGES - seen)
        raise ValueError(f"REMATCH corpus incomplete; missing: {', '.join(missing)}")
    return records


def import_rematch_into_archive(archive: Any, path: str | Path) -> list[str]:
    """Explicitly import validated summaries into Archive with provenance metadata.

    Importing makes records searchable only. The quarantine marker is retained,
    and this function never calls ExpertSystem or neural-training APIs.
    """
    records = load_rematch_records(path)
    imported: list[str] = []
    for record in records:
        challenge_id = record["challenge_id"]
        mappings = record["cwe_mappings"]
        mapping_lines = [
            f"{item['id']} — upstream label: {item['name']}; "
            f"current MITRE title: {item['mitre_catalogue']['title']}"
            for item in mappings
        ]
        content = "\n".join(
            [
                record["description"],
                "Upstream CWE classifications:",
                *mapping_lines,
                f"Historical CVE context only: {', '.join(record.get('historical_cve_references', [])) or 'none listed'}",
                "No CVE is assigned to this synthetic CGC challenge.",
                "Training status: quarantined_not_training_ready.",
            ]
        )
        provenance = record["provenance"]
        source = f"{provenance['repository']}/blob/{provenance.get('ref', 'master')}/{provenance['path']}"
        tags = ["security", "cb-multios", "rematch", "synthetic-cgc"]
        tags.extend(item["id"].lower() for item in mappings)
        metadata = {
            "dataset": DATASET_NAME,
            "record_type": record["record_type"],
            "challenge_id": challenge_id,
            "mapping_status": record["mapping_status"],
            "cve_status": record["cve_status"],
            "historical_cve_references": record.get("historical_cve_references", []),
            "cwe_mappings": mappings,
            "provenance": provenance,
            "training_status": record["training_status"],
        }
        imported.append(
            archive.import_document(
                title=f"{challenge_id}: {record['challenge_title']}",
                content=content,
                source=source,
                tags=tags,
                metadata=metadata,
                doc_id=f"security:cb-multios:{challenge_id.lower()}",
            )
        )
    return imported
