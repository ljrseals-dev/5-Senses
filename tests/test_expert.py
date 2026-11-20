"""Tests for the expert system."""

from body_of_secrets.expert import build_default_expert


def test_hopfield_rule():
    es = build_default_expert()
    result = es.first_match("Tell me about Hopfield networks")
    assert result is not None
    assert result.matched
    assert "Hopfield" in result.output
    assert "energy" in result.output.lower() or "associative" in result.output.lower()


def test_no_match():
    es = build_default_expert()
    result = es.first_match("What is the capital of France?")
    assert result is None or not result.matched


def test_pdp_rule():
    es = build_default_expert()
    result = es.first_match("Explain Parallel Distributed Processing")
    assert result is not None
    assert result.matched
    assert "Rumelhart" in result.output or "1986" in result.output
