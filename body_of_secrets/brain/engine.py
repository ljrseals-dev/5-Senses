"""Brain Engine — core language + reasoning loop.

CLASSICAL, ARCHIVE, and AUTO operate without external LLM providers.
ARCHIVE is document-only: it never uses expert rules or an LLM.
RESEARCH, AUDIT, and HYBRID may use an explicitly permitted provider.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from body_of_secrets import __version__, __disclaimer__
from body_of_secrets.archive import Archive
from body_of_secrets.expert import ExpertSystem, build_default_expert
from body_of_secrets.adapters.mcp_archive import MCPArchiveClient
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
        mcp_archive: MCPArchiveClient | None = None,
    ):
        self.archive = archive
        self.expert = expert or build_default_expert()
        self._provider = provider
        self.require_llm = require_llm
        self.mcp_archive = (
            mcp_archive if mcp_archive is not None
            else MCPArchiveClient.from_environment()
        )

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

    def _retrieve(self, question: str) -> tuple[str, list[str]]:
        sections: list[str] = []
        sources: list[str] = []
        if self.mcp_archive is not None:
            try:
                remote_hits = self.mcp_archive.search(question, limit=3)
            except Exception:
                # A missing, stopped, or unhealthy MCP service must never
                # prevent the local Archive from answering.
                remote_hits = []
            for hit in remote_hits:
                title = hit["title"]
                source = hit.get("source") or hit.get("path")
                content = hit.get("content") or hit.get("snippet")
                if not source or not content:
                    continue
                sources.append(source)
                sections.append(
                    f"[External corpus] Source: {source} | Title: {title}\n{content}"
                )

        if self.archive is not None:
            local = self.archive.context_for_query(question, limit=3)
            if local:
                sections.append("[Local BODY OF SECRETS Archive]\n" + local)
                for line in local.splitlines():
                    if line.startswith("[") and "Source:" in line:
                        source = line.split("Source:")[-1].split("|")[0].strip()
                        if source and source not in sources:
                            sources.append(source)
        return "\n\n".join(sections), sources

    def ask(
        self,
        question: str,
        *,
        mode: str = "CLASSICAL",
        subject: str | None = None,
        context: str | None = None,
        use_archive: bool = True,
    ) -> Answer:
        mode_spec = get_mode("CLASSICAL") if mode.upper() == "AUTO" else get_mode(mode)
        retrieved, sources = self._retrieve(question) if use_archive else ("", [])
        if context is None and retrieved:
            context = retrieved

        if mode_spec.name.value == "ARCHIVE":
            if not retrieved:
                return Answer(
                    question=question, mode=mode_spec.name.value,
                    answer="No relevant, provenance-bearing documents were retrieved from the local Archive or configured MCP corpus.",
                    subject=subject, truth_status="UNKNOWN", sources=[], classical=True,
                )
            return Answer(
                question=question, mode=mode_spec.name.value,
                answer="Retrieved Archive documents:\n\n" + retrieved,
                subject=subject, truth_status="UNKNOWN", sources=sources, classical=True,
            )

        if mode_spec.name.value == "CLASSICAL":
            rule_hit = self.expert.first_match(question)
            if rule_hit and rule_hit.matched and rule_hit.output:
                answer_text = rule_hit.output
                if context:
                    answer_text += "\n\n(Additional retrieved context was available from the configured document archives.)"
                evidence = extract_evidence(answer_text)
                truth = reconcile(answer_text) if "TRUTH_STATUS:" in answer_text else (
                    evidence[0].tag if evidence else "CONSENSUS"
                )
                return Answer(
                    question=question, mode=mode_spec.name.value, answer=answer_text,
                    subject=subject, evidence=evidence, truth_status=truth,
                    sources=sources, classical=True,
                )

        provider = self.provider if mode_spec.allows_provider else None
        if provider is None:
            if context:
                answer_text = (
                    "No matching expert rule and no LLM provider configured.\n\n"
                    "Retrieved Archive context:\n" + context
                )
                return Answer(
                    question=question, mode=mode_spec.name.value, answer=answer_text,
                    subject=subject, evidence=[], truth_status="UNKNOWN",
                    sources=sources, classical=True,
                )
            return Answer(
                question=question, mode=mode_spec.name.value,
                answer=(
                    "No expert rule matched and no LLM provider is available in this mode. "
                    "Import documents into the local Archive, configure the optional offline "
                    "document MCP service, or select RESEARCH, AUDIT, or HYBRID to enable "
                    "an explicitly permitted provider."
                ),
                subject=subject, evidence=[], truth_status="UNKNOWN",
                sources=sources, classical=True,
            )

        system = build_system(mode_spec)
        user = build_user_message(question, context=context, subject=subject)
        raw = provider.complete(system, user)
        truth = reconcile(raw)
        clean = strip_status_line(raw)
        evidence = extract_evidence(raw)
        return Answer(
            question=question, mode=mode_spec.name.value, answer=clean,
            subject=subject, evidence=evidence, truth_status=truth,
            sources=sources, classical=False,
        )
