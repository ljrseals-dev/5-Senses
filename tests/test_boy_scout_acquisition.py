from __future__ import annotations

import hashlib
from datetime import datetime, timezone
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from body_of_secrets.scouting import corpora
from body_of_secrets.scouting.integrity import (
    build_manifest,
    sha256_file,
    verify_manifest,
    write_manifest,
)
from body_of_secrets.scouting.models import (
    ModelCandidate,
    acquire_model,
    write_model_inventory,
)
from body_of_secrets.scouting.corpora import CorpusCandidate, write_corpus_inventory
from body_of_secrets.scouting.integration import import_text_collection
from body_of_secrets.archive import Archive
from body_of_secrets.scan import ScanRecord


class CleanTextScanner:
    def scan(self, path: Path, declared_ext: str) -> ScanRecord:
        data = path.read_bytes()
        return ScanRecord(
            sha256=hashlib.sha256(data).hexdigest(), scanner="test-clean",
            engine_version="test", sig_version="test", sig_age_hours=0.0,
            verdict="clean", detail=None, magic_type="text/plain",
            declared_extension=declared_ext,
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )


def test_sha256_rejects_zero_or_non_integer_chunk_size(tmp_path: Path):
    path = tmp_path / "payload.bin"
    path.write_bytes(b"payload")
    with pytest.raises(ValueError, match="chunk_size"):
        sha256_file(path, chunk_size=0)
    with pytest.raises(ValueError, match="chunk_size"):
        sha256_file(path, chunk_size=True)


