# See documentation:
# docs/13_tests.md

import json
import urllib.request

from scripts.load_to_es import main as load_main
from scripts.config import SETTINGS


def es_get(path: str) -> dict:
    url = SETTINGS.es_url.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_bulk_load_is_idempotent() -> None:
    run_id = "2026-02-12"

    # initial count
    before = es_get("/all-data/_count")["count"]

    # load once
    load_main(run_id)
    after_first = es_get("/all-data/_count")["count"]

    # load same run again
    load_main(run_id)
    after_second = es_get("/all-data/_count")["count"]

    # first load may increase count (wenn Index leer war)
    assert after_first >= before

    # second load must NOT increase count
    assert after_second == after_first
