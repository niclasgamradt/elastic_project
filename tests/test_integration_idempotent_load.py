# See documentation:
# docs/13_tests.md

import json
import urllib.request
from pathlib import Path

import pytest

import scripts.load_to_es as lte
from scripts.config import SETTINGS as GLOBAL_SETTINGS, Settings


def es_get(path: str) -> dict:
    url = f"{GLOBAL_SETTINGS.es_url.rstrip('/')}{path}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def write_ndjson(path: Path, docs: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for d in docs:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def test_bulk_load_is_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    run_id = "2026-02-12"

    # Testdaten erzeugen (minimal, Kernschema)
    docs_brightsky = [
        {
            "doc_id": "ci-test-1",
            "provider": "brightsky",
            "source_id": "7307",
            "timestamp": "2026-02-12T00:00:00Z",
            "processed_at": "2026-02-12T00:00:00Z",
            "temperature": 8.3,
        },
        {
            "doc_id": "ci-test-2",
            "provider": "brightsky",
            "source_id": "7307",
            "timestamp": "2026-02-12T01:00:00Z",
            "processed_at": "2026-02-12T01:00:00Z",
            "temperature": 7.8,
        },
    ]
    docs_hs = [
        {
            "doc_id": "ci-test-3",
            "provider": "hs-worms",
            "source_id": "hs-worms",
            "timestamp": "2026-02-12T00:00:00Z",
            "processed_at": "2026-02-12T00:00:00Z",
            "temperature": 3.8,
        }
    ]

    processed_dir = tmp_path / "processed"
    write_ndjson(processed_dir / f"processed_{run_id}__brightsky.ndjson", docs_brightsky)
    write_ndjson(processed_dir / f"processed_{run_id}__hs-worms.ndjson", docs_hs)

    # SETTINGS in load_to_es auf temp processed_dir umbiegen
    test_settings = Settings(
        raw_dir=tmp_path / "raw",
        processed_dir=processed_dir,
        es_url=GLOBAL_SETTINGS.es_url,
        index_name=GLOBAL_SETTINGS.index_name,
        archive_index=GLOBAL_SETTINGS.archive_index,
        alias_name=GLOBAL_SETTINGS.alias_name,
        raw_prefix=GLOBAL_SETTINGS.raw_prefix,
        processed_prefix=GLOBAL_SETTINGS.processed_prefix,
    )
    monkeypatch.setattr(lte, "SETTINGS", test_settings)

    alias = test_settings.alias_name

    # initial count
    before = es_get(f"/{alias}/_count")["count"]

    # load twice
    lte.main(run_id=run_id)
    mid = es_get(f"/{alias}/_count")["count"]

    lte.main(run_id=run_id)
    after = es_get(f"/{alias}/_count")["count"]

    # After first load we must have +3 docs, second load must not increase (idempotent)
    assert mid == before + 3
    assert after == mid
