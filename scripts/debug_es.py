import json
import urllib.request
from typing import Any, Dict

from scripts.config import SETTINGS


def http_get(url: str) -> Dict[str, Any]:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_text(url: str) -> str:
    with urllib.request.urlopen(url, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main() -> None:
    es = SETTINGS.es_url.rstrip("/")
    alias = SETTINGS.alias_name
    idx_main = SETTINGS.index_name

    print("ES:", es)
    print("alias_name:", alias)
    print("index_name:", idx_main)

    # Alias check
    try:
        print("\nALIASES (cat):")
        print(http_get_text(f"{es}/_cat/aliases?v"))
    except Exception as e:
        print("alias cat failed:", e)

    # Indices check
    try:
        print("\nINDICES (cat):")
        print(http_get_text(f"{es}/_cat/indices?v"))
    except Exception as e:
        print("indices cat failed:", e)

    # Counts
    def safe_count(target: str) -> None:
        try:
            c = http_get(f"{es}/{target}/_count").get("count")
            print(f"count[{target}]:", c)
        except Exception as e:
            print(f"count[{target}] failed:", e)

    print("\nCOUNTS:")
    safe_count(alias)
    safe_count(idx_main)
    safe_count("data-archive")

    # Sample docs from main index
    try:
        q = {"size": 3, "_source": ["doc_id", "source", "title", "timestamp", "url"], "query": {"match_all": {}}}
        req = urllib.request.Request(
            f"{es}/{idx_main}/_search",
            data=json.dumps(q).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            res = json.loads(resp.read().decode("utf-8"))
        hits = [h.get("_source") for h in res.get("hits", {}).get("hits", [])]
        print("\nSAMPLE DOCS:", hits)
    except Exception as e:
        print("\nSAMPLE DOCS failed:", e)


if __name__ == "__main__":
    main()
