"""Operating modes for the Brain (expert personas / system postures)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Mode(str, Enum):
    AUTO = "AUTO"
    CLASSICAL = "CLASSICAL"      # Strict classical AI posture
    RESEARCH = "RESEARCH"        # Graduate-level research reasoning
    ARCHIVE = "ARCHIVE"          # Document-grounded answers only
    AUDIT = "AUDIT"              # Critical review / claim strength
    HYBRID = "HYBRID"            # Classical + modern model bridge


@dataclass(frozen=True)
class ModeSpec:
    name: Mode
    blurb: str
    system_addendum: str


MODES: dict[Mode, ModeSpec] = {
    Mode.CLASSICAL: ModeSpec(
        name=Mode.CLASSICAL,
        blurb="Strict classical AI posture — rules, associative memory, statistical models.",
        system_addendum=(
            "You are operating in CLASSICAL mode. Prefer deterministic rules, "
            "associative recall, n-gram statistics, and explicit provenance. "
            "Do not invent facts. Tag every claim with its epistemic status. "
            "When uncertain, say so clearly using the truth-status vocabulary."
        ),
    ),
    Mode.RESEARCH: ModeSpec(
        name=Mode.RESEARCH,
        blurb="Graduate-level research reasoning, methodology, and epistemology.",
        system_addendum=(
            "You are answering in RESEARCH mode. Assume the reader is a "
            "researcher. Engage methodology and epistemology directly. "
            "Distinguish documented fact, hypothesis, and open question. "
            "Cite fields or primary sources where possible."
        ),
    ),
    Mode.ARCHIVE: ModeSpec(
        name=Mode.ARCHIVE,
        blurb="Document-grounded answers only — no speculation beyond retrieved evidence.",
        system_addendum=(
            "You are operating in ARCHIVE mode. Answer only from the provided "
            "documents and their provenance. If the documents do not contain "
            "the answer, say so. Never invent content that is not present in "
            "the retrieved material."
        ),
    ),
    Mode.AUDIT: ModeSpec(
        name=Mode.AUDIT,
        blurb="Critical review: claim strength, assumptions, and consistency.",
        system_addendum=(
            "You are answering in AUDIT mode. Your job is critical review. "
            "Identify weaknesses, unstated assumptions, and overclaims. "
            "Be direct but constructive. Prefer conservative truth-status tags."
        ),
    ),
    Mode.HYBRID: ModeSpec(
        name=Mode.HYBRID,
        blurb="Bridge classical components with optional modern language models.",
        system_addendum=(
            "You are answering in HYBRID mode. Explicitly separate what comes "
            "from classical components (rules, associative memory, statistics) "
            "from any modern model contribution. Maintain full provenance."
        ),
    ),
}


def get_mode(raw: str) -> ModeSpec:
    try:
        return MODES[Mode(raw.upper())]
    except KeyError as exc:
        valid = [m.value for m in Mode if m != Mode.AUTO]
        raise ValueError(f"Unknown mode {raw!r}. Valid: {valid}") from exc
