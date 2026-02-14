# See documentation:
# docs/13_tests.md

import json

from scripts.load_to_es import parse_bulk_response


def test_parse_bulk_response_ok_no_errors() -> None:
    resp = {
        "took": 5,
        "errors": False,
        "items": [
            {"index": {"_index": "x", "_id": "1", "status": 201}},
            {"index": {"_index": "x", "_id": "2", "status": 201}},
        ],
    }

    has_errors, first_error = parse_bulk_response(json.dumps(resp))
    assert has_errors is False
    assert first_error is None


def test_parse_bulk_response_empty_is_error() -> None:
    has_errors, first_error = parse_bulk_response("")
    assert has_errors is True
    assert first_error is not None
    assert first_error.get("reason") == "empty response"


def test_parse_bulk_response_errors_true_returns_first_item_error() -> None:
    resp = {
        "took": 5,
        "errors": True,
        "items": [
            {"index": {"_index": "x", "_id": "1", "status": 201}},
            {
                "index": {
                    "_index": "x",
                    "_id": "2",
                    "status": 400,
                    "error": {"type": "mapper_parsing_exception", "reason": "failed to parse"},
                }
            },
            {
                "index": {
                    "_index": "x",
                    "_id": "3",
                    "status": 400,
                    "error": {"type": "illegal_argument_exception", "reason": "bad"},
                }
            },
        ],
    }

    has_errors, first_error = parse_bulk_response(json.dumps(resp))
    assert has_errors is True
    assert first_error is not None
    assert first_error["type"] == "mapper_parsing_exception"


def test_parse_bulk_response_errors_true_but_no_item_error() -> None:
    resp = {
        "took": 5,
        "errors": True,
        "items": [
            {"index": {"_index": "x", "_id": "1", "status": 400}},
            {"index": {"_index": "x", "_id": "2", "status": 400}},
        ],
    }

    has_errors, first_error = parse_bulk_response(json.dumps(resp))
    assert has_errors is True
    assert first_error is not None
    assert first_error.get("reason") == "errors=true but no item error found"
