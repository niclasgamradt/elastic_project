# See documentation:
# docs/13_tests.md

from pathlib import Path

import pytest

from scripts.load_to_es import processed_files_for_run


def test_processed_files_for_run_matches_run_id(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    # andere runs (dürfen nicht gematcht werden)
    (processed_dir / "processed_2026-02-11__brightsky.ndjson").write_text("x\n", encoding="utf-8")
    (processed_dir / "processed_2026-02-13__hs-worms.ndjson").write_text("x\n", encoding="utf-8")

    # ziel-run
    f1 = processed_dir / "processed_2026-02-12__brightsky.ndjson"
    f2 = processed_dir / "processed_2026-02-12__hs-worms.ndjson"
    f1.write_text("x\n", encoding="utf-8")
    f2.write_text("x\n", encoding="utf-8")

    files = processed_files_for_run(processed_dir, "2026-02-12")

    assert files == sorted([f1, f2])


def test_processed_files_for_run_raises_if_missing(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    with pytest.raises(FileNotFoundError):
        processed_files_for_run(processed_dir, "2026-02-12")


def test_processed_files_for_run_fallback_latest_without_run_id(tmp_path: Path) -> None:
    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    old = processed_dir / "processed_2026-02-10__brightsky.ndjson"
    new = processed_dir / "processed_2026-02-12__brightsky.ndjson"
    old.write_text("x\n", encoding="utf-8")
    new.write_text("x\n", encoding="utf-8")

    files = processed_files_for_run(processed_dir, None)

    assert files == [new]
