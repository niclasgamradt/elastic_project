import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple, Any

from scripts.config import SETTINGS


def make_compare_doc_id(primary: str, compare: str, source_id: str, ts: str) -> str:
    raw = f"{primary}|{compare}|{source_id}|{ts}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def load_ndjson(path: Path) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """
    Returns dict keyed by (timestamp, source_id).
    """
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            ts = d.get("timestamp")
            sid = d.get("source_id")
            if ts and sid:
                out[(ts, str(sid))] = d
    return out


def main(run_id: str) -> None:
    primary = "brightsky"
    compare = "open-meteo"

    processed_dir = SETTINGS.processed_dir
    p_file = processed_dir / f"processed_{run_id}__{primary}.ndjson"
    c_file = processed_dir / f"processed_{run_id}__{compare}.ndjson"

    if not p_file.exists():
        raise FileNotFoundError(p_file)
    if not c_file.exists():
        raise FileNotFoundError(c_file)

    p = load_ndjson(p_file)
    c = load_ndjson(c_file)

    keys = sorted(set(p.keys()) | set(c.keys()))
    computed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    out_file = processed_dir / f"compare_{run_id}__{primary}_vs_{compare}.ndjson"
    n = 0

    with out_file.open("w", encoding="utf-8") as out:
        for (ts, sid) in keys:
            pd = p.get((ts, sid))
            cd = c.get((ts, sid))

            missing_primary = pd is None
            missing_compare = cd is None
            missing_rate = (int(missing_primary) + int(missing_compare)) / 2.0

            t_p = None if missing_primary else pd.get("temperature")
            t_c = None if missing_compare else cd.get("temperature")
            p_p = None if missing_primary else pd.get("pressure_msl")
            p_c = None if missing_compare else cd.get("pressure_msl")

            doc = {
                "doc_id": make_compare_doc_id(primary, compare, sid, ts),
                "timestamp": ts,
                "source_id": sid,
                "primary_provider": primary,
                "compare_provider": compare,
                "computed_at": computed_at,

                "temperature_primary": t_p,
                "temperature_compare": t_c,
                "delta_temperature": (t_p - t_c) if (t_p is not None and t_c is not None) else None,

                "pressure_primary": p_p,
                "pressure_compare": p_c,
                "delta_pressure": (p_p - p_c) if (p_p is not None and p_c is not None) else None,

                "missing_primary": missing_primary,
                "missing_compare": missing_compare,
                "missing_rate": missing_rate,
            }

            out.write(json.dumps(doc, ensure_ascii=False) + "\n")
            n += 1

    print(f"Wrote compare file: {out_file} (docs={n})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python scripts/compare_weather.py <run_id YYYY-MM-DD>")
    main(sys.argv[1])