"""Evidence tag extraction and validation (Blood subsystem support)."""

from __future__ import annotations

import re
from dataclasses import dataclass

VALID_TAGS = ("OFFICIAL", "CONSENSUS", "PLAUSIBLE", "SPECULATIVE", "UNKNOWN")
TAG_RE = re.compile(r"\[(" + "|".join(VALID_TAGS) + r")\]")


@dataclass(frozen=True)
class Evidence:
    tag: str
    count: int


def extract_evidence(text: str) -> list[Evidence]:
    counts: dict[str, int] = {}
    for match in TAG_RE.finditer(text):
        counts[match.group(1)] = counts.get(match.group(1), 0) + 1
    return [Evidence(tag=t, count=counts[t]) for t in VALID_TAGS if t in counts]


def strongest_supported_tag(evidence: list[Evidence]) -> str:
    """Return the most conservative (weakest) tag present."""
    if not evidence:
        return "UNKNOWN"
    present = {e.tag for e in evidence}
    for tag in reversed(VALID_TAGS):
        if tag in present:
            return tag
    return "UNKNOWN"
