"""C++ semantics rules for the classical Expert system.

These rules emit hypotheses and discriminating tests, never verified diagnoses.
"""
from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from body_of_secrets.expert.rules import ExpertSystem


_RULES = [
    ("cpp_pure_virtual_destructor", r"pure\s+virtual\s+(destructor|~)|virtual\s+~\w+\s*\(\s*\)\s*=\s*0",
     "A pure virtual destructor still needs a definition when derived-object destruction odr-uses it.",
     "Build and link a minimal derived class; inspect any undefined destructor symbol.",
     30),
    ("cpp_unique_ptr", r"\bstd::unique_ptr\b",
     "unique_ptr expresses exclusive ownership; moving it transfers the managed pointer.",
     "Move-construct a second unique_ptr, inspect both get() values, and count destruction.",
     25),
    ("cpp_shared_concurrency", r"\bstd::shared_ptr\b.*\b(thread|mutex|atomic|race|concurr)|\b(shared_ptr|shared ownership)\b.*\b(thread|race|mutable|thread.safe)",
     "shared_ptr synchronizes ownership bookkeeping, not arbitrary mutable object state; unsynchronized access can still data race.",
     "Run a deterministic concurrent read/write reproducer under ThreadSanitizer; compare synchronized and unsynchronized versions.",
     29),
    ("cpp_shared_ptr", r"\bstd::shared_ptr\b",
     "shared_ptr provides shared lifetime ownership through a control block; it does not make the pointee thread-safe.",
     "Copy and reset owners while observing use_count and destructor timing.",
     24),
    ("cpp_weak_ptr", r"\bstd::weak_ptr\b",
     "weak_ptr is a non-owning observer and does not extend the managed object's lifetime.",
     "Reset the final shared owner, then assert expired() and test lock().",
     24),
    ("cpp_move", r"\bstd::move\b(?:\s*\()?",
     "std::move is a cast enabling move-aware overload resolution; it does not itself move a resource.",
     "Use instrumented copy/move constructors and test both lvalue and xvalue inputs.",
     23),
    ("cpp_forward", r"\bstd::forward\b(?:\s*<)?",
     "std::forward<T> conditionally preserves the caller's value category; reference collapsing determines the result.",
     "Pass an lvalue and an rvalue through the same forwarding-reference template and assert overload selection.",
     23),
    ("cpp_type_deduction", r"\b(auto|decltype)\b",
     "auto and decltype use distinct deduction rules, especially for references and expression value categories.",
     "Use static_assert(std::is_same<...>) for const, lvalue-reference, and parenthesized-expression cases.",
     22),
    ("cpp_raw_new", r"\bnew\s+[A-Za-z_:]",
     "Raw allocation requires an explicit, exception-safe ownership strategy; syntax alone does not prove a leak.",
     "Trace all exit paths and run a minimal ownership test under AddressSanitizer.",
     18),
    ("cpp_thread", r"\b(std::thread|std::async|std::mutex|std::atomic)\b",
     "Concurrency primitives are present; correctness depends on synchronization of every conflicting access.",
     "Run ThreadSanitizer on a deterministic reproducer and enumerate shared accesses.",
     18),
]


def register_cpp_rules(expert: "ExpertSystem") -> None:
    """Install C++ semantic rules into an existing ExpertSystem."""
    for name, pattern, hypothesis, test, priority in _RULES:
        def action(match: re.Match[str], text: str, *, h: str = hypothesis, t: str = test) -> str:
            return f"[PLAUSIBLE] {h} Distinguishing test: {t} [NOT_VERIFIED]"
        expert.add_rule(
            name, pattern, action, priority=priority,
            description="C++ reference-semantics hypothesis; source and test evidence required.",
        )
