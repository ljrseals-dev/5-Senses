"""Tests for evidence extraction and truth-status."""

from body_of_secrets.brain.evidence import extract_evidence, strongest_supported_tag
from body_of_secrets.brain.truth_status import reconcile, strip_status_line


def test_extract_evidence():
    text = "This is [OFFICIAL] and also [PLAUSIBLE] and again [OFFICIAL]."
    evidence = extract_evidence(text)
    tags = {e.tag: e.count for e in evidence}
    assert tags["OFFICIAL"] == 2
    assert tags["PLAUSIBLE"] == 1


def test_strongest_supported_tag_conservative():
    evidence = extract_evidence("[OFFICIAL] [SPECULATIVE]")
    # Most conservative present tag
    assert strongest_supported_tag(evidence) == "SPECULATIVE"


def test_reconcile_prefers_declared():
    text = "Some answer.\n\nTRUTH_STATUS: CONSENSUS\n"
    assert reconcile(text) == "CONSENSUS"


def test_strip_status_line():
    text = "Answer text.\nTRUTH_STATUS: OFFICIAL\n"
    assert "TRUTH_STATUS" not in strip_status_line(text)
