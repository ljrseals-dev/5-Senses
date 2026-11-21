"""Archive subsystem — local document store with provenance and BM25 search."""

from __future__ import annotations

import hashlib
import json
import math
import re
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


_TOKEN_RE = re.compile(r"[a-z0-9]+", re.IGNORECASE)


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass
class Document:
    doc_id: str
    title: str
    content: str
    source: str
    tags: list[str] = field(default_factory=list)
    imported_at: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)


@dataclass
class SearchHit:
    doc_id: str
    title: str
    source: str
    score: float
    snippet: str


class Archive:
    """SQLite-backed document archive with simple BM25 ranking."""

    def __init__(self, db_path: str | Path = "data/archive.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id     TEXT PRIMARY KEY,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                source     TEXT NOT NULL,
                tags       TEXT NOT NULL DEFAULT '[]',
                imported_at REAL NOT NULL,
                metadata   TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS term_stats (
                term       TEXT PRIMARY KEY,
                df         INTEGER NOT NULL
            );

            CREATE TABLE IF NOT EXISTS doc_terms (
                doc_id     TEXT NOT NULL,
                term       TEXT NOT NULL,
                tf         INTEGER NOT NULL,
                PRIMARY KEY (doc_id, term),
                FOREIGN KEY (doc_id) REFERENCES documents(doc_id)
            );

            CREATE INDEX IF NOT EXISTS idx_doc_terms_term ON doc_terms(term);
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Archive":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Import
    # ------------------------------------------------------------------

    def import_document(
        self,
        title: str,
        content: str,
        source: str,
        *,
        tags: list[str] | None = None,
        metadata: dict | None = None,
        doc_id: str | None = None,
    ) -> str:
        if not doc_id:
            identity = json.dumps([source, title, content], ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            digest = hashlib.sha256(identity).hexdigest()
            doc_id = f"doc_{digest}"

        tags = tags or []
        metadata = metadata or {}
        now = time.time()

        cur = self._conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO documents
            (doc_id, title, content, source, tags, imported_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (doc_id, title, content, source, json.dumps(tags), now, json.dumps(metadata)),
        )

        # Remove old term stats for this doc
        cur.execute("SELECT term, tf FROM doc_terms WHERE doc_id = ?", (doc_id,))
        old = cur.fetchall()
        for row in old:
            cur.execute(
                "UPDATE term_stats SET df = df - 1 WHERE term = ? AND df > 0",
                (row["term"],),
            )
        cur.execute("DELETE FROM doc_terms WHERE doc_id = ?", (doc_id,))

        # Index new terms
        tokens = tokenize(content)
        tf: dict[str, int] = {}
        for t in tokens:
            tf[t] = tf.get(t, 0) + 1

        for term, count in tf.items():
            cur.execute(
                "INSERT INTO doc_terms (doc_id, term, tf) VALUES (?, ?, ?)",
                (doc_id, term, count),
            )
            cur.execute(
                """
                INSERT INTO term_stats (term, df) VALUES (?, 1)
                ON CONFLICT(term) DO UPDATE SET df = df + 1
                """,
                (term,),
            )

        self._conn.commit()
        return doc_id

    def import_text_file(self, path: str | Path, *, source: str | None = None) -> str:
        path = Path(path)
        content = path.read_text(encoding="utf-8", errors="strict")
        return self.import_document(
            title=path.name,
            content=content,
            source=source or str(path),
        )

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def get(self, doc_id: str) -> Document | None:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
        row = cur.fetchone()
        if not row:
            return None
        return Document(
            doc_id=row["doc_id"],
            title=row["title"],
            content=row["content"],
            source=row["source"],
            tags=json.loads(row["tags"]),
            imported_at=row["imported_at"],
            metadata=json.loads(row["metadata"]),
        )

    def list_documents(self) -> list[Document]:
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM documents ORDER BY imported_at DESC")
        return [
            Document(
                doc_id=r["doc_id"],
                title=r["title"],
                content=r["content"],
                source=r["source"],
                tags=json.loads(r["tags"]),
                imported_at=r["imported_at"],
                metadata=json.loads(r["metadata"]),
            )
            for r in cur.fetchall()
        ]

    def count(self) -> int:
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM documents")
        return int(cur.fetchone()["n"])

    # ------------------------------------------------------------------
    # BM25 search
    # ------------------------------------------------------------------

    def search(self, query: str, *, limit: int = 5, k1: float = 1.2, b: float = 0.75) -> list[SearchHit]:
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
            raise ValueError("limit must be a positive integer")
        if isinstance(k1, bool) or not isinstance(k1, (int, float)) or not math.isfinite(k1) or k1 <= 0:
            raise ValueError("k1 must be a positive finite number")
        if isinstance(b, bool) or not isinstance(b, (int, float)) or not math.isfinite(b) or not 0 <= b <= 1:
            raise ValueError("b must be a finite number between 0 and 1")
        query_terms = tokenize(query)
        if not query_terms:
            return []

        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) AS n FROM documents")
        N = cur.fetchone()["n"]
        if N == 0:
            return []

        # Average document length
        cur.execute(
            """
            SELECT AVG(length) AS avgdl FROM (
                SELECT SUM(tf) AS length FROM doc_terms GROUP BY doc_id
            )
            """
        )
        avgdl = cur.fetchone()["avgdl"] or 1.0

        # Document frequencies
        dfs: dict[str, int] = {}
        for term in set(query_terms):
            cur.execute("SELECT df FROM term_stats WHERE term = ?", (term,))
            row = cur.fetchone()
            dfs[term] = row["df"] if row else 0

        # Score each document that contains at least one query term
        scores: dict[str, float] = {}
        for term in set(query_terms):
            df = dfs.get(term, 0)
            if df == 0:
                continue
            idf = math.log(1 + (N - df + 0.5) / (df + 0.5))
            cur.execute(
                "SELECT doc_id, tf FROM doc_terms WHERE term = ?",
                (term,),
            )
            for row in cur.fetchall():
                doc_id = row["doc_id"]
                tf = row["tf"]
                # Document length
                cur.execute(
                    "SELECT SUM(tf) AS length FROM doc_terms WHERE doc_id = ?",
                    (doc_id,),
                )
                dl = cur.fetchone()["length"] or 1
                denom = tf + k1 * (1 - b + b * dl / avgdl)
                score = idf * (tf * (k1 + 1)) / denom
                scores[doc_id] = scores.get(doc_id, 0.0) + score

        # Rank and build hits
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]
        hits: list[SearchHit] = []
        for doc_id, score in ranked:
            doc = self.get(doc_id)
            if not doc:
                continue
            # Simple snippet: first 240 chars that contain a query term
            snippet = self._make_snippet(doc.content, query_terms)
            hits.append(
                SearchHit(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    source=doc.source,
                    score=round(score, 4),
                    snippet=snippet,
                )
            )
        return hits

    def _make_snippet(self, content: str, query_terms: list[str], width: int = 240) -> str:
        lower = content.lower()
        for term in query_terms:
            idx = lower.find(term)
            if idx >= 0:
                start = max(0, idx - 40)
                end = min(len(content), start + width)
                snippet = content[start:end].replace("\n", " ")
                if start > 0:
                    snippet = "…" + snippet
                if end < len(content):
                    snippet = snippet + "…"
                return snippet
        return content[:width].replace("\n", " ") + ("…" if len(content) > width else "")

    def context_for_query(self, query: str, *, limit: int = 3) -> str:
        """Return a provenance-aware context string suitable for the Brain."""
        hits = self.search(query, limit=limit)
        if not hits:
            return ""
        parts = []
        for i, hit in enumerate(hits, 1):
            doc = self.get(hit.doc_id)
            if not doc:
                continue
            parts.append(
                f"[{i}] Source: {doc.source} | Title: {doc.title}\n"
                f"{hit.snippet}\n"
                f"(score={hit.score})"
            )
        return "\n\n".join(parts)
