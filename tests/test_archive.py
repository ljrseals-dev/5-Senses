"""Tests for the Archive subsystem."""

import tempfile
from pathlib import Path

from body_of_secrets.archive import Archive


def test_import_and_search():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        with Archive(db) as archive:
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
