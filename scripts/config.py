# Ausführliche Dokumentation:
# docs/02_architecture.md

import os
from dataclasses import dataclass
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Settings:
    # directories
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"

    # elasticsearch
    es_url: str = os.getenv("ES_URL", "http://localhost:9200")
    index_name: str = os.getenv("ES_INDEX", "data-2024")
    alias_name: str = os.getenv("ES_ALIAS", "all-data")

    # file naming
    raw_prefix: str = "raw_"
    processed_prefix: str = "processed_"


SETTINGS = Settings()
