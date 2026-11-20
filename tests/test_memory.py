"""Tests for the Memory subsystem."""

import tempfile
from pathlib import Path

from body_of_secrets.memory import Memory


def test_put_get():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "mem.db"
        with Memory(db) as mem:
            mem.put("hopfield.capacity", 0.15, source="literature", tags=["neural"])
            entry = mem.get("hopfield.capacity")
            assert entry is not None
            assert entry.value == 0.15
            assert entry.source == "literature"


def test_search():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "mem.db"
        with Memory(db) as mem:
            mem.put("topic.hopfield", "associative memory")
            mem.put("topic.kohonen", "self organizing maps")
            results = mem.search("hopfield")
            assert len(results) >= 1
            assert "hopfield" in results[0].key
