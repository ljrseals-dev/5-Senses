from pathlib import Path

from body_of_secrets.archive import Archive
from body_of_secrets.scouting.integration import import_text_collection


def test_import_collection_is_repeat_safe(tmp_path: Path) -> None:
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    (corpus / "note.txt").write_text("Hopfield associative memory", encoding="utf-8")
    archive = Archive(tmp_path / "archive.db")
    try:
        first = import_text_collection(corpus, archive)
        second = import_text_collection(corpus, archive)
        assert len(first["imported"]) == 1
        assert len(second["skipped_existing"]) == 1
        assert archive.count() == 1
    finally:
        archive.close()
