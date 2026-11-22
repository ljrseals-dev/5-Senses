"""Optional stdio MCP client for the external refactored-spoon corpus.

The external corpus remains independently owned and indexed by refactored-spoon.
This adapter only queries it; it never copies remote documents into the local Archive.
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
import threading
from typing import Any


class MCPArchiveClient:
    """Query a configured local MCP document server over stdio."""

    def __init__(self, command: str, *, timeout: float = 15.0, tool_name: str = "search_documents"):
        argv = shlex.split(command)
        if not argv:
            raise ValueError("MCP server command must not be empty")
        if not 0.1 <= timeout <= 120:
            raise ValueError("MCP timeout must be between 0.1 and 120 seconds")
        self.command = argv[0]
        self.args = argv[1:]
        self.timeout = timeout
        self.tool_name = tool_name

    @classmethod
    def from_environment(cls) -> "MCPArchiveClient | None":
        command = os.environ.get("BOS_OFFLINE_DOC_MCP_COMMAND", "").strip()
        if not command:
            return None
        try:
            timeout = float(os.environ.get("BOS_OFFLINE_DOC_MCP_TIMEOUT", "15"))
            return cls(command, timeout=timeout)
        except (TypeError, ValueError):
            return None

    async def _search_async(self, query: str, limit: int) -> list[dict[str, Any]]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise RuntimeError(
                "MCP client support requires Python 3.11+ and the 'mcp-client' extra"
            ) from exc

        server = StdioServerParameters(
            command=self.command,
            args=self.args,
            cwd=os.environ.get("BOS_OFFLINE_DOC_MCP_CWD") or None,
        )
        async with stdio_client(server) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(
                    self.tool_name, {"query": query, "limit": limit}
                )
                if getattr(result, "isError", False):
                    raise RuntimeError("MCP document search returned an error")
                for item in result.content:
                    text = getattr(item, "text", None)
                    if not isinstance(text, str):
                        continue
                    payload = json.loads(text)
                    rows = payload.get("results", [])
                    if not isinstance(rows, list):
                        raise ValueError("MCP search response has an invalid results field")
                    return [
                        row for row in rows
                        if isinstance(row, dict)
                        and isinstance(row.get("title"), str)
                        and isinstance(row.get("source") or row.get("path"), str)
                        and isinstance(row.get("content") or row.get("snippet"), str)
                    ]
                return []

    @staticmethod
    def _fts_query(query: str) -> str:
        # refactored-spoon currently passes queries to SQLite FTS5 MATCH.
        # Quote plain tokens so natural-language punctuation cannot become FTS syntax.
        tokens = re.findall(r"\w+", query, flags=re.UNICODE)
        if not tokens:
            raise ValueError("query must contain searchable words")
        return " AND ".join('"'+token.replace('"', '""')+'"' for token in tokens)

    def search(self, query: str, limit: int = 8) -> list[dict[str, Any]]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must not be empty")
        if not 1 <= limit <= 50:
            raise ValueError("limit must be between 1 and 50")
        safe_query = self._fts_query(query)

        async def bounded() -> list[dict[str, Any]]:
            return await asyncio.wait_for(
                self._search_async(safe_query, limit), timeout=self.timeout
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(bounded())

        # The Brain API is synchronous. If called from an async host, isolate
        # the MCP event loop in a worker thread rather than nesting asyncio.run.
        result: list[list[dict[str, Any]]] = []
        failure: list[BaseException] = []

        def runner() -> None:
            try:
                result.append(asyncio.run(bounded()))
            except BaseException as exc:
                failure.append(exc)

        worker = threading.Thread(target=runner, daemon=True)
        worker.start()
        worker.join(self.timeout + 2.0)
        if worker.is_alive():
            raise TimeoutError("MCP document search timed out")
        if failure:
            raise failure[0]
        return result[0] if result else []
