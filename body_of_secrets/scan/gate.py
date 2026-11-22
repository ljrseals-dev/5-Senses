"""Fail-closed document-ingest scanning primitives (no scanner dependency)."""

from __future__ import annotations

import hashlib
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .models import ScanRecord


class IngestRejected(Exception):
    """Raised when a document cannot be proven safe to index."""


class Scanner(Protocol):
    def scan(self, path: Path, declared_ext: str) -> ScanRecord: ...


def _magic_type(data: bytes) -> str:
    if not data:
        return "application/octet-stream"
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
        if scanner is None:
            raise ValueError("scanner must be configured")
        self._scanner = scanner

    def enforce(self, path: Path, *, declared_ext: str) -> tuple[ScanRecord, bytes]:
        path = Path(path)
        extension = (declared_ext or "").lower()
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise IngestRejected(f"cannot read document for scanning: {exc}") from exc
        if not data:
            raise IngestRejected("empty documents cannot be imported")
        digest = hashlib.sha256(data).hexdigest()
        magic = _magic_type(data)
        allowed_extensions = {".txt", ".md", ".rst", ".text", ".pdf"}
        if extension not in allowed_extensions:
            raise IngestRejected(f"unsupported declared extension: {extension or 'none'}")
        if extension == ".pdf" and magic != "application/pdf":
            raise IngestRejected(
                f"extension/signature mismatch: .pdf declared but detected {magic}"
            )
        if magic != "text/plain":
            raise IngestRejected(
                f"unsupported document type for text archive: {magic}"
            )
        # Scan a closed, private snapshot so scanners can reopen it on Windows too.
        try:
            with tempfile.TemporaryDirectory(prefix="5senses-scan-") as directory:
                snapshot = Path(directory) / ("document" + (extension or ".txt"))
                snapshot.write_bytes(data)
                record = self._scanner.scan(snapshot, extension)
                if hashlib.sha256(snapshot.read_bytes()).hexdigest() != digest:
                    raise IngestRejected("scanner modified the document snapshot")
        except IngestRejected:
            raise
        except Exception as exc:
            raise IngestRejected(f"document scanner failed: {type(exc).__name__}") from exc
        if not isinstance(record, ScanRecord):
            raise IngestRejected("scanner returned an invalid scan record")
        if record.sha256.lower() != digest:
            raise IngestRejected("scanner verdict is not bound to the current document bytes")
        if record.magic_type != magic:
            raise IngestRejected("scanner MIME result does not match inspected document bytes")
        if record.declared_extension.lower() != extension:
            raise IngestRejected("scanner extension result does not match the declared extension")
        if (
            record.verdict == "clean"
            and (
                not record.engine_version
                or not record.sig_version
                or record.sig_age_hours is None
                or record.scanner == "unavailable"
            )
        ):
            raise IngestRejected("scanner cannot substantiate a clean verdict")
        if record.verdict != "clean":
            raise IngestRejected(f"document scan did not return clean: {record.verdict}")
        return record, data
