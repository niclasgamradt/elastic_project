# docs/06_preprocessing.md

import hashlib
import json
from datetime import datetime, timezone
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from scripts.config import SETTINGS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def make_doc_id(provider: str, source_id: str, ts: str) -> str:
    base = f"{provider}|{source_id}|{ts}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def _safe_get(arr: Any, i: int) -> Any:
    """Return arr[i] if arr is a list and index exists, else None."""
    if isinstance(arr, list) and 0 <= i < len(arr):
        return arr[i]
    return None


def normalize_ts(ts: str) -> str:
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def iter_processed_docs(raw: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    provider = raw.get("provider") or "open-meteo"
    payload = raw.get("payload") or {}

    hourly = payload.get("hourly") or {}
    times: List[str] = hourly.get("time") or []

    lat = str(raw.get("lat") or payload.get("latitude") or "unknown")
    lon = str(raw.get("lon") or payload.get("longitude") or "unknown")
    source_id = os.getenv("WORMS_SOURCE_ID", "56867")

    processed_at = datetime.now(timezone.utc).isoformat()

    for i, ts in enumerate(times):
        ts = (ts or "").strip()
        if not ts:
            continue

        yield {
            "doc_id": make_doc_id(provider, str(source_id), normalize_ts(ts)),
            "provider": provider,
            "source_id": str(source_id),
            "timestamp": normalize_ts(ts),
            "processed_at": processed_at,

            "temperature": _safe_get(hourly.get("temperature_2m"), i),
            "relative_humidity": _safe_get(hourly.get("relativehumidity_2m"), i),
            "pressure_msl": _safe_get(hourly.get("pressure_msl"), i),
            "precipitation": _safe_get(hourly.get("precipitation"), i),
        }


def main(run_id: str | None = None) -> None:
    if not run_id:
        raise ValueError("run_id required for preprocess_open_meteo")

    ensure_dir(SETTINGS.processed_dir)

    provider = "open-meteo"
    raw_file = SETTINGS.raw_dir / f"raw_{run_id}__{provider}.json"
    if not raw_file.exists():
        raise FileNotFoundError(raw_file)

    raw = json.loads(raw_file.read_text(encoding="utf-8"))
    out_file = SETTINGS.processed_dir / f"processed_{run_id}__{provider}.ndjson"

    n = 0
    with out_file.open("w", encoding="utf-8") as f:
        for doc in iter_processed_docs(raw):
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
            n += 1

    print(f"Wrote processed file: {out_file} (docs={n})")


if __name__ == "__main__":
    main()
