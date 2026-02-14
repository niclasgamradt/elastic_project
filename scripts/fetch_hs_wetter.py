# See documentation:
# docs/05_ingestion_pipeline.md


import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from scripts.config import SETTINGS


def utc_stamp_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def http_get_json(url: str, timeout: int = 30) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        ct = (resp.headers.get("Content-Type") or "").lower()
        body = resp.read().decode("utf-8")
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {body[:200]}")
        if "json" not in ct:
            raise RuntimeError(f"Unexpected Content-Type: {ct}, body starts: {body[:200]}")
        return json.loads(body)


def main(run_id: str | None = None) -> None:
    ensure_dir(SETTINGS.raw_dir)

    ts_fetch = run_id if run_id else utc_stamp_compact()
    out_file = SETTINGS.raw_dir / f"raw_{ts_fetch}__hs-worms.json"


    url = os.getenv("HS_WETTER_URL", "https://wetter.hs-worms.de/api/v3/data").strip()
    print(f"Fetching HS: {url}")

    payload = http_get_json(url, timeout=30)

    raw = {
        "fetched_at": ts_fetch,
        "provider": "hs-worms",
        "endpoint": url,
        "payload": payload,
    }

    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote raw file: {out_file}")


if __name__ == "__main__":
    main()
