from pathlib import Path

import pytest

from body_of_secrets.scouting.models import ModelCandidate, write_model_inventory


def test_model_inventory_is_written_without_overwrite(tmp_path: Path) -> None:
    target = tmp_path / "models.json"
    write_model_inventory([ModelCandidate(repo_id="org/model", tags=("text-generation",))], target)
    assert '"org/model"' in target.read_text(encoding="utf-8")
    with pytest.raises(FileExistsError):
        write_model_inventory([], target)


def test_model_query_validation() -> None:
    from body_of_secrets.scouting.models import search_models

    with pytest.raises(ValueError):
        search_models(" ")
    with pytest.raises(ValueError):
        search_models("model", limit=0)
