from __future__ import annotations

import pytest

from body_of_secrets.archive import Archive


def test_document_ids_include_full_content_not_only_prefix(tmp_path):
    prefix = "a" * 250
    with Archive(tmp_path / "archive.db") as archive:
        first = archive.import_document("title", prefix + " first-tail", "source")
        second = archive.import_document("title", prefix + " second-tail", "source")
        assert first != second
        assert archive.count() == 2


def test_reimport_updates_document_and_search_index_consistently(tmp_path):
    with Archive(tmp_path / "archive.db") as archive:
        doc_id = archive.import_document("title", "alpha token", "source", doc_id="stable")
        archive.import_document("title", "beta token", "source", doc_id=doc_id)
        assert archive.count() == 1
        assert archive.search("alpha") == []
        assert [hit.doc_id for hit in archive.search("beta")] == ["stable"]


@pytest.mark.parametrize("kwargs", [
    {"limit": 0},
    {"limit": True},
    {"k1": 0},
    {"k1": float("nan")},
    {"b": -0.1},
    {"b": 1.1},
])
def test_search_rejects_invalid_bm25_parameters(tmp_path, kwargs):
    with Archive(tmp_path / "archive.db") as archive:
        with pytest.raises(ValueError):
            archive.search("query", **kwargs)


def test_import_text_file_rejects_invalid_utf8_instead_of_replacing(tmp_path):
    source = tmp_path / "invalid.txt"
    source.write_bytes(b"valid\xffinvalid")
    with Archive(tmp_path / "archive.db") as archive:
        with pytest.raises(UnicodeDecodeError):
            archive.import_text_file(source)
        assert archive.count() == 0
