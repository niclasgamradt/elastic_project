# See documentation:
# docs/13_tests.md

import json
import pytest

from scripts.load_to_es import build_bulk_body


def test_build_bulk_body_uses_doc_id_and_valid_ndjson() -> None:
    target = "all-data"
    docs = [
        {"doc_id": "id-1", "provider": "x", "temperature": 1.0},
        {"doc_id": "id-2", "provider": "y", "temperature": 2.0},
    ]

    body = build_bulk_body(target, docs)

    # Must end with newline
    assert body.endswith("\n")

    lines = [ln for ln in body.splitlines() if ln.strip()]
    # For 2 docs: action+doc per entry => 4 lines
    assert len(lines) == 4

    action1 = json.loads(lines[0])
    doc1 = json.loads(lines[1])
    action2 = json.loads(lines[2])
    doc2 = json.loads(lines[3])

    assert action1 == {"index": {"_index": target, "_id": "id-1"}}
    assert doc1["doc_id"] == "id-1"

    assert action2 == {"index": {"_index": target, "_id": "id-2"}}
    assert doc2["doc_id"] == "id-2"


def test_build_bulk_body_raises_on_missing_doc_id() -> None:
    target = "all-data"
    docs = [
        {"doc_id": "id-1", "provider": "x"},
        {"provider": "missing-id"},
    ]

    with pytest.raises(ValueError):
        build_bulk_body(target, docs)
