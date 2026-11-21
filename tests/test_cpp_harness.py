from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from body_of_secrets.cpp_harness import load_fixture_manifest, run_fixture, sha256_file


REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "tests" / "fixtures" / "cpp" / "manifest.json"
COMPILER = os.environ.get("CPP_FIXTURE_COMPILER", "g++")


def test_manifest_contains_only_allowlisted_independent_fixtures():
    root, payload = load_fixture_manifest(MANIFEST)
    assert payload["external_source_code_included"] is False
    assert len(payload["fixtures"]) == 5
    for fixture in payload["fixtures"]:
        source = (root / fixture["path"]).resolve()
        assert root in source.parents
        assert source.is_file()
        assert sha256_file(source) == fixture["sha256"]


def test_manifest_rejects_path_traversal(tmp_path):
    manifest = {
        "schema_version": 1,
        "external_source_code_included": False,
        "fixtures": [{
            "id": "bad.path",
            "path": "../outside.cpp",
            "standard": "c++11",
            "expected": "CLEAN",
            "sanitizers": ["address"],
            "timeout_seconds": 5
        }]
    }
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="stay within"):
        load_fixture_manifest(path)


def test_unknown_fixture_id_is_rejected():
    if not shutil.which(COMPILER):
        pytest.skip("g++ is not installed")
    with pytest.raises(ValueError, match="unknown fixture ID"):
        run_fixture("not-a-real-fixture", compiler_name=COMPILER, manifest_path=MANIFEST)


@pytest.mark.parametrize(
    ("fixture_id", "expected"),
    [
        ("cpp.compile.unique-ptr-copy.v1", "COMPILE_FAIL"),
        ("cpp.link.pure-virtual-dtor.v1", "LINK_FAIL"),
        ("cpp.asan.heap-use-after-free.v1", "ASAN_FINDING"),
        ("cpp.ubsan.signed-overflow.v1", "UBSAN_FINDING"),
        ("cpp.clean.unique-ptr-transfer.v1", "CLEAN"),
    ],
)
def test_fixture_reproduces_expected_compiler_or_sanitizer_result(fixture_id, expected):
    if not shutil.which(COMPILER):
        pytest.skip("g++ is not installed")
    result = run_fixture(fixture_id, compiler_name=COMPILER, manifest_path=MANIFEST)
    assert result["expected"] == expected
    assert result["passed"], json.dumps(result, indent=2)
    assert len(result["source_sha256"]) == 64
    assert result["external_source_code_included"] is False
    if expected in {"COMPILE_FAIL", "LINK_FAIL"}:
        assert result["runs"][0]["failure_signature_matched"] is True
    if expected == "CLEAN":
        assert [run["outcome"] for run in result["runs"]] == ["CLEAN", "CLEAN"]


def test_verify_cpp_cli_archives_the_compiler_evidence(tmp_path):
    if not shutil.which(COMPILER):
        pytest.skip("g++ is not installed")
    from body_of_secrets.archive import Archive
    from body_of_secrets.interface.cli import main

    db_path = tmp_path / "verification.db"
    exit_code = main([
        "--db", str(db_path),
        "verify-cpp",
        "--fixture", "cpp.clean.unique-ptr-transfer.v1",
        "--compiler", COMPILER,
        "--manifest", str(MANIFEST),
    ])
    assert exit_code == 0
    with Archive(db_path) as archive:
        assert archive.count() == 1
        hits = archive.search("cpp.clean.unique-ptr-transfer.v1", limit=5)
        assert hits
