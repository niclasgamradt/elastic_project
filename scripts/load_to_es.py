import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from scripts.config import SETTINGS

PIPELINE_NAME = "standardize-v1"
CHUNK_SIZE = 500  # bei echten Daten: 500–5000 sinnvoll


def latest_processed_file(processed_dir: Path) -> Path:
    files = sorted(processed_dir.glob("processed_*.ndjson"))
    if not files:
        raise FileNotFoundError("No processed_*.ndjson found in data/processed/")
    return files[-1]


def read_ndjson(path: Path) -> Iterable[Dict]:
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def chunked(items: Iterable[Dict], size: int) -> Iterable[List[Dict]]:
    buf: List[Dict] = []
    for x in items:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def http_request(method: str, url: str, body: Optional[str] = None, content_type: str = "application/json") -> Tuple[int, str]:
    data = None if body is None else body.encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={"Content-Type": content_type},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8") if e.fp else ""
        return e.code, text


def set_refresh_interval(index_or_alias: str, value: str) -> None:
    es = SETTINGS.es_url.rstrip("/")
    payload = json.dumps({"index": {"refresh_interval": value}})
    status, text = http_request("PUT", f"{es}/{index_or_alias}/_settings", payload)
    if status >= 300:
        raise RuntimeError(f"Failed to set refresh_interval={value}: status={status}, body={text}")


def refresh(index_or_alias: str) -> None:
    es = SETTINGS.es_url.rstrip("/")
    status, text = http_request("POST", f"{es}/{index_or_alias}/_refresh", body="")
    if status >= 300:
        raise RuntimeError(f"Failed to refresh: status={status}, body={text}")


def build_bulk_body(target: str, docs: List[Dict]) -> str:
    lines: List[str] = []
    for d in docs:
        doc_id = d.get("doc_id")
        if not doc_id:
            continue
        action = {"index": {"_index": target, "_id": doc_id}}
        lines.append(json.dumps(action, ensure_ascii=False))
        lines.append(json.dumps(d, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def parse_bulk_response(resp_text: str) -> Tuple[bool, Optional[Dict]]:
    """
    returns: (has_errors, first_error_obj)
    """
    resp = json.loads(resp_text) if resp_text else {}
    if not resp:
        return True, {"reason": "empty response"}
    if not resp.get("errors"):
        return False, None

    for it in resp.get("items", []):
        r = it.get("index") or {}
        if "error" in r:
            return True, r["error"]
    return True, {"reason": "errors=true but no item error found"}


def main() -> None:
    es = SETTINGS.es_url.rstrip("/")

    # Empfehlung: in Alias laden (wenn Alias als write_index gesetzt ist).
    # Fallback: direkt in Index.
    target = SETTINGS.alias_name or SETTINGS.index_name

    in_file = latest_processed_file(SETTINGS.processed_dir)
    docs_iter = read_ndjson(in_file)

    # Bulk URL + Pipeline
    bulk_url = f"{es}/_bulk?pipeline={PIPELINE_NAME}"

    print(f"Input:  {in_file}")
    print(f"Target: {target}")
    print(f"Chunk:  {CHUNK_SIZE}")
    print(f"Bulk:   {bulk_url}")

    # Optionales Tuning: refresh_interval während Bulk hochsetzen/disable
    # Für kleine Tests können Sie das auskommentiert lassen.
    set_refresh_interval(target, "-1")

    total_actions = 0
    try:
        for part in chunked(docs_iter, CHUNK_SIZE):
            body = build_bulk_body(target, part)
            status, text = http_request("POST", bulk_url, body, content_type="application/x-ndjson")

            if status >= 300:
                raise RuntimeError(f"Bulk HTTP error: status={status}, body={text}")

            has_errors, first_error = parse_bulk_response(text)
            if has_errors:
                raise RuntimeError(f"Bulk item error: {first_error}")

            # Elasticsearch gibt pro Doc 1 action zurück
            items = json.loads(text).get("items", [])
            total_actions += len(items)
            print(f"Bulk ok: {len(items)} actions (total {total_actions})")

    finally:
        # refresh_interval wieder normal setzen + refresh erzwingen
        set_refresh_interval(target, "1s")
        refresh(target)

    print(f"Done. Total indexed actions: {total_actions}")


if __name__ == "__main__":
    main()
