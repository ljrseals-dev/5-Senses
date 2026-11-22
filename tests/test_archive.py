"""Tests for the Archive subsystem."""

import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from body_of_secrets.archive import Archive
from body_of_secrets.scan import IngestRejected, ScanRecord


class CleanTextScanner:
    def scan(self, path: Path, declared_ext: str) -> ScanRecord:
        data = path.read_bytes()
        return ScanRecord(
            sha256=hashlib.sha256(data).hexdigest(),
            scanner="test-clean",
            engine_version="test",
            sig_version="test",
            sig_age_hours=0.0,
            verdict="clean",
            detail=None,
            magic_type="text/plain",
            declared_extension=declared_ext,
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )


def test_import_and_search():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        with Archive(db, scanner=CleanTextScanner()) as archive:
            archive.import_document(
                title="Hopfield 1982",
                content="Hopfield networks store patterns as energy minima of a recurrent network. Capacity is about 0.15N.",
                source="test-corpus",
                tags=["neural", "associative"],
            )
            archive.import_document(
                title="Kohonen SOM",
                content="Self-organizing maps perform unsupervised topology-preserving projection.",
                source="test-corpus",
                tags=["neural", "unsupervised"],
            )
            assert archive.count() == 2

            hits = archive.search("Hopfield energy capacity")
            assert len(hits) >= 1
            assert "Hopfield" in hits[0].title

            ctx = archive.context_for_query("associative memory energy")
            assert "Hopfield" in ctx or "energy" in ctx.lower()


def test_get_document():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        with Archive(db) as archive:
            doc_id = archive.import_document(
                title="PDP",
                content="Parallel Distributed Processing volumes introduced connectionism to a wide audience.",
                source="rumelhart-1986",
            )
            doc = archive.get(doc_id)
            assert doc is not None
            assert doc.title == "PDP"
            assert "connectionism" in doc.content


def test_documents_with_same_prefix_keep_distinct_ids():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        prefix = "same opening text " * 20
        with Archive(db) as archive:
            first_id = archive.import_document(
                title="Reference A",
                content=prefix + "unique ending alpha",
                source="same-source",
            )
            second_id = archive.import_document(
                title="Reference A",
                content=prefix + "unique ending beta",
                source="same-source",
            )

            assert first_id != second_id
            assert archive.count() == 2
            assert archive.get(first_id).content.endswith("unique ending alpha")
            assert archive.get(second_id).content.endswith("unique ending beta")



def test_unavailable_scanner_fails_closed_without_database_mutation():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "unscanned.txt"
        path.write_text("untrusted document", encoding="utf-8")
        with Archive(Path(tmp) / "test.db") as archive:
            try:
                archive.import_text_file(path)
            except IngestRejected as exc:
                assert "degraded" in str(exc)
            else:
                raise AssertionError("unavailable scanner must reject import")
            assert archive.count() == 0


def test_elf_payload_disguised_as_pdf_is_rejected_before_database_write():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "document.pdf"
        path.write_bytes(b"\\x7fELF" + b"fake executable")
        with Archive(Path(tmp) / "test.db", scanner=CleanTextScanner()) as archive:
            try:
                archive.import_text_file(path)
            except IngestRejected as exc:
                assert "application/x-elf" in str(exc)
            else:
                raise AssertionError("ELF payload must be rejected")
            assert archive.count() == 0


def test_same_doc_id_with_changed_bytes_is_scanned_again_and_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "replace.txt"
        path.write_text("first clean text", encoding="utf-8")
        class SwitchableScanner(CleanTextScanner):
            reject = False
            def scan(self, path: Path, declared_ext: str) -> ScanRecord:
                record = super().scan(path, declared_ext)
                if self.reject:
                    return ScanRecord(
                        sha256=record.sha256, scanner=record.scanner,
                        engine_version=record.engine_version, sig_version=record.sig_version,
                        sig_age_hours=record.sig_age_hours, verdict="malware",
                        detail="test detection", magic_type=record.magic_type,
                        declared_extension=declared_ext, scanned_at=record.scanned_at,
                    )
                return record
        scanner = SwitchableScanner()
        with Archive(Path(tmp) / "test.db", scanner=scanner) as archive:
            doc_id = archive.import_text_file(path)
            original = archive.get(doc_id).content
            path.write_text("changed payload", encoding="utf-8")
            scanner.reject = True
            try:
                archive.import_document(
                    title=path.name,
                    content="changed payload",
                    source=str(path),
                    doc_id=doc_id,
                )
            except IngestRejected:
                pass
            else:
                raise AssertionError("changed content must be scanned and rejected")
            assert archive.get(doc_id).content == original



def test_clean_verdict_without_signature_metadata_is_rejected():
    class UnsubstantiatedCleanScanner(CleanTextScanner):
        def scan(self, path: Path, declared_ext: str) -> ScanRecord:
            record = super().scan(path, declared_ext)
            return ScanRecord(
                sha256=record.sha256, scanner="scanner-without-signatures",
                engine_version=None, sig_version=None, sig_age_hours=None,
                verdict="clean", detail=None, magic_type=record.magic_type,
                declared_extension=declared_ext, scanned_at=record.scanned_at,
            )
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "document.txt"
        path.write_text("ordinary text", encoding="utf-8")
        with Archive(Path(tmp) / "test.db", scanner=UnsubstantiatedCleanScanner()) as archive:
            try:
                archive.import_text_file(path)
            except IngestRejected as exc:
                assert "cannot substantiate" in str(exc)
            else:
                raise AssertionError("unsubstantiated clean verdict must be rejected")
            assert archive.count() == 0


def test_pdf_extension_is_rejected_even_when_payload_is_text():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "document.pdf"
        path.write_text("ordinary text", encoding="utf-8")
        with Archive(Path(tmp) / "test.db", scanner=CleanTextScanner()) as archive:
            try:
                archive.import_text_file(path)
            except IngestRejected as exc:
                assert "unsupported declared extension" in str(exc)
            else:
                raise AssertionError("unsupported extension must be rejected")
            assert archive.count() == 0
