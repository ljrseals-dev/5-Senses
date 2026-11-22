"""Offline document corpus bridge into the canonical BODY OF SECRETS Archive."""
from __future__ import annotations
import hashlib, json, mimetypes, os
from pathlib import Path
from typing import Iterable
from body_of_secrets.archive import Archive

SUPPORTED_SUFFIXES = {".txt", ".md", ".rst", ".text"}

def iter_documents(root: Path, max_file_bytes: int = 25 * 1024 * 1024) -> Iterable[Path]:
    root = root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        try:
            if path.stat().st_size <= max_file_bytes:
                yield path
        except OSError:
            continue

def ingest_directory(archive: Archive, root: str | Path, source_prefix: str | None = None,
                     max_file_bytes: int = 25 * 1024 * 1024) -> dict[str, object]:
    base = Path(root).resolve()
    imported = skipped = 0
    errors: list[dict[str, str]] = []
    for path in iter_documents(base, max_file_bytes):
        try:
            content = path.read_text(encoding="utf-8", errors="strict")
            if not content.strip():
                skipped += 1
                continue
            relative = path.relative_to(base).as_posix()
            source = f"{source_prefix.rstrip('/')}/{relative}" if source_prefix else str(path)
            digest = hashlib.sha256(json.dumps([source, path.name, content], ensure_ascii=False,
                separators=(",", ":")).encode("utf-8")).hexdigest()
            archive.import_document(title=path.name, content=content, source=source,
                tags=["offline-doc-mcp", "local-corpus"],
                metadata={"ingestion":"offline-doc-mcp-bridge","relative_path":relative,
                          "sha256":digest,"mime_type":mimetypes.guess_type(path.name)[0] or "text/plain"},
                doc_id=f"odm_{digest[:32]}")
            imported += 1
        except (OSError, UnicodeError, ValueError) as exc:
            errors.append({"path":str(path),"error":type(exc).__name__})
    return {"imported":imported,"skipped":skipped,"errors":errors,"archive_documents":archive.count()}

def search_archive(archive: Archive, query: str, limit: int = 8) -> list[dict[str, object]]:
    if not isinstance(query,str) or not query.strip():
        raise ValueError("query must not be empty")
    if not 1 <= limit <= 50:
        raise ValueError("limit must be between 1 and 50")
    results=[]
    for hit in archive.search(query,limit=limit):
        doc=archive.get(hit.doc_id)
        if doc is not None:
            results.append({"doc_id":doc.doc_id,"title":doc.title,"source":doc.source,
                "score":hit.score,"snippet":hit.snippet,"metadata":doc.metadata})
    return results

def mcp_server() -> None:
    try:
        from mcp.server.fastmcp import FastMCP
    except ImportError as exc:
        raise RuntimeError("Install BODY OF SECRETS with the offline-docs extra") from exc
    db_path=Path(os.environ.get("BODY_OF_SECRETS_DB","data/archive.db"))
    server=FastMCP("body-of-secrets-offline-archive")
    @server.tool()
    def search_documents(query: str, limit: int = 8) -> str:
        """Search the local provenance-aware Archive; no network access."""
        with Archive(db_path) as archive:
            return json.dumps({"results":search_archive(archive,query,limit)},ensure_ascii=False)
    @server.tool()
    def archive_stats() -> str:
        """Return local Archive document count."""
        with Archive(db_path) as archive:
            return json.dumps({"documents":archive.count(),"database":str(db_path)})
    server.run(transport="stdio")
