import hashlib
from datetime import datetime, timezone
from pathlib import Path

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
from body_of_secrets.scouting.integration import import_text_collection


def test_import_collection_is_repeat_safe(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "note.txt").write_text("Hopfield associative memory", encoding="utf-8")
    archive = Archive(tmp_path / "archive.db", scanner=CleanTextScanner())
    try:
        first = import_text_collection(corpus, archive)
        second = import_text_collection(corpus, archive)
        assert len(first["imported"]) == 1
        assert len(second["skipped_existing"]) == 1
        assert archive.count() == 1
    finally:
        archive.close()
