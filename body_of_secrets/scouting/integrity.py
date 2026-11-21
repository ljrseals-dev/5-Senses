"""Integrity manifests and lossless compression for acquired text assets."""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Iterable
from pathlib import Path, PurePosixPath


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _validate_chunk_size(chunk_size: int) -> None:
    if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer")


def _hash_stable_file(path: Path, *, chunk_size: int = 1024 * 1024) -> tuple[str, int]:
    _validate_chunk_size(chunk_size)
    if path.is_symlink():
        raise ValueError(f"refusing symlink file: {path}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"not a regular file: {path}")
        digest = hashlib.sha256()
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
        after = os.fstat(stream.fileno())
        if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
            after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns
        ):
            raise ValueError(f"file changed while hashing: {path}")
        return digest.hexdigest(), after.st_size


def sha256_file(path: str | Path, *, chunk_size: int = 1024 * 1024) -> str:
    """Hash one regular, non-symlink file; reject invalid chunk sizes and races."""
    digest, _ = _hash_stable_file(Path(path), chunk_size=chunk_size)
    return digest


def build_manifest(paths: Iterable[str | Path], root: str | Path) -> dict:
    """Describe unique regular files relative to root with stable size and SHA-256."""
    raw_root = Path(root)
    if raw_root.is_symlink():
        raise ValueError("manifest root must not be a symlink")
    base = raw_root.resolve()
    if not base.is_dir():
        raise NotADirectoryError(base)
    entries = []
    seen: set[str] = set()
    for raw in sorted((Path(p) for p in paths), key=lambda p: str(p)):
        if raw.is_symlink():
            raise ValueError(f"manifest input must not be a symlink: {raw}")
        path = raw.resolve()
        if not path.is_file():
            raise FileNotFoundError(path)
        try:
            relative = path.relative_to(base)
        except ValueError as exc:
            raise ValueError(f"file is outside manifest root: {path}") from exc
        key = relative.as_posix()
        if key in seen:
            raise ValueError(f"duplicate manifest path: {key}")
        seen.add(key)
        digest, size = _hash_stable_file(path)
        entries.append({"path": key, "size_bytes": size, "sha256": digest})
    return {"schema_version": 1, "algorithm": "sha256", "files": entries}


def write_manifest(manifest: dict, destination: str | Path) -> Path:
    """Create a manifest exclusively; remove a partial file if serialization fails."""
    target = Path(destination)
    if target.is_symlink():
        raise ValueError(f"manifest destination must not be a symlink: {target}")
    target.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with target.open("x", encoding="utf-8", newline="") as stream:
            created = True
            json.dump(manifest, stream, indent=2, ensure_ascii=False, allow_nan=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        if created:
            try:
                target.unlink()
            except OSError:
                pass
        raise
    return target


def verify_manifest(manifest_path: str | Path, root: str | Path) -> list[dict[str, str]]:
    """Validate manifest shape and verify files without following symlinks or repairing."""
    manifest_file = Path(manifest_path)
    if manifest_file.is_symlink():
        raise ValueError("manifest file must not be a symlink")
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("schema_version") != 1 or manifest.get("algorithm") != "sha256":
        raise ValueError("unsupported manifest schema or digest algorithm")
    entries = manifest.get("files")
    if not isinstance(entries, list):
        raise TypeError("manifest files must be a list")
    raw_root = Path(root)
    if raw_root.is_symlink():
        raise ValueError("verification root must not be a symlink")
    base = raw_root.resolve()
    if not base.is_dir():
        raise NotADirectoryError(base)
    results = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise TypeError(f"manifest entry {index} must be an object")
        name, size, expected = entry.get("path"), entry.get("size_bytes"), entry.get("sha256")
        if not isinstance(name, str) or not name or "\x00" in name or "\\" in name:
            raise ValueError(f"manifest entry {index} has an invalid path")
        relative = PurePosixPath(name)
        if (relative.is_absolute() or not relative.parts or relative.as_posix() != name
                or any(part in {"", ".", ".."} for part in relative.parts)):
            raise ValueError(f"unsafe manifest path: {name}")
        normalized = relative.as_posix()
        if normalized in seen:
            raise ValueError(f"duplicate manifest path: {normalized}")
        seen.add(normalized)
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError(f"invalid size_bytes for {name}")
        if not isinstance(expected, str) or not _SHA256_RE.fullmatch(expected):
            raise ValueError(f"invalid SHA-256 for {name}")
        candidate = base
        for part in relative.parts:
            candidate = candidate / part
            if candidate.is_symlink():
                raise ValueError(f"manifest path traverses a symlink: {name}")
        path = candidate.resolve()
        if not path.is_relative_to(base):
            raise ValueError(f"manifest path escapes root: {name}")
        if not path.is_file():
            status = "missing"
        else:
            actual, actual_size = _hash_stable_file(path)
            if actual_size != size:
                status = "size_mismatch"
            elif actual != expected:
                status = "hash_mismatch"
            else:
                status = "ok"
        results.append({"path": normalized, "status": status})
    return results


def compress_zstd(source: str | Path, destination: str | Path, *, level: int = 9) -> Path:
    """Create a Zstandard copy; preserve source and clean partial output on failure."""
    src, dst = Path(source), Path(destination)
    if src.is_symlink() or not src.is_file():
        raise ValueError(f"source must be a regular, non-symlink file: {src}")
    if dst.is_symlink() or dst.exists():
        raise FileExistsError(dst)
    if isinstance(level, bool) or not isinstance(level, int) or not 1 <= level <= 22:
        raise ValueError("zstd level must be an integer between 1 and 22")
    try:
        import zstandard
    except ImportError as exc:
        raise RuntimeError("Install optional dependency: pip install zstandard") from exc
    dst.parent.mkdir(parents=True, exist_ok=True)
    created = False
    try:
        with src.open("rb") as input_stream, dst.open("xb") as output_stream:
            created = True
            zstandard.ZstdCompressor(level=level).copy_stream(input_stream, output_stream)
            output_stream.flush()
            os.fsync(output_stream.fileno())
    except Exception:
        if created:
            try:
                dst.unlink()
            except OSError:
                pass
        raise
    return dst
