# See documentation:
# docs/pipeline.md

import json
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from scripts.config import SETTINGS

PIPELINE_NAME = "standardize-v1"
CHUNK_SIZE = 500


def processed_files_for_run(processed_dir: Path, run_id: str | None) -> List[Path]:
    """
    Load all processed files for a specific Airflow run.

    Naming convention:
        processed_<run_id>__<provider>.ndjson

    Fallback (without run_id):
        Loads only the most recent processed_*.ndjson file.
    """
    if not run_id:
        files = sorted(processed_dir.glob("processed_*.ndjson"))
        if not files:
            raise FileNotFoundError("No processed_*.ndjson found in data/processed/")
        return [files[-1]]

    pattern = f"processed_{run_id}__*.ndjson"
    files = sorted(processed_dir.glob(pattern))
    if not files:
        raise FileNotFoundError(f"No {pattern} found in {processed_dir}")
    return files


def read_ndjson(path: Path) -> Iterable[Dict]:
    """Stream NDJSON file line by line."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def chunked(items: Iterable[Dict], size: int) -> Iterable[List[Dict]]:
    """Split iterable into chunks of defined size."""
    buf: List[Dict] = []
    for x in items:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


def http_request(method: str, url: str, body: Optional[str] = None, content_type: str = "application/json") -> Tuple[int, str]:
    """Generic HTTP request helper for Elasticsearch communication."""
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
    """
    Temporarily adjust refresh_interval for bulk performance optimization.
    """
    es = SETTINGS.es_url.rstrip("/")
    payload = json.dumps({"index": {"refresh_interval": value}})
    status, text = http_request("PUT", f"{es}/{index_or_alias}/_settings", payload)
    if status >= 300:
        raise RuntimeError(f"Failed to set refresh_interval={value}: status={status}, body={text}")


def refresh(index_or_alias: str) -> None:
    """Force index refresh after bulk ingestion."""
    es = SETTINGS.es_url.rstrip("/")
    status, text = http_request("POST", f"{es}/{index_or_alias}/_refresh", body="")
    if status >= 300:
        raise RuntimeError(f"Failed to refresh: status={status}, body={text}")


def build_bulk_body(target: str, docs: List[Dict]) -> str:
    """
    Build NDJSON bulk request body.

    Fails if a document has no doc_id (no silent drops).
    """
    lines: List[str] = []

    for d in docs:
        doc_id = d.get("doc_id")
        if not doc_id:
            raise ValueError(f"Missing doc_id in document: {d}")

        action = {"index": {"_index": target, "_id": doc_id}}
        lines.append(json.dumps(action, ensure_ascii=False))
        lines.append(json.dumps(d, ensure_ascii=False))

    return "\n".join(lines) + "\n"



def parse_bulk_response(resp_text: str) -> Tuple[bool, Optional[Dict]]:
    """
    Analyze Elasticsearch bulk response.

    Returns:
        (has_errors, first_error_object)
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


def main(run_id: str | None = None) -> None:
    """
    Load processed NDJSON files into Elasticsearch using the Bulk API.

    Supports multi-source ingestion per Airflow run.
    """
    es = SETTINGS.es_url.rstrip("/")

    # Prefer writing to alias (if configured as write_index)
    target = SETTINGS.alias_name or SETTINGS.index_name

    in_files = processed_files_for_run(SETTINGS.processed_dir, run_id)

    bulk_url = f"{es}/_bulk?pipeline={PIPELINE_NAME}"

    print("Inputs:")
    for f in in_files:
        print(" -", f)
    print(f"Target: {target}")
    print(f"Chunk:  {CHUNK_SIZE}")
    print(f"Bulk:   {bulk_url}")

    total_actions = 0

    # Disable refresh during bulk indexing for performance
    set_refresh_interval(target, "-1")

    try:
        for in_file in in_files:
            docs_iter = read_ndjson(in_file)

            for part in chunked(docs_iter, CHUNK_SIZE):
                body = build_bulk_body(target, part)
                status, text = http_request(
                    "POST",
                    bulk_url,
                    body,
                    content_type="application/x-ndjson"
                )

                if status >= 300:
                    raise RuntimeError(f"Bulk HTTP error: status={status}, body={text}")

                has_errors, first_error = parse_bulk_response(text)
                if has_errors:
                    raise RuntimeError(f"Bulk item error: {first_error}")

                items = json.loads(text).get("items", [])
                total_actions += len(items)

                if len(items) != len(part):
                    raise RuntimeError(
                        f"Bulk mismatch: sent {len(part)} docs but ES processed {len(items)} items"
                    )

                print(f"Bulk ok: {len(items)} actions (total {total_actions})")

    finally:
        # Restore refresh interval and force refresh
        set_refresh_interval(target, "1s")
        refresh(target)

    print(f"Done. Total indexed actions: {total_actions}")


if __name__ == "__main__":
    main()
