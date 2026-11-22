from __future__ import annotations

from body_of_secrets.brain.engine import Engine
from body_of_secrets.archive import Archive


class FakeMCPArchive:
    def __init__(self, rows=None, error=None):
        self.rows = rows or []
        self.error = error
        self.calls = 0

    def search(self, query, limit=8):
        self.calls += 1
        if self.error:
            raise self.error
        return self.rows


def test_archive_mode_queries_external_mcp_without_copying_documents(tmp_path):
    client = FakeMCPArchive([{
        "title": "Field notes", "source": "gutenberg/notes.txt",
        "content": "A source-backed passage about ancient navigation.",
    }])
    with Archive(tmp_path / "archive.db") as archive:
        engine = Engine(archive=archive, mcp_archive=client)
        answer = engine.ask("ancient navigation", mode="ARCHIVE")
        assert client.calls == 1
        assert "gutenberg/notes.txt" in answer.answer
        assert answer.sources == ["gutenberg/notes.txt"]
        assert archive.count() == 0


def test_mcp_failure_falls_back_to_local_archive(tmp_path):
    client = FakeMCPArchive(error=RuntimeError("server unavailable"))
    with Archive(tmp_path / "archive.db") as archive:
        archive.import_document(
            "Navigation", "A sextant measures angles for navigation.",
            "local/handbook.md",
        )
        answer = Engine(archive=archive, mcp_archive=client).ask(
            "sextant navigation", mode="ARCHIVE"
        )
        assert "local/handbook.md" in answer.answer
        assert answer.sources == ["local/handbook.md"]


def test_offline_mcp_retrieval_does_not_resolve_llm_provider(tmp_path, monkeypatch):
    client = FakeMCPArchive([{
        "title": "Notes", "source": "remote/notes.md", "content": "Documented fact."
    }])
    with Archive(tmp_path / "archive.db") as archive:
        engine = Engine(archive=archive, mcp_archive=client)
        answer = engine.ask("documented fact", mode="ARCHIVE")
        assert answer.classical is True
        assert answer.truth_status == "UNKNOWN"
