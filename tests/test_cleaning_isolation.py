from pathlib import Path

import pytest

from body_of_secrets.scouting import cleaning as cleaning_module
from body_of_secrets.scouting.cleaning import (
    clean_directory,
    clean_file,
    normalize_layout,
)


def test_normalize_layout_preserves_unicode_format_characters_and_boundaries():
    source = "\n  A\u200dB  \n\n\nC\n"

    assert normalize_layout(source) == "\n A\u200dB\n\nC\n"


def test_clean_file_never_overwrites_an_existing_output(tmp_path: Path):
    source = tmp_path / "raw.txt"
    destination = tmp_path / "clean" / "raw.txt"
    source.write_text("original\n", encoding="utf-8")
    destination.parent.mkdir()
    destination.write_text("do not replace\n", encoding="utf-8")

    with pytest.raises(FileExistsError):
        clean_file(source, destination)

    assert source.read_text(encoding="utf-8") == "original\n"
    assert destination.read_text(encoding="utf-8") == "do not replace\n"


def test_clean_directory_writes_real_manifest_newline_and_isolated_outputs(
    tmp_path: Path,
):
    source = tmp_path / "source"
    destination = tmp_path / "cleaned"
    review = tmp_path / "review"
    source.mkdir()
    (source / "record.txt").write_text("A\n", encoding="utf-8")

    results = clean_directory(source, destination, review_dir=review)

    assert len(results) == 1
    assert (source / "record.txt").read_text(encoding="utf-8") == "A\n"
    assert (destination / "record.txt").read_text(encoding="utf-8") == "A\n"
    manifest = (destination / "cleaning_manifest.json").read_bytes()
    assert manifest.endswith(b"\n")
    assert not manifest.endswith(b"\\n")
    assert (review / "record.txt.review.jsonl").is_file()


def test_clean_directory_rolls_back_prior_outputs_after_later_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    source = tmp_path / "source"
    destination = tmp_path / "cleaned"
    review = tmp_path / "review"
    source.mkdir()
    (source / "a.txt").write_text("first\n", encoding="utf-8")
    (source / "b.txt").write_text("second\n", encoding="utf-8")
    real_clean_file = cleaning_module.clean_file
    calls = 0

    def fail_second(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated disk failure")
        return real_clean_file(*args, **kwargs)

    monkeypatch.setattr(cleaning_module, "clean_file", fail_second)
    with pytest.raises(OSError, match="simulated disk failure"):
        clean_directory(source, destination, review_dir=review)

    assert (source / "a.txt").read_text(encoding="utf-8") == "first\n"
    assert (source / "b.txt").read_text(encoding="utf-8") == "second\n"
    assert not destination.exists()
    assert not review.exists()


def test_clean_directory_rejects_symlink_destination(tmp_path: Path):
    source = tmp_path / "source"
    actual = tmp_path / "actual"
    alias = tmp_path / "alias"
    source.mkdir()
    actual.mkdir()
    alias.symlink_to(actual, target_is_directory=True)

    with pytest.raises(ValueError, match="destination_dir must not be a symlink"):
        clean_directory(source, alias)

    assert list(actual.iterdir()) == []
