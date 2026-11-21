"""Tests for metadata-only C++ corpus ingestion and Expert hypotheses."""
import json
from pathlib import Path

import pytest

from body_of_secrets.archive import Archive
from body_of_secrets.cpp_corpus import import_manifest, load_manifest
from body_of_secrets.expert import build_default_expert

MANIFEST = "data/cpp_reference_corpora.json"
revisions = {"bart-cpp": "376ae463ee95ee5723e74322b7fa25a59e972ac9"}


def test_manifest_is_metadata_only_and_rights_held():
    manifest = load_manifest(MANIFEST)
    assert manifest["contains_source_code"] is False
    assert len(manifest["sources"]) == 2
    assert all(source["revision_status"] == "PINNED" for source in manifest["sources"])
    assert all(source["revision"] for source in manifest["sources"])
    assert all(item["rights_status"] == "UNVERIFIED_HOLD" for item in manifest["records"])
    assert all(item["source_path"] for item in manifest["records"])
    assert all(item["source_path_status"] == "VERIFIED_AT_PINNED_REVISION" for item in manifest["records"])
    assert all(item["source_blob_sha"] for item in manifest["records"])


def test_manifest_rejects_embedded_source_code(tmp_path):
    payload = json.loads(Path(MANIFEST).read_text(encoding="utf-8"))
    payload["records"][0]["source_code"] = "int main() {}"
    path = tmp_path / "unsafe.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="source_code"):
        load_manifest(path)


def test_archive_import_is_provenance_bound_and_repeatable(tmp_path):
    with Archive(tmp_path / "archive.db") as archive:
        first = import_manifest(archive, MANIFEST)
        second = import_manifest(archive, MANIFEST)
        assert first == second
        assert len(first) == 8
        doc = archive.get(first[0])
        assert doc is not None
        assert doc.metadata["source_code_included"] is False
        assert doc.metadata["rights_status"] == "UNVERIFIED_HOLD"
        assert doc.metadata["source_repo"] == "BartVandewoestyne/Cpp"
        assert doc.metadata["source_revision"] == revisions["bart-cpp"]\n        assert doc.metadata["source_path"] == "C++98/examples/pure_virtual_destructors.cpp"\n        assert doc.metadata["source_blob_sha"] == "172b422e67aba9e6bd08892590dbbbba72937f13"


@pytest.mark.parametrize(
    ("query", "rule_name", "expected"),
    [
        ("Should I use std::unique_ptr here?", "cpp_unique_ptr", "exclusive ownership"),
        ("Explain std::weak_ptr lifetime", "cpp_weak_ptr", "non-owning observer"),
        ("What does std::move actually do?", "cpp_move", "does not itself move"),
        ("How does std::forward preserve category?", "cpp_forward", "reference collapsing"),
        ("Explain decltype(auto)", "cpp_type_deduction", "decltype"),
        ("Does shared_ptr make my object thread safe?", "cpp_shared_concurrency", "data race"),
        ("Why define a pure virtual destructor?", "cpp_pure_virtual_destructor", "definition"),
    ],
)
def test_cpp_expert_rules_emit_plausible_hypothesis_and_test(query, rule_name, expected):
    expert = build_default_expert()
    results = expert.evaluate(query)
    result = next(item for item in results if item.rule_name == rule_name)
    assert result.matched
    assert "[PLAUSIBLE]" in result.output
    assert "Distinguishing test:" in result.output
    assert expected.lower() in result.output.lower()
