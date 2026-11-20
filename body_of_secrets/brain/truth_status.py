"""Truth-status computation and normalization (Heart subsystem support)."""

from __future__ import annotations

import re

from .evidence import VALID_TAGS, extract_evidence, strongest_supported_tag

TRUTH_LINE_RE = re.compile(
    r"^\s*TRUTH_STATUS:\s*(?P<status>[A-Z_]+)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def parse_declared_status(text: str) -> str | None:
    match = TRUTH_LINE_RE.search(text)
    if not match:
        return None
    status = match.group("status").upper()
    return status if status in VALID_TAGS else None


def reconcile(text: str) -> str:
    """Prefer the model's declared status; fall back to conservative tag census."""
    declared = parse_declared_status(text)
    if declared:
        return declared
    return strongest_supported_tag(extract_evidence(text))


def strip_status_line(text: str) -> str:
    return TRUTH_LINE_RE.sub("", text).rstrip()
