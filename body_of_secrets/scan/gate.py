"""Fail-closed document-ingest scanning primitives (no scanner dependency)."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import ScanRecord


class IngestRejected(Exception):
    """Raised when a document cannot be proven safe to index."""


class Scanner(Protocol):
    def scan(self, path: Path, declared_ext: str) -> ScanRecord: ...


def _magic_type(data: bytes) -> str:
    if data.startswith(b"%PDF-"):
        return "application/pdf"
    if data.startswith(b"\x7fELF"):
        return "application/x-elf"
    if data.startswith(b"PK\x03\x04"):
        return "application/zip"
    if b"\x00" in data:
        return "application/octet-stream"
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return "application/octet-stream"
    return "text/plain"


class UnavailableScanner:
    """Safe default: absence of a configured scanner is never a clean verdict."""

    def scan(self, path: Path, declared_ext: str) -> ScanRecord:
        data = path.read_bytes()
        return ScanRecord(
            sha256=hashlib.sha256(data).hexdigest(),
            scanner="unavailable",
            engine_version=None,
            sig_version=None,
            sig_age_hours=None,
            verdict="degraded",
            detail="No document scanner is configured",
            magic_type=_magic_type(data),
            declared_extension=declared_ext or "",
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )


class IngestGate:
    def __init__(self, scanner: Scanner):
        self._scanner = scanner

    def enforce(self, path: Path, *, declared_ext: str) -> ScanRecord:
        path = Path(path)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise IngestRejected(f"cannot read document for scanning: {exc}") from exc
        digest = hashlib.sha256(data).hexdigest()
        magic = _magic_type(data)
        if magic != "text/plain":
            raise IngestRejected(
                f"unsupported or mismatched document type: {magic} ({declared_ext or 'no extension'})"
            )
        try:
            record = self._scanner.scan(path, declared_ext)
        except Exception as exc:
            raise IngestRejected(f"document scanner failed: {type(exc).__name__}") from exc
        if record.sha256.lower() != digest:
            raise IngestRejected("scanner verdict is not bound to the current document bytes")
        if record.magic_type != magic:
            raise IngestRejected("scanner MIME result does not match inspected document bytes")
        if record.verdict != "clean":
            raise IngestRejected(f"document scan did not return clean: {record.verdict}")
        return record
