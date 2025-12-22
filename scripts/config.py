from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    # Verzeichnisse
    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")

    # Quelle (erstmal Dummy; später ersetzen)
    source_name: str = "example"

    # Elasticsearch
    es_url: str = "http://localhost:9200"
    index_name: str = "data-2024"
    alias_name: str = "all-data"

    # Files
    raw_prefix: str = "raw_"
    processed_prefix: str = "processed_"


SETTINGS = Settings()
