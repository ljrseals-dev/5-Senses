"""Tests for non-executing C++ triage and epistemic safeguards."""
import json
import pytest

from body_of_secrets.cpp_debug import analyze_cpp_source, report_json

def test_source_observations_create_unverified_hypotheses():
    report = analyze_cpp_source("int* make() { int* p = new int(1); delete p; return p; }")
    assert report.source_sha256
    assert report.observations
    assert report.hypotheses
    assert all(h.status == "PLAUSIBLE" for h in report.hypotheses)
    assert report.verified_cause is None
    assert report.minimal_fix is None
    assert report.environment["execution_performed"] is False

def test_no_matches_means_no_invented_hypotheses():
    report = analyze_cpp_source("int add(int a, int b) { return a + b; }")
    assert report.observations == []
    assert report.hypotheses == []
    assert report.verified_cause is None

def test_rejects_unsupported_standard():
    with pytest.raises(ValueError):
        analyze_cpp_source("int main() {}", standard="c++23")

def test_report_is_json_serializable_and_provenance_bound():
    report = analyze_cpp_source("void f() { std::thread t(work); }", source_path="f.cpp")
    data = json.loads(report_json(report))
    assert data["provenance"][0]["sha256"] == report.source_sha256
    assert data["hypotheses"][0]["status"] == "PLAUSIBLE"
    assert data["environment"]["compiler"] is None
