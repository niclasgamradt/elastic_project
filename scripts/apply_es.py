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
from typing import Any, Dict, List, Tuple

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


def current_alias_indices(es_base: str, alias: str) -> List[str]:
    """
    Returns a list of index names currently associated with the given alias.
    If alias does not exist -> [].
    """
    st, out = http_request("GET", f"{es_base}/_alias/{alias}", None)
    if st == 404:
        return []
    if st >= 300:
        raise RuntimeError(f"Failed to read alias {alias}: status={st}, body={out}")
    return list(out.keys())


def apply_aliases_idempotent(es_base: str, aliases_payload: Dict[str, Any]) -> None:
    """
    Makes alias application idempotent by removing the alias from all currently linked indices first,
    then applying the actions from aliases.json.
    """
    actions = aliases_payload.get("actions", [])
    if not isinstance(actions, list) or not actions:
        raise ValueError("aliases.json must contain a non-empty 'actions' array")

    # Determine alias name(s) used in the add-actions. (We assume all actions refer to the same alias.)
    alias_names = []
    for a in actions:
        add = a.get("add")
        if isinstance(add, dict) and "alias" in add:
            alias_names.append(add["alias"])

    alias_names = sorted(set(alias_names))
    if not alias_names:
        raise ValueError("aliases.json contains no add-actions with an 'alias' field")

    if len(alias_names) > 1:
        # Still supported, we just handle all found aliases.
        pass

    final_actions: List[Dict[str, Any]] = []

    # Remove aliases from existing indices to avoid conflicts (idempotent)
    for alias in alias_names:
        for idx in current_alias_indices(es_base, alias):
            final_actions.append({"remove": {"index": idx, "alias": alias}})

    # Add desired alias configuration
    final_actions.extend(actions)

    st, out = http_request("POST", f"{es_base}/_aliases", {"actions": final_actions})
    print("aliases:", st, out.get("acknowledged", out))


def main() -> None:
    es = SETTINGS.es_url.rstrip("/")

    # 1) Apply index template
    template = load_json(BASE / "index-template.json")
    st, out = http_request("PUT", f"{es}/_index_template/{TEMPLATE_NAME}", template)
    print("template:", st, out.get("acknowledged", out))

    # 2) Apply ingest pipeline (optional)
    pipeline_path = BASE / "ingest-pipeline.json"
    if pipeline_path.exists():
        pipeline = load_json(pipeline_path)
        st, out = http_request("PUT", f"{es}/_ingest/pipeline/{PIPELINE_NAME}", pipeline)
        print("pipeline:", st, out.get("acknowledged", out))
    else:
        print("pipeline: skipped (no db/elastic/ingest-pipeline.json)")

    # 3) Create indices (write index from config + archive)
    indices = [SETTINGS.index_name, "weather-archive"]
    for index in indices:
        st, out = http_request("PUT", f"{es}/{index}", {})
        print(f"index {index}:", st, out.get("error", "ok"))

    # 4) Configure aliases (idempotent)
    aliases_payload = load_json(BASE / "aliases.json")
    apply_aliases_idempotent(es, aliases_payload)

    # 5) Mini health check
    st, out = http_request("GET", f"{es}/_cluster/health", None)
    print("health:", st, {k: out.get(k) for k in ["status", "number_of_nodes", "active_shards"]})


if __name__ == "__main__":
    main()
