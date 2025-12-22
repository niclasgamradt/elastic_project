import json
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

from scripts.config import SETTINGS


def latest_processed_file(processed_dir: Path) -> Path:
    files = sorted(processed_dir.glob("processed_*.ndjson"))
    if not files:
        raise FileNotFoundError("No processed_*.ndjson found in data/processed/")
    return files[-1]


def build_bulk_lines(index_name: str, docs: List[Dict]) -> str:
    # NDJSON für _bulk: action-line + source-line
    lines = []
    for d in docs:
        doc_id = d.get("doc_id")
        if not doc_id:
            continue
        action = {"index": {"_index": index_name, "_id": doc_id}}
        lines.append(json.dumps(action, ensure_ascii=False))
        lines.append(json.dumps(d, ensure_ascii=False))
    return "\n".join(lines) + "\n"


def http_post(url: str, body: str, headers: Dict[str, str]) -> Tuple[int, str]:
    req = urllib.request.Request(url, data=body.encode("utf-8"), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status, resp.read().decode("utf-8")


def main() -> None:
    in_file = latest_processed_file(SETTINGS.processed_dir)
    docs = []
    with in_file.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                docs.append(json.loads(line))

    bulk_body = build_bulk_lines(SETTINGS.index_name, docs)

    status, resp_text = http_post(
        f"{SETTINGS.es_url}/_bulk",
        bulk_body,
        headers={"Content-Type": "application/x-ndjson"},
    )

    print(f"Bulk status: {status}")
    # Minimale Ausgabe, keine komplette Response-Spam
    resp = json.loads(resp_text)
    print(f"errors: {resp.get('errors')}, items: {len(resp.get('items', []))}")


if __name__ == "__main__":
    main()
