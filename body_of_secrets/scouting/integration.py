"""Controlled import of acquired text assets into the BODY OF SECRETS archive."""
from __future__ import annotations

import hashlib
import os
import stat
from pathlib import Path

from body_of_secrets.archive import Archive

TEXT_EXTENSIONS = {".txt", ".md", ".rst", ".text"}


def _read_stable_text(path: Path, *, max_file_bytes: int) -> tuple[str, str, int]:
    """Read one regular non-symlink UTF-8 file and detect concurrent mutation."""
    if path.is_symlink():
        raise ValueError(f"refusing symlink input: {path}")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"input is not a regular file: {path}")
        if before.st_size > max_file_bytes:
            raise OverflowError(f"input exceeds max_file_bytes: {path}")
        chunks = []
        total = 0
        digest = hashlib.sha256()
        while True:
            chunk = stream.read(min(1024 * 1024, max_file_bytes - total + 1))
            if not chunk:
                break
            total += len(chunk)
            if total > max_file_bytes:
                raise OverflowError(f"input exceeds max_file_bytes: {path}")
            chunks.append(chunk)
            digest.update(chunk)
        after = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ):
            raise ValueError(f"input changed while reading: {path}")
    raw = b"".join(chunks)
    return raw.decode("utf-8", errors="strict"), digest.hexdigest(), total


def import_text_collection(
    source_dir: str | Path,
    archive: Archive,
    *,
    max_file_bytes: int = 25 * 1024 * 1024,
) -> dict[str, list[str]]:
    """Import stable UTF-8 text files, skipping known sources and oversized files.

    This function does not extract archives, perform OCR, or import binaries.
    Every imported record receives a SHA-256 and byte-size provenance record.
    It does not establish license rights; callers must review rights separately.
    """
    raw_root = Path(source_dir)
    if raw_root.is_symlink():
        raise ValueError("source_dir must not be a symlink")
    root = raw_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    if (isinstance(max_file_bytes, bool) or not isinstance(max_file_bytes, int)
            or max_file_bytes < 1):
        raise ValueError("max_file_bytes must be a positive integer")
    existing_sources = {doc.source for doc in archive.list_documents()}
    report: dict[str, list[str]] = {"imported": [], "skipped_existing": [],
                                  "skipped_oversize": [], "failed": []}
    for path in sorted(root.rglob("*")):
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.is_symlink():
            report["failed"].append(str(path))
            continue
        if not path.is_file():
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            report["failed"].append(str(path))
            continue
        source = str(resolved)
        if source in existing_sources:
            report["skipped_existing"].append(source)
            continue
        try:
            content, digest, size = _read_stable_text(resolved, max_file_bytes=max_file_bytes)
        except OverflowError:
            report["skipped_oversize"].append(source)
            continue
        except (OSError, UnicodeError, ValueError):
            report["failed"].append(source)
            continue
        try:
            archive.import_document(
                title=resolved.name,
                content=content,
                source=source,
                metadata={"sha256": digest, "size_bytes": size,
                          "acquisition_method": "local_text_import"},
            )
        except (OSError, UnicodeError):
            report["failed"].append(source)
        else:
            report["imported"].append(source)
            existing_sources.add(source)
    return report
