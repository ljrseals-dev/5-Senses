"""System and user prompt construction for the Brain."""

from __future__ import annotations

from .modes import ModeSpec

BASE_SYSTEM = """You are the Brain of BODY OF SECRETS — a classical intelligence and language architecture.

Core rules:
- Prefer documented evidence over speculation.
- Tag every substantive claim with an epistemic status using the tags:
  [OFFICIAL]  [CONSENSUS]  [PLAUSIBLE]  [SPECULATIVE]  [UNKNOWN]
- End your response with a single line:
  TRUTH_STATUS: <one of the five tags above>
- Never invent primary sources, policy, or historical facts.
- When the answer is not known, say so clearly.
"""


def build_system(mode: ModeSpec) -> str:
    return BASE_SYSTEM + "\n\n" + mode.system_addendum


def build_user_message(
    question: str,
    *,
    context: str | None = None,
    subject: str | None = None,
) -> str:
    parts: list[str] = []
    if subject:
        parts.append(f"Subject focus: {subject}")
    if context:
        parts.append("Retrieved context / documents:\n" + context)
    parts.append("Question:\n" + question)
    return "\n\n".join(parts)
