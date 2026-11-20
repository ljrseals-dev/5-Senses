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
    """A small default rule set useful for classical AI / research questions."""
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

    return es
