"""Evidence-preserving, non-executing C++ source triage.

This first milestone deliberately does not invoke a shell, compiler, or sanitizer.
Static matches are observations; every resulting cause remains PLAUSIBLE until
a separately authorized test produces reproducible evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class Observation:
    rule: str
    line: int
    excerpt: str

@dataclass(frozen=True)
class Hypothesis:
    id: str
    category: str
    statement: str
    status: str = "PLAUSIBLE"
    confidence: None = None
    supporting_evidence: list[str] = field(default_factory=list)
    contradicting_evidence: list[str] = field(default_factory=list)
    discriminating_tests: list[str] = field(default_factory=list)

@dataclass
class CppDebugReport:
    record_id: str
    language: str
    standard: str
    source_path: str
    source_sha256: str
    created_at: str
    source_type: str
    input_text: str
    environment: dict[str, Any]
    observations: list[Observation]
    hypotheses: list[Hypothesis]
    verified_cause: None = None
    minimal_fix: None = None
    regression_results: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[dict[str, str]] = field(default_factory=list)

_RULES: tuple[tuple[str, str, str, str], ...] = (
    ("raw_delete", r"\bdelete\s*(?:\[\s*\])?\s*[A-Za-z_]\w*", "ownership",
     "Manual deletion is present; inspect ownership, aliasing, and lifetime paths."),
    ("raw_new", r"\bnew\s+(?:[A-Za-z_:]\w*|\()", "ownership",
     "Raw allocation is present; inspect exception safety and ownership transfer."),
    ("borrowed_return", r"\breturn\s+\w+\s*;", "lifetime",
     "A named object is returned; determine whether it is a value, reference, or view."),
    ("thread_creation", r"\b(std::thread|std::async|pthread_create)\b", "concurrency",
     "Concurrent execution is present; inspect synchronization and shared state."),
    ("shared_mutation", r"\b(std::atomic|std::mutex|std::lock_guard|std::unique_lock)\b", "concurrency",
     "Synchronization primitives are present; verify every conflicting access is covered."),
    ("reinterpret_cast", r"\breinterpret_cast\s*<", "memory_ub",
     "Low-level type reinterpretation is present; inspect alignment, object lifetime, and aliasing."),
    ("memcpy", r"\b(std::)?memcpy\s*\(", "memory_ub",
     "Byte-wise copying is present; verify object representation and destination bounds."),
    ("allocation_in_callback", r"\b(new|make_unique|make_shared|vector|std::string)\b", "realtime_safety",
     "Potential allocation site found; determine whether it executes on a real-time callback."),
)
_TESTS = {
    "ownership": ["Trace every owner and alias; add a focused lifetime test.", "Run AddressSanitizer on a minimal reproducer."],
    "lifetime": ["Check the declared return type and object lifetime at each call site.", "Run AddressSanitizer with a minimal reproducer."],
    "concurrency": ["Run ThreadSanitizer on a deterministic concurrent reproducer.", "Enumerate shared reads/writes and their synchronization."],
    "memory_ub": ["Run UndefinedBehaviorSanitizer and AddressSanitizer on a minimal reproducer.", "Check alignment, bounds, and object-lifetime preconditions."],
    "realtime_safety": ["Trace whether the matched site is reachable from the audio callback.", "Instrument callback allocations and lock acquisition in a test build."],
}

def analyze_cpp_source(source: str, *, source_path: str = "<memory>",
                       standard: str = "c++20", input_text: str = "") -> CppDebugReport:
    """Classify static source observations without executing or modifying it."""
    if standard not in {"c++17", "c++20"}:
        raise ValueError("standard must be c++17 or c++20")
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    record_id = "cpp-debug-" + digest[:12]
    observations: list[Observation] = []
    hypotheses: list[Hypothesis] = []
    lines = source.splitlines()
    for rule, pattern, category, statement in _RULES:
        regex = re.compile(pattern)
        matches = [(i, line.strip()) for i, line in enumerate(lines, 1) if regex.search(line)]
        if not matches:
            continue
        evidence_ids = []
        for line_no, excerpt in matches:
            observations.append(Observation(rule, line_no, excerpt[:240]))
            evidence_ids.append(f"{rule}:L{line_no}")
        hypotheses.append(Hypothesis(
            id=f"H{len(hypotheses) + 1}", category=category, statement=statement,
            supporting_evidence=evidence_ids,
            discriminating_tests=list(_TESTS[category]),
        ))
    return CppDebugReport(
        record_id=record_id, language="cpp", standard=standard,
        source_path=source_path, source_sha256=digest,
        created_at=datetime.now(timezone.utc).isoformat(),
        source_type="typed", input_text=input_text,
        environment={"compiler": None, "compiler_version": None, "flags": [],
                     "sanitizers": [], "execution_performed": False},
        observations=observations, hypotheses=hypotheses,
        provenance=[{"kind": "source_file", "path": source_path, "sha256": digest}],
    )

def analyze_cpp_file(path: str | Path, *, standard: str = "c++20",
                     input_text: str = "") -> CppDebugReport:
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(source_path)
    source = source_path.read_text(encoding="utf-8")
    return analyze_cpp_source(source, source_path=str(source_path),
                              standard=standard, input_text=input_text)

def report_dict(report: CppDebugReport) -> dict[str, Any]:
    return asdict(report)

def report_json(report: CppDebugReport) -> str:
    return json.dumps(report_dict(report), indent=2, sort_keys=True)
