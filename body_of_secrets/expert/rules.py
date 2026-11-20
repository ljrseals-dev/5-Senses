"""Lightweight rule-based expert system (classical component)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Rule:
    name: str
    pattern: re.Pattern[str]
    action: Callable[[re.Match[str], str], str]
    priority: int = 0
    description: str = ""


@dataclass
class RuleResult:
    rule_name: str
    matched: bool
    output: str | None = None
    description: str = ""


class ExpertSystem:
    """Simple forward-chaining rule engine over text input."""

    def __init__(self) -> None:
        self.rules: list[Rule] = []

    def add_rule(
        self,
        name: str,
        pattern: str,
        action: Callable[[re.Match[str], str], str],
        *,
        priority: int = 0,
        description: str = "",
        flags: int = re.IGNORECASE,
    ) -> None:
        self.rules.append(
            Rule(
                name=name,
                pattern=re.compile(pattern, flags),
                action=action,
                priority=priority,
                description=description,
            )
        )
        # Keep highest priority first
        self.rules.sort(key=lambda r: -r.priority)

    def evaluate(self, text: str) -> list[RuleResult]:
        results: list[RuleResult] = []
        for rule in self.rules:
            m = rule.pattern.search(text)
            if m:
                try:
                    out = rule.action(m, text)
                except Exception as exc:
                    out = f"[rule error: {exc}]"
                results.append(
                    RuleResult(
                        rule_name=rule.name,
                        matched=True,
                        output=out,
                        description=rule.description,
                    )
                )
            else:
                results.append(
                    RuleResult(
                        rule_name=rule.name,
                        matched=False,
                        description=rule.description,
                    )
                )
        return results

    def first_match(self, text: str) -> RuleResult | None:
        for rule in self.rules:
            m = rule.pattern.search(text)
            if m:
                try:
                    out = rule.action(m, text)
                except Exception as exc:
                    out = f"[rule error: {exc}]"
                return RuleResult(
                    rule_name=rule.name,
                    matched=True,
                    output=out,
                    description=rule.description,
                )
        return None


def build_default_expert() -> ExpertSystem:
    """Default rule set: classical AI facts + verified disease-origin consensus."""
    es = ExpertSystem()

    def hopfield_info(m: re.Match[str], text: str) -> str:
        return (
            "Hopfield networks (1982) are recurrent associative-memory models. "
            "They store patterns as energy minima and retrieve them by energy minimization. "
            "Capacity is roughly 0.15N patterns for N neurons. [CONSENSUS]"
        )

    def kohonen_info(m: re.Match[str], text: str) -> str:
        return (
            "Kohonen Self-Organizing Maps (SOMs) perform unsupervised topology-preserving "
            "dimensionality reduction. They were a major classical alternative to supervised "
            "multilayer perceptrons in the 1980s. [CONSENSUS]"
        )

    def pdp_info(m: re.Match[str], text: str) -> str:
        return (
            "Parallel Distributed Processing (Rumelhart & McClelland, 1986) is the foundational "
            "two-volume work that re-introduced connectionism and distributed representations "
            "to a wide audience. [OFFICIAL]"
        )

    def ngram_info(m: re.Match[str], text: str) -> str:
        return (
            "n-gram models estimate the probability of a token given the previous n-1 tokens. "
            "They were the dominant statistical language modelling approach before neural LMs. "
            "[CONSENSUS]"
        )

    def provenance_info(m: re.Match[str], text: str) -> str:
        return (
            "In BODY OF SECRETS every factual claim should carry an epistemic tag: "
            "[OFFICIAL], [CONSENSUS], [PLAUSIBLE], [SPECULATIVE], or [UNKNOWN]. "
            "This is a classical certainty-factor discipline. [OFFICIAL]"
        )

    def west_nile_info(m: re.Match[str], text: str) -> str:
        return (
            "West Nile virus was first isolated in 1937 in the West Nile district of Uganda "
            "from a febrile patient during yellow-fever surveillance. It is a bird–mosquito "
            "(Culex) flavivirus. No documented human outbreaks exist from the early 1900s; "
            "the virus was unknown to science before 1937. It reached North America in 1999. "
            "[CONSENSUS]"
        )

    def hiv_info(m: re.Match[str], text: str) -> str:
        return (
            "HIV-1 (pandemic group M) originated from SIVcpz in central chimpanzees via "
            "bushmeat exposure, most likely 1890–1920 in west-central Africa, with early "
            "spread centered on Kinshasa. HIV-2 came from sooty mangabeys. There is no "
            "credible evidence it was engineered or deliberately released. [CONSENSUS]"
        )

    def covid_info(m: re.Match[str], text: str) -> str:
        return (
            "SARS-CoV-2 is most closely related to horseshoe-bat sarbecoviruses. The leading "
            "scientific hypothesis is natural zoonotic spillover in late 2019, associated with "
            "the Huanan market in Wuhan. Laboratory-incident hypotheses remain discussed but "
            "are not the majority view in the peer-reviewed virological literature. [CONSENSUS]"
        )

    es.add_rule("hopfield", r"\bhopfield\b", hopfield_info, priority=10,
                description="Hopfield network facts")
    es.add_rule("kohonen", r"\b(kohonen|self[- ]organising map|self[- ]organizing map|SOM)\b",
                kohonen_info, priority=10, description="Kohonen SOM facts")
    es.add_rule("pdp", r"\b(parallel distributed processing|PDP|rumelhart|mcclelland)\b",
                pdp_info, priority=10, description="PDP volumes facts")
    es.add_rule("ngram", r"\b(n[- ]gram|ngram)\b", ngram_info, priority=5,
                description="n-gram language model facts")
    es.add_rule("provenance", r"\b(provenance|truth[- ]status|epistemic|certainty factor)\b",
                provenance_info, priority=5, description="Provenance discipline")

    # Disease-origin consensus rules (higher priority for specific queries)
    es.add_rule("west_nile", r"\b(west nile|west-nile|WNV)\b", west_nile_info, priority=12,
                description="West Nile virus origin facts")
    es.add_rule("hiv_aids", r"\b(HIV|AIDS|acquired immunodeficiency)\b", hiv_info, priority=12,
                description="HIV/AIDS origin consensus")
    es.add_rule("covid", r"\b(COVID|COVID-19|SARS-CoV-2|SARSCoV2|coronavirus pandemic)\b",
                covid_info, priority=12, description="SARS-CoV-2 origin consensus")

    return es
