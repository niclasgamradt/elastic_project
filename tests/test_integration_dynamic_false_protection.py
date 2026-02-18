import json
import uuid
import urllib.request

from scripts.config import SETTINGS


def es_request(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{SETTINGS.es_url.rstrip('/')}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method=method, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        text = resp.read().decode("utf-8")
        return json.loads(text) if text else {}


def test_dynamic_false_prevents_mapping_and_searchability() -> None:
    alias = SETTINGS.alias_name
    index = SETTINGS.index_name

    doc_id = f"test-{uuid.uuid4()}"

    doc = {
        "doc_id": doc_id,
        "provider": "test-provider",
        "source_id": "test-source",
        "timestamp": "2026-02-14T00:00:00Z",
        "processed_at": "2026-02-14T00:00:00Z",
        "temperature": 10.0,
        "unknown_field_xyz": "SHOULD_NOT_BE_SEARCHABLE",
    }

    idx_resp = es_request("PUT", f"/{alias}/_doc/{doc_id}?refresh=true", doc)
    assert idx_resp.get("result") in {"created", "updated"}

    mapping = es_request("GET", f"/{index}/_mapping")
    props = mapping[index]["mappings"]["properties"]
    assert "unknown_field_xyz" not in props

    search = es_request(
        "POST",
        f"/{alias}/_search",
        {"query": {"term": {"unknown_field_xyz": "SHOULD_NOT_BE_SEARCHABLE"}}},
    )
    assert search["hits"]["total"]["value"] == 0
