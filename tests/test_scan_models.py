from __future__ import annotations

import pytest

from body_of_secrets.scan import ScanRecord


def make_record(**overrides):
    values = {
        "sha256": "a" * 64,
        "scanner": "clamav",
        "engine_version": "1.4.2",
        "sig_version": "27800",
        "sig_age_hours": 1.5,
        "verdict": "clean",
        "detail": None,
        "magic_type": "text/plain",
        "declared_extension": ".txt",
        "scanned_at": "2026-11-22T00:00:00+00:00",
    }
    values.update(overrides)
    return ScanRecord(**values)


def test_scan_record_is_immutable_and_preserves_provenance():
    record = make_record()
    assert record.scanner == "clamav"
    assert record.verdict == "clean"
    with pytest.raises((AttributeError, TypeError)):
        record.verdict = "malware"


@pytest.mark.parametrize(
    "overrides",
    [
        {"sha256": "not-a-hash"},
        {"scanner": ""},
        {"verdict": "unknown"},
        {"sig_age_hours": -1},
        {"sig_age_hours": float("inf")},
        {"magic_type": ""},
        {"scanned_at": "not-a-time"},
    ],
)
def test_scan_record_rejects_invalid_provenance(overrides):
    with pytest.raises(ValueError):
        make_record(**overrides)


def test_scan_record_allows_missing_signature_metadata_only_as_degraded_by_contract():
    record = make_record(
        engine_version=None,
        sig_version=None,
        sig_age_hours=None,
        verdict="degraded",
        detail="scanner metadata unavailable",
    )
    assert record.verdict == "degraded"
    assert record.sig_version is None
