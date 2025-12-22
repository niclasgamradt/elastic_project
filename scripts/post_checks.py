import json
import urllib.request

from scripts.config import SETTINGS


def http_get(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main() -> None:
    health = http_get(f"{SETTINGS.es_url}/_cluster/health")
    count = http_get(f"{SETTINGS.es_url}/{SETTINGS.alias_name}/_count")

    print("cluster:", {"status": health.get("status"), "number_of_nodes": health.get("number_of_nodes")})
    print("count:", count.get("count"))


if __name__ == "__main__":
    main()
