import json
import urllib.request

from scripts.config import SETTINGS


def es_post(path: str, body: dict) -> dict:
    url = f"{SETTINGS.es_url.rstrip('/')}{path}"
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_aggregations_work_on_core_fields() -> None:
    resp = es_post(
        f"/{SETTINGS.alias_name}/_search",
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
