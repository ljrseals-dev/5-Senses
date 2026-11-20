"""Brain Engine — core language + reasoning loop.

Supports two operating regimes:
1. Classical / offline  – uses Expert rules + Archive retrieval (no external LLM)
2. Hybrid / LLM-backed – uses an LLMProvider when one is configured
"""

from __future__ import annotations

from dataclasses import dataclass, field

from body_of_secrets import __version__, __disclaimer__
from body_of_secrets.archive import Archive
from body_of_secrets.expert import ExpertSystem, build_default_expert
from .evidence import Evidence, extract_evidence
from .modes import ModeSpec, get_mode
from .prompts import build_system, build_user_message
from .providers import LLMProvider, default_provider
from .truth_status import reconcile, strip_status_line


@dataclass
class Answer:
    question: str
    mode: str
    answer: str
    subject: str | None
    evidence: list[Evidence] = field(default_factory=list)
    truth_status: str = "UNKNOWN"
    sources: list[str] = field(default_factory=list)
    disclaimer: str = __disclaimer__
    version: str = __version__
    classical: bool = False  # True when answered without an external LLM


class Engine:
    """Main entry point for the Brain subsystem."""

    def __init__(
        self,
        provider: LLMProvider | None = None,
        archive: Archive | None = None,
        expert: ExpertSystem | None = None,
        *,
        require_llm: bool = False,
    ):
        self.archive = archive
        self.expert = expert or build_default_expert()
        self._provider = provider
        self.require_llm = require_llm

    @property
    def provider(self) -> LLMProvider | None:
        if self._provider is not None:
            return self._provider
        if self.require_llm:
            return default_provider()
        try:
            return default_provider()
        except RuntimeError:
            return None

    def ask(
        self,
        question: str,
        *,
        mode: str = "CLASSICAL",
        subject: str | None = None,
        context: str | None = None,
        use_archive: bool = True,
    ) -> Answer:
        if mode.upper() == "AUTO":
            mode_spec = get_mode("CLASSICAL")
        else:
            mode_spec = get_mode(mode)

        # 1. Gather classical context from Archive
        retrieved = ""
        sources: list[str] = []
        if use_archive and self.archive is not None and context is None:
            retrieved = self.archive.context_for_query(question, limit=3)
            if retrieved:
                context = retrieved
                for line in retrieved.splitlines():
                    if line.startswith("[") and "Source:" in line:
                        sources.append(line.split("Source:")[-1].split("|")[0].strip())

        # 2. Try classical Expert rules first (fast, offline, deterministic)
        if mode_spec.name.value in ("CLASSICAL", "ARCHIVE", "AUTO"):
            rule_hit = self.expert.first_match(question)
            if rule_hit and rule_hit.matched and rule_hit.output:
                answer_text = rule_hit.output
                if context:
                    answer_text += "\n\n(Additional retrieved context was available from the Archive.)"
                evidence = extract_evidence(answer_text)
                truth = reconcile(answer_text) if "TRUTH_STATUS:" in answer_text else (
                    evidence[0].tag if evidence else "CONSENSUS"
                )
                return Answer(
                    question=question,
                    mode=mode_spec.name.value,
                    answer=answer_text,
                    subject=subject,
                    evidence=evidence,
                    truth_status=truth,
                    sources=sources,
                    classical=True,
                )

        # 3. Fall back to LLM provider if available
        provider = self.provider
        if provider is None:
            if context:
                answer_text = (
                    "No matching expert rule and no LLM provider configured.\n\n"
                    "Retrieved Archive context:\n" + context
                )
                return Answer(
                    question=question,
                    mode=mode_spec.name.value,
                    answer=answer_text,
                    subject=subject,
                    evidence=[],
                    truth_status="UNKNOWN",
                    sources=sources,
                    classical=True,
                )
            return Answer(
                question=question,
                mode=mode_spec.name.value,
                answer=(
                    "No expert rule matched and no LLM provider is configured. "
                    "Import documents into the Archive or set OPENAI_API_KEY / "
                    "ANTHROPIC_API_KEY to enable hybrid answers."
                ),
                subject=subject,
                evidence=[],
                truth_status="UNKNOWN",
                sources=sources,
                classical=True,
            )

        # 4. LLM path
        system = build_system(mode_spec)
        user = build_user_message(question, context=context, subject=subject)
        raw = provider.complete(system, user)

        truth = reconcile(raw)
        clean = strip_status_line(raw)
        evidence = extract_evidence(raw)

        return Answer(
            question=question,
            mode=mode_spec.name.value,
            answer=clean,
            subject=subject,
            evidence=evidence,
            truth_status=truth,
            sources=sources,
            classical=False,
        )
