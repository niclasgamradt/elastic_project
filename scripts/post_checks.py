# See documentation:
# docs/pipeline.md

import json
import urllib.request
from typing import Any, Dict, List

from scripts.config import SETTINGS


def http_get(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_post(url: str, body: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    es = SETTINGS.es_url.rstrip("/")
    target = SETTINGS.alias_name  # all-data

    health = http_get(f"{es}/_cluster/health")
    count = http_get(f"{es}/{target}/_count")

    print("cluster:", {"status": health.get("status"), "number_of_nodes": health.get("number_of_nodes")})
    print("count:", count.get("count"))

    # Query: letzte 5 nach timestamp
    q_last = {
        "size": 5,
        "sort": [{"timestamp": {"order": "desc"}}],
        "_source": ["doc_id", "source", "title", "timestamp", "url"],
        "query": {"match_all": {}},
    }
    res_last = http_post(f"{es}/{target}/_search", q_last)
    hits = res_last.get("hits", {}).get("hits", [])
    docs: List[Dict[str, Any]] = [h.get("_source", {}) for h in hits]
    print("last_docs:", docs)

    # Aggregation: Anzahl pro source
    q_agg = {
        "size": 0,
        "aggs": {"by_source": {"terms": {"field": "source", "size": 10}}},
    }
    res_agg = http_post(f"{es}/{target}/_search", q_agg)
    buckets = res_agg.get("aggregations", {}).get("by_source", {}).get("buckets", [])
    print("agg_by_source:", buckets)


if __name__ == "__main__":
    main()
