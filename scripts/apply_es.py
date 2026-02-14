# See documentation:
# docs/09_elasticsearch_index_design.md


import json
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

from scripts.config import SETTINGS

from scripts.config import PROJECT_ROOT
BASE = PROJECT_ROOT / "db" / "elastic"

TEMPLATE_NAME = "data-template"
PIPELINE_NAME = "standardize-v1"


def http_request(method: str, url: str, body: Dict[str, Any] | None = None) -> Tuple[int, Dict[str, Any]]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, (json.loads(text) if text else {})
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8") if e.fp else ""
        try:
            payload = json.loads(text) if text else {"error": str(e)}
        except json.JSONDecodeError:
            payload = {"error": text or str(e)}
        return e.code, payload


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    es = SETTINGS.es_url.rstrip("/")

    # aplly index template
    template = load_json(BASE / "index-template.json")
    st, out = http_request("PUT", f"{es}/_index_template/{TEMPLATE_NAME}", template)
    print("template:", st, out.get("acknowledged", out))

    # apply ingest pipeline
    pipeline_path = BASE / "ingest-pipeline.json"
    if pipeline_path.exists():
        pipeline = load_json(pipeline_path)
        st, out = http_request("PUT", f"{es}/_ingest/pipeline/{PIPELINE_NAME}", pipeline)
        print("pipeline:", st, out.get("acknowledged", out))
    else:
        print("pipeline: skipped (no db/elastic/ingest-pipeline.json)")

    # 3) create indeces
    for index in ["data-2024", "data-archive"]:
        st, out = http_request("PUT", f"{es}/{index}", {})
        # 200 = created
        print(f"index {index}:", st, out.get("error", "ok"))

    # 4) configure aliases
    aliases = load_json(BASE / "aliases.json")
    st, out = http_request("POST", f"{es}/_aliases", aliases)
    print("aliases:", st, out.get("acknowledged", out))

    # 5) mini check
    st, out = http_request("GET", f"{es}/_cluster/health", None)
    print("health:", st, {k: out.get(k) for k in ["status", "number_of_nodes", "active_shards"]})


if __name__ == "__main__":
    main()
