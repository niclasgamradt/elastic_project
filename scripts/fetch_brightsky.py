# See documentation:
# docs/06_ingestion_pipeline.md

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
        body = resp.read().decode("utf-8")
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status}: {body[:200]}")
        ct = (resp.headers.get("Content-Type") or "").lower()
        if "json" not in ct:
            raise RuntimeError(f"Unexpected Content-Type: {ct}, body starts: {body[:200]}")
        return json.loads(body)


def main(run_id: str | None = None) -> None:
    ensure_dir(SETTINGS.raw_dir)

    provider = "brightsky"
    lat = os.getenv("WORMS_LAT", "49.6")
    lon = os.getenv("WORMS_LON", "8.36")
    base = os.getenv("BRIGHTSKY_BASE", "https://api.brightsky.dev")

    ts_fetch = run_id if run_id else utc_stamp_compact()
    day = run_id if run_id else datetime.now(timezone.utc).strftime("%Y-%m-%d")

    out_file = SETTINGS.raw_dir / f"raw_{ts_fetch}__{provider}.json"
    url = f"{base}/weather?lat={lat}&lon={lon}&date={day}"

    print(f"Fetching BrightSky: {url}")
    payload = http_get_json(url, timeout=30)

    raw = {
        "fetched_at": utc_stamp_compact(),
        "provider": provider,
        "lat": lat,
        "lon": lon,
        "date": day,
        "endpoint": url,
        "payload": payload,
    }

    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote raw file: {out_file}")


if __name__ == "__main__":
    main()
