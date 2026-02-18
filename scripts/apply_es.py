# ------------------------------------------------------------
# Elasticsearch setup script
#
# Loads and applies:
# - Index Template  (db/elastic/index-template.json)
# - Ingest Pipeline (db/elastic/ingest-pipeline.json)
# - Alias config    (db/elastic/aliases.json)
#
# Documentation:
# docs/09_elasticsearch_index_design.md
# ------------------------------------------------------------

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Any, Dict, Tuple

from scripts.config import SETTINGS, PROJECT_ROOT

BASE = PROJECT_ROOT / "db" / "elastic"

TEMPLATE_NAME = "weather-template"
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


def replace_placeholders(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: replace_placeholders(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [replace_placeholders(v) for v in obj]
    if isinstance(obj, str):
        return (
            obj.replace("__WRITE_INDEX__", SETTINGS.index_name)
               .replace("__ARCHIVE_INDEX__", SETTINGS.archive_index)
               .replace("__ALIAS__", SETTINGS.alias_name)
        )
    return obj


def main() -> None:
    es = SETTINGS.es_url.rstrip("/")

    # 1) Apply index template
    template = load_json(BASE / "index-template.json")
    st, out = http_request("PUT", f"{es}/_index_template/{TEMPLATE_NAME}", template)
    if st >= 300:
        raise RuntimeError(f"Template failed: status={st}, body={out}")
    print("template:", st, out.get("acknowledged", out))

    # 2) Apply ingest pipeline (optional)
    pipeline_path = BASE / "ingest-pipeline.json"
    if pipeline_path.exists():
        pipeline = load_json(pipeline_path)
        st, out = http_request("PUT", f"{es}/_ingest/pipeline/{PIPELINE_NAME}", pipeline)
        if st >= 300:
            raise RuntimeError(f"Pipeline failed: status={st}, body={out}")
        print("pipeline:", st, out.get("acknowledged", out))
    else:
        print("pipeline: skipped (no db/elastic/ingest-pipeline.json)")

    # 3) Create indices (write + archive)
    for index in [SETTINGS.index_name, SETTINGS.archive_index]:
        st, out = http_request("PUT", f"{es}/{index}", {})
        # 200 created, 400 already exists (acceptable)
        if st == 400 and out.get("error", {}).get("type") == "resource_already_exists_exception":
            print(f"index {index}: 400 already exists (ok)")
        elif st >= 300:
            raise RuntimeError(f"Index create failed for {index}: status={st}, body={out}")
        else:
            print(f"index {index}:", st, "ok")

    # 4) Configure alias
    aliases = load_json(BASE / "aliases.json")
    aliases = replace_placeholders(aliases)
    st, out = http_request("POST", f"{es}/_aliases", aliases)
    if st >= 300:
        raise RuntimeError(f"Aliases failed: status={st}, body={out}")
    print("aliases:", st, out.get("acknowledged", out))

    # 5) Mini health check
    st, out = http_request("GET", f"{es}/_cluster/health", None)
    print("health:", st, {k: out.get(k) for k in ["status", "number_of_nodes", "active_shards"]})


if __name__ == "__main__":
    main()
