"""Controlled import of acquired text assets into the BODY OF SECRETS archive."""
from __future__ import annotations

from pathlib import Path

from body_of_secrets.archive import Archive

TEXT_EXTENSIONS = {".txt", ".md", ".rst", ".text"}


def import_text_collection(
    source_dir: str | Path,
    archive: Archive,
    *,
    max_file_bytes: int = 25 * 1024 * 1024,
) -> dict[str, list[str]]:
    """Import UTF-8 text files, skipping known sources and oversized files.

    This function does not extract archives, perform OCR, or import binaries.
    Existing archive sources are skipped to avoid replacing previously indexed content.
    """
    root = Path(source_dir).resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)
    if max_file_bytes <= 0:
        raise ValueError("max_file_bytes must be positive")
    existing_sources = {doc.source for doc in archive.list_documents()}
    report: dict[str, list[str]] = {"imported": [], "skipped_existing": [],
                                  "skipped_oversize": [], "failed": []}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        resolved = path.resolve()
        if not resolved.is_relative_to(root):
            report["failed"].append(str(path))
            continue
        source = str(resolved)
        if source in existing_sources:
            report["skipped_existing"].append(source)
            continue
        if resolved.stat().st_size > max_file_bytes:
            report["skipped_oversize"].append(source)
            continue
        try:
            archive.import_text_file(resolved, source=source)
        except (OSError, UnicodeError):
            report["failed"].append(source)
        else:
            report["imported"].append(source)
            existing_sources.add(source)
    return report
