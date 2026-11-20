"""Memory subsystem — simple associative / key-value store with provenance."""

from __future__ import annotations

import json
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class MemoryEntry:
    key: str
    value: Any
    source: str
    tags: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)


class Memory:
    """Lightweight persistent associative memory."""

    def __init__(self, db_path: str | Path = "data/memory.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                key         TEXT PRIMARY KEY,
                value       TEXT NOT NULL,
                source      TEXT NOT NULL,
                tags        TEXT NOT NULL DEFAULT '[]',
                created_at  REAL NOT NULL,
                updated_at  REAL NOT NULL
            )
            """
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "Memory":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def put(
        self,
        key: str,
        value: Any,
        *,
        source: str = "user",
        tags: list[str] | None = None,
    ) -> None:
        now = time.time()
        tags = tags or []
        self._conn.execute(
            """
            INSERT INTO memories (key, value, source, tags, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                source = excluded.source,
                tags = excluded.tags,
                updated_at = excluded.updated_at
            """,
            (key, json.dumps(value), source, json.dumps(tags), now, now),
        )
        self._conn.commit()

    def get(self, key: str) -> MemoryEntry | None:
        cur = self._conn.execute("SELECT * FROM memories WHERE key = ?", (key,))
        row = cur.fetchone()
        if not row:
            return None
        return MemoryEntry(
            key=row["key"],
            value=json.loads(row["value"]),
            source=row["source"],
            tags=json.loads(row["tags"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def delete(self, key: str) -> bool:
        cur = self._conn.execute("DELETE FROM memories WHERE key = ?", (key,))
        self._conn.commit()
        return cur.rowcount > 0

    def search(self, query: str, *, limit: int = 10) -> list[MemoryEntry]:
        """Simple substring search over keys and serialized values."""
        q = f"%{query.lower()}%"
        cur = self._conn.execute(
            """
            SELECT * FROM memories
            WHERE lower(key) LIKE ? OR lower(value) LIKE ?
            ORDER BY updated_at DESC
            LIMIT ?
            """,
            (q, q, limit),
        )
        return [
            MemoryEntry(
                key=r["key"],
                value=json.loads(r["value"]),
                source=r["source"],
                tags=json.loads(r["tags"]),
                created_at=r["created_at"],
                updated_at=r["updated_at"],
            )
            for r in cur.fetchall()
        ]

    def list_keys(self) -> list[str]:
        cur = self._conn.execute("SELECT key FROM memories ORDER BY key")
        return [r["key"] for r in cur.fetchall()]
