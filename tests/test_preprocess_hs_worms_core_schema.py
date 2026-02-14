# See documentation:
# docs/13_tests.md

import json
from pathlib import Path

import pytest

from scripts.config import Settings
import scripts.preprocess_hs_wetter as hs


CORE_KEYS = {
    "doc_id",
    "provider",
    "source_id",
    "timestamp",
    "processed_at",
    "temperature",
    "relative_humidity",
    "dew_point",
    "pressure_msl",
    "precipitation",
    "wind_speed",
    "wind_direction",
    "wind_gust_speed",
    "wind_gust_direction",
    "cloud_cover",
    "sunshine",
    "visibility",
    "condition",
    "icon",
    "solar",
}


def test_preprocess_hs_worms_produces_only_core_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: isolate filesystem using temp dirs by overriding SETTINGS in the module under test
    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    test_settings = Settings(
        raw_dir=raw_dir,
        processed_dir=processed_dir,
        es_url="http://localhost:9200",
        index_name="data-2026",
        alias_name="all-data",
        raw_prefix="raw_",
        processed_prefix="processed_",
    )
    monkeypatch.setattr(hs, "SETTINGS", test_settings)
    monkeypatch.setenv("HS_STATION_ID", "hs-worms")

    run_id = "2026-02-12"

    raw_payload = {
        "fetched_at": "2026-02-14T11:50:22+00:00",
        "provider": "hs-worms",
        "endpoint": "dummy",
        "payload": {
            "ts": 1771069818,  # 2026-02-14T11:50:18Z
            "temperature": {"out": 3.8, "in": 23.3},
            "humidity": {"out": 87, "in": 18},
            "baro": 1002.8793985,
            "wind": {"speed": {"kmh": 9.7}, "dir": {"deg": 26, "text": "NNE"}},
            "rain": {"rate": 0, "day": 0},
            "forecast": {"rule": 122, "val": 2},
            "batt": 4.74609375,
            "sun": {"uv": 1, "rad": 121},
        },
    }

    raw_file = raw_dir / f"raw_{run_id}__hs-worms.json"
    raw_file.write_text(json.dumps(raw_payload), encoding="utf-8")

    # Act
    hs.main(run_id=run_id)

    # Assert: output exists and is valid JSON
    out_file = processed_dir / f"processed_{run_id}__hs-worms.ndjson"
    assert out_file.exists()

    line = out_file.read_text(encoding="utf-8").strip()
    doc = json.loads(line)

    # Assert: only core keys (no provider-specific top-level fields)
    assert set(doc.keys()) <= CORE_KEYS

    # Guardrails: typical legacy HS fields must NOT appear
    assert "station_id" not in doc
    assert "temperature_out" not in doc
    assert "wind_speed_kmh" not in doc

    # Core semantics
    assert doc["provider"] == "hs-worms"
    assert doc["source_id"] == "hs-worms"
    assert isinstance(doc["temperature"], (int, float)) or doc["temperature"] is None

    # Unit conversion check: 9.7 km/h -> 2.694... m/s
    assert doc["wind_speed"] == pytest.approx(9.7 / 3.6, rel=1e-6)

    # Deterministic doc_id
    expected_doc_id = hs.make_doc_id("hs-worms", "hs-worms", doc["timestamp"])
    assert doc["doc_id"] == expected_doc_id
