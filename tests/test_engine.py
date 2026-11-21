"""Integration tests for provider and execution-mode isolation."""

from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from body_of_secrets.brain import Engine
from body_of_secrets.brain import engine as engine_module
from body_of_secrets.brain.modes import get_mode
from body_of_secrets.brain.providers import CallableProvider


def fake_complete(system: str, user: str) -> str:
    return (
        "This is a test answer grounded in classical principles [CONSENSUS].\n\n"
        "TRUTH_STATUS: CONSENSUS"
    )


def test_provider_modes_can_use_injected_provider():
    engine = Engine(provider=CallableProvider(fake_complete))
    answer = engine.ask("An unmatched question with no expert rule", mode="HYBRID")

    assert answer.mode == "HYBRID"
    assert answer.truth_status == "CONSENSUS"
    assert answer.classical is False
    assert len(answer.evidence) >= 1


@pytest.mark.parametrize("mode", ["CLASSICAL", "ARCHIVE", "AUTO"])
def test_offline_modes_never_resolve_default_provider(monkeypatch, mode):
    def forbidden_provider():
        raise AssertionError("offline mode attempted provider discovery")

    monkeypatch.setattr(engine_module, "default_provider", forbidden_provider)
    answer = Engine(require_llm=True).ask(
        "zzqx unmatched gibberish question 12345", mode=mode
    )

    assert answer.truth_status == "UNKNOWN"
    assert answer.classical is True


def test_archive_mode_does_not_use_expert_rules_or_injected_provider():
    calls = []
    provider = CallableProvider(
        lambda system, user: calls.append((system, user)) or fake_complete(system, user)
    )
    answer = Engine(provider=provider).ask(
        "What is a Hopfield network?", mode="ARCHIVE"
    )

    assert answer.truth_status == "UNKNOWN"
    assert answer.sources == []
    assert "No relevant" in answer.answer
    assert calls == []


def test_classical_expert_rule_answers_without_provider():
    answer = Engine(provider=CallableProvider(fake_complete)).ask(
        "What is a Hopfield network?", mode="CLASSICAL"
    )

    assert answer.mode == "CLASSICAL"
    assert answer.classical is True
    assert "Hopfield" in answer.answer


def test_mode_provider_permissions_are_explicit():
    assert get_mode("CLASSICAL").allows_provider is False
    assert get_mode("ARCHIVE").allows_provider is False
    assert get_mode("RESEARCH").allows_provider is True
    assert get_mode("AUDIT").allows_provider is True
    assert get_mode("HYBRID").allows_provider is True


def test_optional_provider_sdk_missing_falls_back_to_classical(monkeypatch):
    calls = []

    def unavailable_provider():
        calls.append(True)
        raise ImportError("optional Anthropic SDK is not installed")

    monkeypatch.setattr(engine_module, "default_provider", unavailable_provider)
    engine = Engine()
    first = engine.ask("An unmatched question", mode="RESEARCH")
    second = engine.ask("Another unmatched question", mode="RESEARCH")

    assert first.classical is True
    assert second.classical is True
    assert "no LLM provider" in first.answer
    assert len(calls) == 1


def test_required_provider_surfaces_missing_optional_sdk(monkeypatch):
    def unavailable_provider():
        raise ImportError("optional Anthropic SDK is not installed")

    monkeypatch.setattr(engine_module, "default_provider", unavailable_provider)
    with pytest.raises(ImportError, match="optional Anthropic SDK"):
        Engine(require_llm=True).ask("Research this", mode="RESEARCH")


def test_default_provider_is_cached(monkeypatch):
    calls = []
    provider = CallableProvider(fake_complete)

    def resolve_provider():
        calls.append(True)
        return provider

    monkeypatch.setattr(engine_module, "default_provider", resolve_provider)
    engine = Engine()

    first = engine.ask("First research question", mode="RESEARCH")
    second = engine.ask("Second research question", mode="RESEARCH")

    assert first.classical is False
    assert second.classical is False
    assert len(calls) == 1


def test_concurrent_provider_discovery_is_single_flight(monkeypatch):
    calls = []
    calls_lock = threading.Lock()
    provider = CallableProvider(fake_complete)

    def resolve_provider():
        with calls_lock:
            calls.append(True)
        time.sleep(0.02)
        return provider

    monkeypatch.setattr(engine_module, "default_provider", resolve_provider)
    engine = Engine()
    with ThreadPoolExecutor(max_workers=12) as pool:
        resolved = list(pool.map(lambda _: engine.provider, range(24)))

    assert len(calls) == 1
    assert all(item is provider for item in resolved)
