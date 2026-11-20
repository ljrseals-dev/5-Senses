from pathlib import Path

import pytest

from body_of_secrets.scouting.corpora import CorpusCandidate, write_corpus_inventory


def test_corpus_inventory_is_written_without_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "corpora.json"
    write_corpus_inventory([CorpusCandidate("internet_archive", "item-1")], target)
    assert '"item-1"' in target.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_corpus_inventory([], target)
