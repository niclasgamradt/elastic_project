import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

from scripts.config import SETTINGS


WS_RE = re.compile(r"\s+")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def latest_raw_file(raw_dir: Path) -> Path:
    files = sorted(raw_dir.glob("raw_*.json"))
    if not files:
        raise FileNotFoundError("No raw_*.json found in data/raw/")
    return files[-1]


def normalize_whitespace(text: str) -> str:
    return WS_RE.sub(" ", text.strip())


def parse_timestamp(value: Optional[str]) -> Optional[str]:
    """
    Normalisiert auf ISO-8601.
    Unterstützt u.a.:
    - 20251223T143230Z
    - ISO8601 (wird durchgereicht)
    """
    if not value:
        return None

    v = value.strip()

    # Format: YYYYmmddTHHMMSSZ
    try:
        dt = datetime.strptime(v, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except ValueError:
        pass

    # Wenn es schon wie ISO aussieht, lassen wir es (minimal)
    return v

def make_doc_id(source: str, url: str, published_at: str) -> str:
    base = f"{source}|{url}|{published_at}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def iter_processed_docs(raw: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    source = raw.get("source") or SETTINGS.source_name
    fetched_at = raw.get("fetched_at")

    for item in raw.get("items", []):
        url = (item.get("url") or "").strip()
        title = normalize_whitespace(item.get("title") or "")
        published_at = parse_timestamp(item.get("published_at")) or (fetched_at or "")
        content = normalize_whitespace(item.get("content") or "")

        doc = {
            "doc_id": make_doc_id(source, url, published_at),
            "source": source,
            "url": url,
            "title": title,
            "timestamp": published_at,      # später: echtes Datumsformat sicherstellen
            "message": content or title,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        yield doc


def main() -> None:
    ensure_dir(SETTINGS.processed_dir)

    raw_file = latest_raw_file(SETTINGS.raw_dir)
    raw = json.loads(raw_file.read_text(encoding="utf-8"))

    out_file = SETTINGS.processed_dir / raw_file.name.replace("raw_", "processed_").replace(".json", ".ndjson")

    with out_file.open("w", encoding="utf-8") as f:
        for doc in iter_processed_docs(raw):
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Wrote processed file: {out_file}")


if __name__ == "__main__":
    main()
