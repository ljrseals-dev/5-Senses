"""Brain Engine — core language + reasoning loop.

CLASSICAL, ARCHIVE, and AUTO operate without external LLM providers.
ARCHIVE is document-only: it never uses expert rules or an LLM.
RESEARCH, AUDIT, and HYBRID may use an explicitly permitted provider.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock

from body_of_secrets import __disclaimer__, __version__
from body_of_secrets.archive import Archive
from body_of_secrets.expert import ExpertSystem, build_default_expert
from .evidence import Evidence, extract_evidence
from .modes import get_mode
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
    classical: bool = False


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
        self._provider_resolved = provider is not None
        self._provider_lock = Lock()
        self.require_llm = require_llm

    @property
    def provider(self) -> LLMProvider | None:
        """Resolve an optional provider once, without breaking offline operation.

        Missing credentials or an uninstalled optional SDK are equivalent to no
        provider when ``require_llm`` is false. When it is true, the original
        configuration/import error is surfaced to the caller.
        """
        with self._provider_lock:
            if self._provider_resolved:
                return self._provider

            try:
                provider = default_provider()
            except (RuntimeError, ImportError):
                if self.require_llm:
                    raise
                self._provider_resolved = True
                return None

            self._provider = provider
            self._provider_resolved = True
            return self._provider

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

        retrieved = ""
        sources: list[str] = []
        if use_archive and self.archive is not None and context is None:
            retrieved = self.archive.context_for_query(question, limit=3)
            if retrieved:
                context = retrieved
                for line in retrieved.splitlines():
                    if line.startswith("[") and "Source:" in line:
                        sources.append(line.split("Source:")[-1].split("|")[0].strip())

        # ARCHIVE is strict document-only. Caller-supplied context is not
        # treated as verified archive material because it has no source record.
        if mode_spec.name.value == "ARCHIVE":
            if not retrieved:
                return Answer(
                    question=question,
                    mode=mode_spec.name.value,
                    answer="No relevant, provenance-bearing documents were retrieved from the Archive.",
                    subject=subject,
                    truth_status="UNKNOWN",
                    sources=[],
                    classical=True,
                )
            return Answer(
                question=question,
                mode=mode_spec.name.value,
                answer="Retrieved Archive documents:\n\n" + retrieved,
                subject=subject,
                truth_status="UNKNOWN",
                sources=sources,
                classical=True,
            )

        # Expert rules are available in CLASSICAL, never in ARCHIVE.
        if mode_spec.name.value == "CLASSICAL":
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

        # Do not resolve the provider property unless this mode permits it.
        provider = self.provider if mode_spec.allows_provider else None
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
                    "No expert rule matched and no LLM provider is available in this mode. "
                    "Import documents into the Archive or select RESEARCH, AUDIT, or HYBRID "
                    "to enable an explicitly permitted provider."
                ),
                subject=subject,
                evidence=[],
                truth_status="UNKNOWN",
                sources=sources,
                classical=True,
            )

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
