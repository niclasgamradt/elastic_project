# See documentation:
# docs/13_tests.md

import json
import urllib.request
import urllib.error
import uuid
import pytest

from scripts.config import SETTINGS


def http_post(url: str, body: str, content_type: str) -> tuple[int, str]:
    data = body.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8") if e.fp else ""
        return e.code, text


def test_bulk_returns_error_on_type_conflict() -> None:
    es = SETTINGS.es_url.rstrip("/")
    bulk_url = f"{es}/_bulk?pipeline=standardize-v1"

    doc_id = f"bad-{uuid.uuid4()}"

    # temperature ist im Mapping float -> absichtlich falscher Typ (string)
    bad_doc = {
        "doc_id": doc_id,
        "provider": "test-provider",
        "source_id": "test-source",
        "timestamp": "2026-02-14T00:00:00Z",
        "processed_at": "2026-02-14T00:00:00Z",
        "temperature": "NOT_A_FLOAT",
    }

    action = {"index": {"_index": "all-data", "_id": doc_id}}
    body = json.dumps(action) + "\n" + json.dumps(bad_doc) + "\n"

    status, text = http_post(bulk_url, body, "application/x-ndjson")

    assert status == 200
    resp = json.loads(text)
    assert resp.get("errors") is True
