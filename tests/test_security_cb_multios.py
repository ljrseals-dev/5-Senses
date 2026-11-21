"""Tests for the quarantined CB-MultiOS REMATCH Archive integration."""

import json
from pathlib import Path

import pytest

from body_of_secrets.archive import Archive
from body_of_secrets.security.cb_multios import (
    EXPECTED_CHALLENGES,
    import_rematch_into_archive,
    load_rematch_records,
)


CORPUS = Path(__file__).parents[1] / "data/security/cb-multios/rematch/rematch_cwe.jsonl"


def test_loads_all_six_records_with_explicit_provenance():
    records = load_rematch_records(CORPUS)
    assert {record["challenge_id"] for record in records} == EXPECTED_CHALLENGES
    assert sum(len(record["cwe_mappings"]) for record in records) == 8
    assert all(record["training_status"] == "quarantined_not_training_ready" for record in records)


def test_archive_import_preserves_provenance_and_quarantine(tmp_path):
    with Archive(tmp_path / "archive.db") as archive:
        ids = import_rematch_into_archive(archive, CORPUS)
        assert len(ids) == 6
        assert archive.count() == 6
        doc = archive.get("security:cb-multios:rematch_6")
        assert doc is not None
        assert doc.metadata["challenge_id"] == "REMATCH_6"
        assert doc.metadata["cve_status"] == "no_cve_assigned_to_synthetic_challenge"
        assert doc.metadata["training_status"] == "quarantined_not_training_ready"
        assert doc.metadata["provenance"]["repository"].endswith("trailofbits/cb-multios")
        assert "CWE-788" in doc.content
        assert "No CVE is assigned" in doc.content
        assert archive.search("Heartbleed heartbeat buffer", limit=6)


def test_rejects_duplicate_challenge_ids(tmp_path):
    lines = CORPUS.read_text(encoding="utf-8").splitlines()
    bad = tmp_path / "duplicate.jsonl"
    bad.write_text("\n".join([lines[0], lines[0], *lines[2:]]) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate challenge_id"):
        load_rematch_records(bad)


def test_rejects_records_that_escape_training_quarantine(tmp_path):
    records = [json.loads(line) for line in CORPUS.read_text(encoding="utf-8").splitlines()]
    records[0]["training_status"] = "training_ready"
    bad = tmp_path / "unquarantined.jsonl"
    bad.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="record is not quarantined"):
        load_rematch_records(bad)
