# See documentation:
# docs/13_tests.md

import json
import urllib.request

from scripts.config import SETTINGS


def es_get(path: str) -> dict:
    url = SETTINGS.es_url.rstrip("/") + path
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_alias_all_data_has_write_index_data_2026() -> None:
    # GET /_alias/all-data liefert Alias-Infos je Index
    alias_info = es_get("/_alias/all-data")

    assert "data-2026" in alias_info
    assert "data-archive" in alias_info

    data_2026_alias = alias_info["data-2026"]["aliases"]["all-data"]
    assert data_2026_alias.get("is_write_index") is True


def test_mapping_does_not_contain_hs_specific_fields() -> None:
    mapping = es_get("/data-2026/_mapping")

    props = mapping["data-2026"]["mappings"]["properties"]

    # HS-spezifische Felder dürfen nicht im Mapping auftauchen
    forbidden = {"station_id", "temperature_out", "wind_speed_kmh"}
    assert forbidden.isdisjoint(set(props.keys()))
