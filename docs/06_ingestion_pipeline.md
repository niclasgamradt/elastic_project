# Ingestion Details

## Fetch
- HTTP GET Requests
- Fehlerbehandlung (HTTP Status, Timeout)
- Speicherung als raw JSON

## Run-ID
- run_id basiert auf Airflow Execution Date
- Dateibenennung: raw_<run_id>__provider.json

## Reproduzierbarkeit
Rohdaten bleiben erhalten (Reprocessing möglich).


## Neue API anbinden: Anforderungen an `fetch_<provider>.py`

Um eine weitere API einzubinden, wird ein neues Fetch-Skript nach dem Muster  
`scripts/fetch_<provider>.py` erstellt. Das Skript ist ausschließlich für den
**Rohdatenabruf** zuständig (keine Normalisierung).

### Muss-Aufgaben im Fetch-Skript

1. **Parameter / Konfiguration lesen**
   - z. B. API-Base-URL, Token, Standortparameter, etc. (über `os.getenv()` oder `SETTINGS`)
   - optional: Provider-Name festlegen (`provider = "<provider>"`)

2. **Run-ID / Datum ableiten**
   - `run_id` (z. B. `YYYY-MM-DD`) aus Airflow übernehmen, falls vorhanden
   - Fallback auf aktuelles Datum, wenn `run_id` nicht gesetzt ist

3. **API-Endpunkt/URL bauen**
   - URL inkl. Query-Parametern deterministisch zusammensetzen
   - Endpoint-URL in den Rohdaten mit abspeichern (Nachvollziehbarkeit)

4. **HTTP-Request durchführen**
   - `GET` Request mit sinnvollen Headers (Accept, Auth)
   - Timeout setzen
   - HTTP-Fehler sauber behandeln (Statuscodes, Exceptions)

5. **Rohdaten unverändert speichern (Raw Layer)**
   - Ziel: `data/raw/`
   - Dateiname: `raw_<run_id>__<provider>.json`
   - Inhalt enthält Metadaten + Original-Payload, z. B.:
     - `fetched_at`
     - `provider`
     - `endpoint`
     - `payload` (unverändert)

6. **Deterministische Ausgaben**
   - `print()` mit Endpoint + Output-Datei (Debug/Logging)
   - Keine Seiteneffekte außerhalb von `data/raw`

### Wichtig (Abgrenzung)
- Keine Feldnamen ändern
- Keine Typkonvertierung
- Keine Deduplikation
- Keine NDJSON-Erzeugung  
Diese Schritte gehören ausschließlich in `preprocess_<provider>.py`.


### Template: `scripts/fetch_<provider>.py`

```python
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from scripts.config import SETTINGS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main(run_id: str | None = None) -> None:
    """
    Fetches raw data from <provider> API and stores it unchanged
    in data/raw as JSON.
    """

    ensure_dir(SETTINGS.raw_dir)

    provider = "<provider-name>"

    # 1) Determine run date
    if run_id:
        date_str = run_id
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 2) Build API URL
    base_url = os.getenv("<PROVIDER>_BASE_URL", "https://api.example.com")
    url = f"{base_url}/endpoint?date={date_str}"

    print(f"Fetching {provider}: {url}")

    # 3) HTTP request
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}")
            payload = json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTPError {e.code}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}")

    # 4) Store raw data
    raw = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "run_id": date_str,
        "endpoint": url,
        "payload": payload,
    }

    out_file = SETTINGS.raw_dir / f"raw_{date_str}__{provider}.json"
    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote raw file: {out_file}")


if __name__ == "__main__":
    main()
```




# scrape_and_load (Airflow DAG)

## Zweck

`scrape_and_load` ist der zentrale Airflow-DAG des Projekts.  
Er orchestriert die vollständige End-to-End-Datenpipeline vom API-Abruf bis zur Speicherung in Elasticsearch.

Der DAG automatisiert:

- Infrastruktur-Initialisierung
- Datenabruf von mehreren APIs
- Vorverarbeitung
- Bulk-Ingestion
- technische Validierung

---

## Zeitsteuerung

Der DAG läuft periodisch:

- Schedule: `@daily`
- `catchup=False`

Das bedeutet:
- tägliche Ausführung
- keine rückwirkende Verarbeitung alter Zeiträume

---

## Task-Reihenfolge

Struktur:

apply_es  
→ fetch_*  
→ preprocess_*  
→ load_to_es  
→ post_checks  

---

## Einzelne Tasks

### apply_es

- Legt Index-Template an
- Erstellt Ingest-Pipeline
- Erstellt Indizes
- Setzt Alias
- Prüft Cluster-Zustand

