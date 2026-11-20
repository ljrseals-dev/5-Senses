from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from body_of_secrets.scouting.cleaning import (
    EMOCRRanker,
    clean_directory,
    clean_file,
    normalize_layout,
)


def test_layout_normalization_is_content_conservative() -> None:
    raw = "Cafe\u0301\r\n\r\n\r\n  text   here\x00\r\n"
    cleaned = normalize_layout(raw)
    assert cleaned == "Café\n\n text here\n"
    assert "here" in cleaned


def test_clean_file_preserves_raw_and_writes_hashes(tmp_path: Path) -> None:
    source = tmp_path / "raw.txt"
    destination = tmp_path / "clean" / "raw.txt"
    review = tmp_path / "review" / "raw.jsonl"
    raw = "A   line\r\n"
    source.write_text(raw, encoding="utf-8")

    result = clean_file(source, destination, review_path=review)

    assert source.read_text(encoding="utf-8") == raw
    assert result.raw_sha256 == hashlib.sha256(raw.encode()).hexdigest()
    assert destination.read_text(encoding="utf-8") == "A line\n"
    assert review.exists()
    with pytest.raises(FileExistsError):
        clean_file(source, destination)


def test_em_ranker_proposes_only_observed_vocabulary_candidates() -> None:
    ranker = EMOCRRanker().fit(
        ["modern modern modern modern modern modern modern rnodern"]
    )
    proposals = ranker.propose("rnodern")
    assert proposals
    assert proposals[0].candidate == "modern"
    assert proposals[0].action == "REVIEW"
    opted_in = ranker.propose("rnodern", auto_accept=True)
    assert opted_in[0].action == "AUTO_ACCEPT"


def test_em_ranker_does_not_rewrite_more_common_valid_word() -> None:
    ranker = EMOCRRanker().fit(
        ["modern modern modern modern modern modern modern rnodern"]
    )
    proposals = ranker.propose("modern")
    assert proposals == []


def test_em_ranker_does_not_auto_rewrite_capitalized_tokens() -> None:
    ranker = EMOCRRanker().fit(
        ["modern modern modern modern modern modern modern rnodern"]
    )
    proposals = ranker.propose("Rnodern")
    assert proposals
    assert proposals[0].action == "REVIEW"


def test_clean_directory_mirrors_tree_and_leaves_raw_untouched(tmp_path: Path) -> None:
    source = tmp_path / "incoming"
    (source / "vol1").mkdir(parents=True)
    raw = source / "vol1" / "page.txt"
    raw.write_text("modern modern modern modern modern modern modern rnodern\n")
    output = tmp_path / "cleaned"

    results = clean_directory(source, output, apply_em_corrections=True)

    assert len(results) == 1
    assert raw.exists()
    assert "rnodern" not in (output / "vol1" / "page.txt").read_text()
    assert (output / "vol1" / "page.txt").exists()
    assert (output / "cleaning_manifest.json").exists()


def test_clean_directory_rejects_oversized_input_before_writing(tmp_path: Path) -> None:
    source = tmp_path / "incoming"
    source.mkdir()
    (source / "large.txt").write_text("123456")
    output = tmp_path / "cleaned"

    with pytest.raises(ValueError, match="max_file_bytes"):
        clean_directory(source, output, max_file_bytes=3)
    assert not output.exists()


def test_em_is_review_only_by_default(tmp_path: Path) -> None:
    source = tmp_path / "incoming"
    source.mkdir()
    raw = source / "page.txt"
    raw.write_text("modern modern modern modern modern modern modern rnodern\n")
    output = tmp_path / "cleaned"
    review = tmp_path / "review"

    clean_directory(source, output, review_dir=review)

    assert "rnodern" in (output / "page.txt").read_text()
    review_text = (review / "page.txt.review.jsonl").read_text()
    assert '"action": "REVIEW"' in review_text
