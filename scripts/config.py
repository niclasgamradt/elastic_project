# See documentation:
# docs/09_elasticsearch_index_design.md

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    # Paths
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"

    # Elasticsearch
    es_url: str = os.getenv("ES_URL", "http://localhost:9200")
    index_name: str = os.getenv("ES_INDEX", "weather-processed-2026")
    archive_index: str = os.getenv("ES_ARCHIVE_INDEX", "weather-archive")
    alias_name: str = os.getenv("ES_ALIAS", "weather-all")

    # Naming conventions
    raw_prefix: str = "raw_"
    processed_prefix: str = "processed_"


SETTINGS = Settings()
