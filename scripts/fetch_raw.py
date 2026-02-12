import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from scripts.config import SETTINGS


def utc_stamp_compact() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main(run_date: str | None = None) -> None:
    ensure_dir(SETTINGS.raw_dir)

    ts = utc_stamp_compact()
    out_file = SETTINGS.raw_dir / f"{SETTINGS.raw_prefix}{ts}.json"

    provider = os.getenv("WEATHER_PROVIDER", "brightsky")
    lat = os.getenv("WORMS_LAT", "49.6")
    lon = os.getenv("WORMS_LON", "8.36")
    base = os.getenv("BRIGHTSKY_BASE", "https://api.brightsky.dev")

    # Airflow-Datum verwenden, falls vorhanden
    if run_date:
        day = run_date
    else:
        day = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    url = f"{base}/weather?lat={lat}&lon={lon}&date={day}"

    print(f"Fetching: {url}")

    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}")
            payload = json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTPError {e.code}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}")

    raw = {
        "fetched_at": ts,
        "provider": provider,
        "lat": lat,
        "lon": lon,
        "date": day,
        "endpoint": url,
        "payload": payload,
    }

    out_file.write_text(
        json.dumps(raw, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Wrote raw file: {out_file}")


if __name__ == "__main__":
    main()
