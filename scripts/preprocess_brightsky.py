# See documentation:
# docs/06_preprocessing.md

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable

from scripts.config import SETTINGS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def make_doc_id(provider: str, source_id: str, ts: str) -> str:
    base = f"{provider}|{source_id}|{ts}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def iter_processed_docs(raw: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    provider = raw.get("provider") or "brightsky"
    payload = raw.get("payload") or {}
    weather = payload.get("weather") or []

    for w in weather:
        ts = (w.get("timestamp") or "").strip()
        source_id = str(w.get("source_id") or "unknown")

        yield {
            "doc_id": make_doc_id(provider, source_id, ts),
            "provider": provider,
            "source_id": source_id,
            "timestamp": ts,
            "processed_at": datetime.now(timezone.utc).isoformat(),

            "temperature": w.get("temperature"),
            "relative_humidity": w.get("relative_humidity"),
            "dew_point": w.get("dew_point"),
            "pressure_msl": w.get("pressure_msl"),
            "precipitation": w.get("precipitation"),
            "wind_speed": w.get("wind_speed"),
            "wind_direction": w.get("wind_direction"),
            "wind_gust_speed": w.get("wind_gust_speed"),
            "wind_gust_direction": w.get("wind_gust_direction"),
            "cloud_cover": w.get("cloud_cover"),
            "sunshine": w.get("sunshine"),
            "visibility": w.get("visibility"),
            "condition": w.get("condition"),
            "icon": w.get("icon"),
            "solar": w.get("solar"),
        }


def main(run_id: str | None = None) -> None:
    if not run_id:
        raise ValueError("run_id required for preprocess_brightsky")

    ensure_dir(SETTINGS.processed_dir)

    provider = "brightsky"
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
