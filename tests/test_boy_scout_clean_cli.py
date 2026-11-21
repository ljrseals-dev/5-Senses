from pathlib import Path

from body_of_secrets.interface.cli import main


def test_clean_cli_creates_separate_output_and_manifest(tmp_path: Path) -> None:
    source = tmp_path / "raw"
    source.mkdir()
    (source / "page.txt").write_text("A clean line.\n", encoding="utf-8")
    output = tmp_path / "cleaned"

    assert main(["clean", str(source), str(output)]) == 0
    assert (source / "page.txt").exists()
    assert (output / "page.txt").exists()
    assert (output / "cleaning_manifest.json").exists()
