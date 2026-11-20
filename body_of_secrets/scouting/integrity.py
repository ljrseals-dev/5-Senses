"""Integrity manifests and lossless compression for acquired text assets."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(paths: Iterable[str | Path], root: str | Path) -> dict:
    """Describe files relative to root with size and SHA-256; no files are changed."""
    base = Path(root).resolve()
    entries = []
    for raw in sorted((Path(p) for p in paths), key=lambda p: str(p)):
        path = raw.resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            relative = path.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"file is outside manifest root: {path}") from exc
        entries.append({"path": relative.as_posix(), "size_bytes": path.stat().st_size,
                        "sha256": sha256_file(path)})
    return {"schema_version": 1, "algorithm": "sha256", "files": entries}


def write_manifest(manifest: dict, destination: str | Path) -> Path:
    target = Path(destination)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        raise FileExistsError(target)
    target.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return target


def verify_manifest(manifest_path: str | Path, root: str | Path) -> list[dict[str, str]]:
    """Return per-file verification results; never repairs or overwrites source files."""
    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    if manifest.get("schema_version") != 1 or manifest.get("algorithm") != "sha256":
        raise ValueError("unsupported manifest schema or digest algorithm")
    base = Path(root).resolve()
    results = []
    for entry in manifest.get("files", []):
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError(f"unsafe manifest path: {relative}")
        path = (base / relative).resolve()
        if not path.is_relative_to(base):
            raise ValueError(f"manifest path escapes root: {relative}")
        if not path.is_file():
            status = "missing"
        elif path.stat().st_size != entry["size_bytes"]:
            status = "size_mismatch"
        elif sha256_file(path) != entry["sha256"]:
            status = "hash_mismatch"
        else:
            status = "ok"
        results.append({"path": relative.as_posix(), "status": status})
    return results


def compress_zstd(source: str | Path, destination: str | Path, *, level: int = 9) -> Path:
    """Create a Zstandard copy; original is preserved and existing targets are refused."""
    src, dst = Path(source), Path(destination)
    if not src.is_file():
        raise FileNotFoundError(src)
    if dst.exists():
        raise FileExistsError(dst)
    if not 1 <= level <= 22:
        raise ValueError("zstd level must be between 1 and 22")
    try:
        import zstandard
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install zstandard") from exc
    dst.parent.mkdir(parents=True, exist_ok=True)
    with src.open("rb") as input_stream, dst.open("xb") as output_stream:
        zstandard.ZstdCompressor(level=level).copy_stream(input_stream, output_stream)
    return dst
