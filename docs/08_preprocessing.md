# Preprocessing Logic

## Normalisierung
- Einheitliche Feldnamen
- ISO-8601 Timestamp
- Typkonvertierungen

## Deduplikation
- Deterministische doc_id (Hash)



# preprocess_*.py

## Zweck

Die `preprocess_*.py` Skripte transformieren die Rohdaten (`data/raw/`) in ein einheitliches, indexierbares Schema und erzeugen NDJSON-Dateien im Verzeichnis `data/processed/`.

Sie stellen sicher, dass:

- unterschiedliche APIs auf ein gemeinsames Datenmodell abgebildet werden
- Datentypen vereinheitlicht werden
- Zeitstempel normalisiert werden (ISO-8601 / UTC)
- deterministische `doc_id`-Werte erzeugt werden
- die Daten bulkfähig formatiert sind

---

## Rolle in der Pipeline

fetch_* → preprocess_* → load_to_es → post_checks

- `fetch_*`: speichert Rohdaten unverändert
- `preprocess_*`: transformiert in standardisiertes Schema
- `load_to_es`: übernimmt NDJSON in Elasticsearch

---

## Aufgaben eines preprocess-Skripts

Ein `preprocess_<provider>.py` muss:

1. Rohdatei für einen Run laden  
   (z. B. raw_<run_id>__provider.json)

2. Payload-Struktur der API auslesen

3. Daten auf gemeinsames Schema abbilden  
   Beispiel-Felder:
   - doc_id
   - provider
   - timestamp
   - temperature
   - relative_humidity
   - pressure_msl
   - wind_speed
   - etc.

4. `doc_id` deterministisch erzeugen  
   z. B. Hash aus:
   - provider
   - timestamp
   - station_id

5. NDJSON-Datei erzeugen  
   processed_<run_id>__provider.ndjson

---

## Gemeinsames Zielschema (Beispiel)

```json
{
  "doc_id": "...",
  "provider": "brightsky",
  "timestamp": "2026-02-12T00:00:00+00:00",
  "temperature": 8.3,
  "relative_humidity": 89,
  "pressure_msl": 983.9,
  "wind_speed": 10.8
}
```

### Template: `scripts/fetch_<provider>.py`

```python
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from scripts.config import SETTINGS


def make_doc_id(provider: str, key: str) -> str:
    base = f"{provider}|{key}".encode("utf-8")
    return hashlib.sha256(base).hexdigest()


def main(run_id: str | None = None) -> None:
    if not run_id:
        raise ValueError("run_id required")

    raw_file = SETTINGS.raw_dir / f"raw_{run_id}__newapi.json"
    processed_file = SETTINGS.processed_dir / f"processed_{run_id}__newapi.ndjson"

    raw = json.loads(raw_file.read_text(encoding="utf-8"))

    with processed_file.open("w", encoding="utf-8") as f:
        for item in raw["payload"]["data"]:
            timestamp = item["timestamp"]

            doc = {
                "doc_id": make_doc_id("newapi", timestamp),
                "provider": "newapi",
                "timestamp": timestamp,
                "temperature": item.get("temperature"),
                "relative_humidity": item.get("humidity"),
                "processed_at": datetime.now(timezone.utc).isoformat()
            }

            f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    print(f"Wrote processed file: {processed_file}")
```