Sorgt für idempotentes Elasticsearch-Setup.

---

### fetch_brightsky / fetch_hs

- Ruft externe APIs ab
- Speichert Rohdaten unverändert in `data/raw/`
- Benennt Dateien mit `run_id`

---

### preprocess_brightsky / preprocess_hs

- Transformiert Rohdaten in gemeinsames Schema
- Normalisiert Zeitstempel
- Erzeugt deterministische `doc_id`
- Schreibt NDJSON nach `data/processed/`

---

### load_to_es

- Liest alle `processed_<run_id>__*.ndjson`
- Führt Bulk-Ingestion aus
- Nutzt Ingest-Pipeline
- Optimiert temporär `refresh_interval`

---

### post_checks

- Prüft Cluster Health
- Prüft Dokumentanzahl
- Führt Beispiel-Search aus
- Führt Aggregation aus

---

## Multi-Source-Integration

Der DAG unterstützt mehrere Datenquellen parallel.

Pro Run werden mehrere Dateien verarbeitet:

processed_<run_id>__brightsky.ndjson  
processed_<run_id>__hs-worms.ndjson  

Alle Daten werden in denselben Alias geladen.



# Airflow

## Zweck

Airflow orchestriert die vollständige Datenpipeline. Dadurch laufen alle Schritte periodisch, reproduzierbar und in definierter Reihenfolge – ohne manuelle Eingriffe. Der DAG verbindet Datenquellen (APIs), Vorverarbeitung, Elasticsearch-Ingestion und abschließende Checks.

## DAG

Der zentrale DAG heißt `scrape_and_load` und liegt hier:

- `dags/scrape_and_load.py`

Wichtige Parameter:

- Schedule: `@daily`
- Catchup: `False`
- Übergabe eines Run-Identifiers über `{{ ds }}` (Format `YYYY-MM-DD`)

## Task-Reihenfolge

Ablauf (logisch):

1. `apply_es`
2. `fetch_brightsky`
3. `preprocess_brightsky`
4. `fetch_hs`
5. `preprocess_hs`
6. `load_to_es`
7. `post_checks`

Hinweis: Die Reihenfolge kann bei Bedarf angepasst werden (z. B. beide Fetch-Schritte parallel, danach beide Preprocess-Schritte parallel). Wichtig ist, dass `load_to_es` erst startet, wenn alle gewünschten `processed_*` Dateien vorliegen.

## Aufgaben je Task

apply_es  
Initialisiert Elasticsearch automatisiert:

- legt Index-Template an
- legt Ingest-Pipeline an
- erstellt benötigte Indizes
- setzt Aliases
- führt einen kurzen Health-Check aus

fetch_*  
Ruft externe APIs ab und speichert Rohdaten unverändert im Raw-Layer:

- Zielpfad: `data/raw/`
- Dateiname: `raw_<run_id>__<provider>.json`

preprocess_*  
Transformiert Rohdaten in ein einheitliches Schema und schreibt NDJSON:

- Zielpfad: `data/processed/`
- Dateiname: `processed_<run_id>__<provider>.ndjson`
- erzeugt deterministische `doc_id` Werte
- normalisiert Zeitstempel (ISO-8601 / UTC)

load_to_es  
Lädt alle `processed_<run_id>__*.ndjson` Dateien des Runs via Bulk-API in Elasticsearch:

- Ziel: Alias (z. B. `all-data`)
- optionales Performance-Tuning über `refresh_interval` während Bulk
- Nutzung der Ingest-Pipeline `standardize-v1`

post_checks  
Validiert nach der Ingestion den Cluster- und Datenzustand:

- Cluster Health
- Dokumentanzahl über `_count`
- Beispiel-Search (`_search`)
- einfache Aggregation (z. B. nach `provider`)

## run_id-Konzept

Airflow übergibt als `run_id` typischerweise:

- `{{ ds }}` → `YYYY-MM-DD`

Dieses Datum wird im Dateinamen verwendet, damit jeder Lauf eindeutig nachvollziehbar ist:

- `raw_2026-02-12__brightsky.json`
- `processed_2026-02-12__brightsky.ndjson`

Vorteile:

- klare Zuordnung Run → Dateien
- reproduzierbares Reprocessing
- Multi-Source-Unterstützung pro Lauf

## Reproduzierbarkeit

Airflow ist vollständig über Docker Compose integriert (CeleryExecutor mit Postgres + Redis). Der DAG und alle Pipeline-Skripte sind im Repository versioniert und werden in den Container gemountet.

Es gibt keine manuelle Konfiguration über UI-Klicks; alle Einstellungen sind „as code“ abgebildet.

