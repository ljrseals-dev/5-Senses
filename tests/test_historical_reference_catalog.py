import json
from pathlib import Path


def test_historical_reference_catalog_is_structured_and_honest() -> None:
    root = Path(__file__).resolve().parents[1]
    catalog = json.loads(
        (root / "data" / "inventory" / "historical_reference_works.json").read_text(
            encoding="utf-8"
        )
    )
    works = catalog["works"]
    ids = [work["id"] for work in works]
    assert len(ids) == len(set(ids))
    assert len(works) >= 6
    assert all(work["acquisition_status"] == "NOT_DOWNLOADED" for work in works)
    assert all(work["candidate_sources"] for work in works)
