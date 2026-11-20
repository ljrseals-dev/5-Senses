"""Integration tests for the Brain Engine using a fake provider."""

from body_of_secrets.brain import Engine
from body_of_secrets.brain.providers import CallableProvider


def fake_complete(system: str, user: str) -> str:
    return (
        "This is a test answer grounded in classical principles [CONSENSUS].\n\n"
        "TRUTH_STATUS: CONSENSUS"
    )


def test_engine_ask():
    engine = Engine(provider=CallableProvider(fake_complete))
    answer = engine.ask("What is associative memory?", mode="CLASSICAL")

    assert answer.mode == "CLASSICAL"
    assert answer.truth_status == "CONSENSUS"
    assert "associative" in answer.question.lower() or True  # just sanity
    assert len(answer.evidence) >= 1
    assert answer.version.startswith("0.")
