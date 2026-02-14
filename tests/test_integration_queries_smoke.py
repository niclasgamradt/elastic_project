# See documentation:
# docs/13_tests.md

import json
import urllib.request

from scripts.config import SETTINGS


def es_post(path: str, payload: dict) -> dict:
    url = SETTINGS.es_url.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_aggregations_work_on_core_fields() -> None:
    resp = es_post(
        "/all-data/_search",
        {
            "size": 0,
            "aggs": {
                "by_provider": {"terms": {"field": "provider"}},
                "avg_temp": {"avg": {"field": "temperature"}},
            },
        },
    )

    assert "aggregations" in resp
    assert "by_provider" in resp["aggregations"]
    assert "avg_temp" in resp["aggregations"]

    buckets = resp["aggregations"]["by_provider"]["buckets"]
    assert isinstance(buckets, list)
    assert len(buckets) >= 1

    # avg_temp kann None sein, wenn ein provider keine temperature hat,
    # aber der Aggregation-Block muss existieren.
    assert "value" in resp["aggregations"]["avg_temp"]
