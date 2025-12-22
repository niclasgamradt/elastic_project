import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.config import SETTINGS


def utc_stamp_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_dir(SETTINGS.raw_dir)

    ts = utc_stamp_compact()
    out_file = SETTINGS.raw_dir / f"{SETTINGS.raw_prefix}{ts}.json"

    # Dummy-Rohdaten: ersetzen Sie später durch echten HTTP/RSS Abruf
    raw = {
        "fetched_at": ts,
        "source": SETTINGS.source_name,
        "items": [
            {"title": "Example Item", "url": "https://example.com", "published_at": ts, "content": "hello world"}
        ],
    }

    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote raw file: {out_file}")


if __name__ == "__main__":
    main()
