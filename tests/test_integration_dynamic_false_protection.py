# See documentation:
# docs/13_tests.md

import json
import urllib.request
import urllib.error
import uuid

from scripts.config import SETTINGS


def es_request(method: str, path: str, payload: dict | None = None) -> dict:
    url = SETTINGS.es_url.rstrip("/") + path
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8") if e.fp else ""
        payload = json.loads(text) if text else {"error": str(e)}
        payload["_http_status"] = e.code
        return payload


def test_dynamic_false_prevents_mapping_and_searchability() -> None:
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

    # Indexieren in den Write-Index über Alias
    idx_resp = es_request("PUT", f"/all-data/_doc/{doc_id}?refresh=true", doc)
    assert idx_resp.get("result") in {"created", "updated"}

    # 1) Mapping darf das Feld nicht enthalten
    mapping = es_request("GET", "/data-2026/_mapping")
    props = mapping["data-2026"]["mappings"]["properties"]
    assert "unknown_field_xyz" not in props

    # 2) Feld darf nicht suchbar sein (exists query muss 0 Treffer liefern)
    q = es_request(
        "POST",
        "/all-data/_search?size=0",
        {"query": {"exists": {"field": "unknown_field_xyz"}}},
    )
    assert q["hits"]["total"]["value"] == 0

    # 3) Optional: Dokument muss existieren (Abruf über physischen Index)
    get_doc = es_request("GET", f"/data-2026/_doc/{doc_id}")
    assert get_doc.get("found") is True
    assert get_doc["_source"]["doc_id"] == doc_id