def test_build_manifest_rejects_symlinks_and_duplicate_paths(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    item = root / "item.txt"
    item.write_text("content", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate"):
        build_manifest([item, item], root)
    alias = root / "alias.txt"
    alias.symlink_to(item)
    with pytest.raises(ValueError, match="symlink"):
        build_manifest([alias], root)


def test_manifest_detects_modified_content(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    item = root / "item.txt"
    item.write_text("original", encoding="utf-8")
    manifest = build_manifest([item], root)
    manifest_path = write_manifest(manifest, tmp_path / "manifest.json")
    item.write_text("modified", encoding="utf-8")
    assert verify_manifest(manifest_path, root) == [
        {"path": "item.txt", "status": "hash_mismatch"}
    ]


def test_manifest_rejects_traversal_and_malformed_entries(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps({
        "schema_version": 1, "algorithm": "sha256",
        "files": [{"path": "../outside", "size_bytes": 1, "sha256": "0" * 64}],
    }), encoding="utf-8")
    with pytest.raises(ValueError, match="unsafe"):
        verify_manifest(manifest_path, root)


def test_write_manifest_never_overwrites_existing_file(tmp_path: Path):
    path = tmp_path / "manifest.json"
    path.write_text("preserve", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_manifest({"schema_version": 1, "algorithm": "sha256", "files": []}, path)
    assert path.read_text(encoding="utf-8") == "preserve"


def test_model_revision_must_be_full_commit_sha(tmp_path: Path):
    with pytest.raises(ValueError, match="40-character"):
        acquire_model("org/model", tmp_path / "model", revision="main")
    assert not (tmp_path / "model").exists()


def test_acquire_model_writes_revision_and_hash_manifest(tmp_path: Path, monkeypatch):
    revision = "a" * 40
    payload = b"model weights"

    def fake_snapshot_download(**kwargs):
        assert kwargs["revision"] == revision
        assert kwargs["repo_id"] == "org/model"
        Path(kwargs["local_dir"], "weights.bin").write_bytes(payload)

    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        SimpleNamespace(snapshot_download=fake_snapshot_download))
    target = acquire_model("org/model", tmp_path / "snapshot", revision=revision)
    manifest = json.loads((target / "model_manifest.json").read_text(encoding="utf-8"))
    assert manifest["revision"] == revision
    assert manifest["repo_id"] == "org/model"
    assert manifest["files"] == [{
        "path": "weights.bin",
        "size_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }]


def test_failed_model_download_removes_exclusive_partial_directory(tmp_path: Path, monkeypatch):
    def failed_download(**kwargs):
        Path(kwargs["local_dir"], "partial.bin").write_bytes(b"partial")
        raise OSError("simulated network failure")

    monkeypatch.setitem(sys.modules, "huggingface_hub",
                        SimpleNamespace(snapshot_download=failed_download))
    target = tmp_path / "snapshot"
    with pytest.raises(OSError, match="simulated network failure"):
        acquire_model("org/model", target, revision="b" * 40)
    assert not target.exists()


def test_model_inventory_rejects_overwrite(tmp_path: Path):
    path = tmp_path / "models.json"
    path.write_text("keep", encoding="utf-8")
    candidate = ModelCandidate(repo_id="org/model")
    with pytest.raises(FileExistsError):
        write_model_inventory([candidate], path)
    assert path.read_text(encoding="utf-8") == "keep"


def test_dataset_search_rejects_invalid_query_and_timeout():
    with pytest.raises(ValueError, match="query"):
        corpora.search_huggingface_datasets(" ")
    with pytest.raises(ValueError, match="timeout"):
        corpora.search_huggingface_datasets("text", timeout=float("nan"))


def test_dataset_search_rejects_malformed_catalog_payload(monkeypatch):
    monkeypatch.setattr(corpora, "_get_json", lambda url, timeout: {"unexpected": []})
    with pytest.raises(TypeError, match="catalog response"):
        corpora.search_huggingface_datasets("history")


def test_dataset_search_validates_tags(monkeypatch):
    monkeypatch.setattr(corpora, "_get_json", lambda url, timeout: [{"id": "org/data", "tags": "not-a-list"}])
    with pytest.raises(ValueError, match="tags"):
        corpora.search_huggingface_datasets("history")


def test_internet_archive_search_rejects_malformed_response(monkeypatch):
    monkeypatch.setattr(corpora, "_get_json", lambda url, timeout: [])
    with pytest.raises(TypeError, match="Internet Archive"):
        corpora.search_internet_archive("history")


def test_corpus_inventory_never_overwrites_existing_file(tmp_path: Path):
    path = tmp_path / "corpora.json"
    path.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_corpus_inventory([CorpusCandidate("archive", "id-1")], path)
    assert path.read_text(encoding="utf-8") == "keep"


def test_import_text_collection_records_stable_sha256_provenance(tmp_path: Path):
    source = tmp_path / "incoming"
    source.mkdir()
    item = source / "record.txt"
    item.write_bytes(b"source text")
    with Archive(tmp_path / "archive.db", scanner=CleanTextScanner()) as archive:
        report = import_text_collection(source, archive)
        assert report["imported"] == [str(item.resolve())]
        document = archive.list_documents()[0]
        assert document.metadata["sha256"] == hashlib.sha256(b"source text").hexdigest()
        assert document.metadata["size_bytes"] == len(b"source text")


def test_import_text_collection_rejects_source_directory_symlink(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(source, target_is_directory=True)
    with Archive(tmp_path / "archive.db", scanner=CleanTextScanner()) as archive:
        with pytest.raises(ValueError, match="source_dir must not be a symlink"):
            import_text_collection(alias, archive)


def test_import_text_collection_does_not_follow_file_symlinks(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    target = tmp_path / "outside.txt"
    target.write_text("outside", encoding="utf-8")
    (source / "linked.txt").symlink_to(target)
    with Archive(tmp_path / "archive.db", scanner=CleanTextScanner()) as archive:
        report = import_text_collection(source, archive)
        assert report["failed"] == [str(source / "linked.txt")]
        assert archive.count() == 0


def test_import_text_collection_requires_positive_integer_limit(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    with Archive(tmp_path / "archive.db", scanner=CleanTextScanner()) as archive:
        with pytest.raises(ValueError, match="positive integer"):
            import_text_collection(source, archive, max_file_bytes=True)
