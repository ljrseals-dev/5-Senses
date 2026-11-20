from pathlib import Path

import pytest

from body_of_secrets.scouting.integrity import (
    build_manifest, verify_manifest, write_manifest,
)


def test_manifest_detects_modified_file(tmp_path: Path) -> None:
    source = tmp_path / "source.txt"
    source.write_text("original", encoding="utf-8")
    manifest = build_manifest([source], tmp_path)
    manifest_path = write_manifest(manifest, tmp_path / "manifest.json")
    assert verify_manifest(manifest_path, tmp_path)[0]["status"] == "ok"
    source.write_text("changed", encoding="utf-8")
    assert verify_manifest(manifest_path, tmp_path)[0]["status"] == "size_mismatch"


def test_manifest_rejects_path_escape(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        '{"schema_version":1,"algorithm":"sha256","files":[{"path":"../secret","size_bytes":1,"sha256":"x"}]}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError):
        verify_manifest(manifest_path, tmp_path)
