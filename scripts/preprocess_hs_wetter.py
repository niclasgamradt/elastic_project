# See documentation:
# docs/06_preprocessing.md

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from scripts.config import SETTINGS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def latest_hs_raw_file(raw_dir: Path) -> Path:
    files = sorted(raw_dir.glob("raw_*_hs.json"))
    if not files:
        raise FileNotFoundError("No raw_*_hs.json found in data/raw/")
    return files[-1]


def make_doc_id(provider: str, station_id: str, ts_iso: str) -> str:
    base = f"{provider}|{station_id}|{ts_iso}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def unix_to_iso(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()


def main(run_id: str | None = None) -> None:

    ensure_dir(SETTINGS.processed_dir)

    if not run_id:
        raise ValueError("run_id required for preprocess_hs_wetter")

    raw_file = SETTINGS.raw_dir / f"raw_{run_id}__hs-worms.json"
    if not raw_file.exists():
        raise FileNotFoundError(raw_file)
    
    raw = json.loads(raw_file.read_text(encoding="utf-8"))

    payload: Dict[str, Any] = raw.get("payload") or {}
    provider = "hs-worms"
    station_id = os.getenv("HS_STATION_ID", "hs-worms")

    # Messzeitpunkt aus der API: "ts" (unix)
    ts_unix = payload.get("ts")
    if ts_unix is None:
        raise RuntimeError("HS payload missing 'ts'")
    ts_iso = unix_to_iso(int(ts_unix))

    doc = {
        "doc_id": make_doc_id(provider, station_id, ts_iso),
        "provider": provider,
        "station_id": station_id,
        "timestamp": ts_iso,
        "processed_at": datetime.now(timezone.utc).isoformat(),

        # Common weather fields (vereinheitlicht)
        "temperature_out": (payload.get("temperature") or {}).get("out"),
        "temperature_in": (payload.get("temperature") or {}).get("in"),
        "relative_humidity_out": (payload.get("humidity") or {}).get("out"),
        "relative_humidity_in": (payload.get("humidity") or {}).get("in"),
        "pressure_msl": payload.get("baro"),
        "wind_speed_kmh": ((payload.get("wind") or {}).get("speed") or {}).get("kmh"),
        "wind_dir_deg": ((payload.get("wind") or {}).get("dir") or {}).get("deg"),
        "wind_dir_text": ((payload.get("wind") or {}).get("dir") or {}).get("text"),
        "rain_rate": ((payload.get("rain") or {}).get("rate")),
        "rain_day": ((payload.get("rain") or {}).get("day")),
        "condition_rule": ((payload.get("forecast") or {}).get("rule")),
        "condition_val": ((payload.get("forecast") or {}).get("val")),

        # optional
        "battery_v": payload.get("batt"),
        "sun_uv": ((payload.get("sun") or {}).get("uv")),
        "sun_rad": ((payload.get("sun") or {}).get("rad")),
    }

    out_file = SETTINGS.processed_dir / f"processed_{run_id}__hs-worms.ndjson"

    out_file.write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote processed file: {out_file} (docs=1)")


if __name__ == "__main__":
    main()
