import json
import urllib.request

from scripts.config import SETTINGS


def es_get(path: str) -> dict:
    url = f"{SETTINGS.es_url.rstrip('/')}{path}"
    with urllib.request.urlopen(url, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def test_alias_has_write_index() -> None:
    alias = SETTINGS.alias_name
    write_index = SETTINGS.index_name

    alias_info = es_get(f"/_alias/{alias}")

    # alias_info looks like:
    # { "<index>": { "aliases": { "<alias>": { "is_write_index": true } } } }
    assert write_index in alias_info, (
        f"Write index {write_index} not present in alias response"
    )

    aliases_block = alias_info[write_index].get("aliases", {}).get(alias, {})
    assert aliases_block.get("is_write_index") is True


def test_mapping_does_not_contain_hs_specific_fields() -> None:
    index = SETTINGS.index_name
    mapping = es_get(f"/{index}/_mapping")

    props = mapping[index]["mappings"]["properties"]

    # HS-specific fields should NOT be mapped in the provider-independent core schema
    hs_fields = [
        "temperature_in",
        "temperature_out",
        "relative_humidity_in",
        "relative_humidity_out",
        "wind_speed_kmh",
        "wind_dir_deg",
        "wind_dir_text",
        "rain_rate",
        "rain_day",
        "battery_v",
        "sun_uv",
        "sun_rad",
        "condition_rule",
        "condition_val",
    ]
    for f in hs_fields:
        assert f not in props, f"HS-specific field {f} must not be in mapping"
