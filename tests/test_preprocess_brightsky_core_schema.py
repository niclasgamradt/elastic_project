# See documentation:
# docs/13_tests.md

import json
from pathlib import Path

import pytest

from scripts.config import Settings
import scripts.preprocess_brightsky as br


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


def test_preprocess_brightsky_produces_only_core_schema(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Arrange: isolate filesystem
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
    monkeypatch.setattr(br, "SETTINGS", test_settings)

    run_id = "2026-02-12"

    # Minimaler BrightSky-Raw-Body, so dass preprocess_brightsky laufen kann.
    # Falls dein preprocess andere Felder erwartet, musst du diese Struktur anpassen.
    raw_payload = {
        "fetched_at": "2026-02-12T00:00:00+00:00",
        "provider": "brightsky",
        "endpoint": "dummy",
        "payload": {
            "weather": [
                {
                    "timestamp": "2026-02-12T00:00:00+00:00",
                    "source_id": 7307,
                    "temperature": 8.3,
                    "relative_humidity": 89,
                    "dew_point": 6.6,
                    "pressure_msl": 983.9,
                    "precipitation": 0.0,
                    "wind_speed": 10.8,
                    "wind_direction": 180,
                    "wind_gust_speed": 16.6,
                    "wind_gust_direction": 170,
                    "cloud_cover": 100,
                    "sunshine": 0.0,
                    "visibility": 19710,
                    "condition": "dry",
                    "icon": "cloudy",
                    "solar": 0.0,
                },
                {
                    "timestamp": "2026-02-12T01:00:00+00:00",
                    "source_id": 7307,
                    "temperature": 7.8,
                    "relative_humidity": 94,
                    "dew_point": 6.9,
                    "pressure_msl": 982.6,
                    "precipitation": 1.6,
                    "wind_speed": 10.8,
                    "wind_direction": 170,
                    "wind_gust_speed": 20.5,
                    "wind_gust_direction": 160,
                    "cloud_cover": 100,
                    "sunshine": 0.0,
                    "visibility": 19760,
                    "condition": "rain",
                    "icon": "rain",
                    "solar": 0.0,
                },
            ]
        },
    }

    raw_file = raw_dir / f"raw_{run_id}__brightsky.json"
    raw_file.write_text(json.dumps(raw_payload), encoding="utf-8")

    # Act
    br.main(run_id=run_id)

    # Assert
    out_file = processed_dir / f"processed_{run_id}__brightsky.ndjson"
    assert out_file.exists()

    lines = [ln for ln in out_file.read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) == 2

    docs = [json.loads(ln) for ln in lines]

    for d in docs:
        assert set(d.keys()) <= CORE_KEYS
        assert d["provider"] == "brightsky"
        assert d["source_id"] is not None
        assert d["timestamp"].startswith("2026-02-12T")
        assert "processed_at" in d

        # Typen (minimal)
        assert isinstance(d["temperature"], (int, float)) or d["temperature"] is None
        assert isinstance(d["pressure_msl"], (int, float)) or d["pressure_msl"] is None

    # Determinismus doc_id: gleiche Funktion wie im Modul nutzen (falls vorhanden)
    # Wenn dein Modul anders heißt, musst du das anpassen.
    if hasattr(br, "make_doc_id"):
        for d in docs:
            expected = br.make_doc_id("brightsky", str(d["source_id"]), d["timestamp"])
            assert d["doc_id"] == expected
