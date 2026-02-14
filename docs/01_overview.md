# Technische Dokumentation – Weather Data Pipeline (Airflow + Elasticsearch)

## Projektüberblick

Dieses Repository implementiert eine periodische Data-Engineering-Pipeline zur Erfassung und Vereinheitlichung von Wetterdaten aus mehreren APIs. Die Verarbeitung wird durch Airflow orchestriert und die Ergebnisse werden in einem 3-Node-Elasticsearch-Cluster gespeichert (Alias-basiertes Schreiben, Infrastructure-as-Code).

Datenfluss:
Fetch (API) → Raw (JSON) → Preprocess (NDJSON) → Bulk Load (ES) → Post Checks


## Laufzeitumgebung (Docker Compose)

### Komponenten

- Elasticsearch-Cluster: `es01`, `es02`, `es03`
- Airflow-Stack (CeleryExecutor):
  - `airflow-api-server`
  - `airflow-scheduler`
  - `airflow-dag-processor`
  - `airflow-triggerer`
  - `airflow-worker`
- Airflow Dependencies:
  - `postgres` (Airflow Metadatenbank)
  - `redis` (Celery Broker)

### Persistenz

- Elasticsearch: `esdata01`, `esdata02`, `esdata03`
- Airflow: `airflow_postgres` sowie Runtime-Verzeichnisse unter `./airflow_runtime/` (Logs/Config/Plugins)

Elasticsearch-Daten liegen in Docker-Volumes (persistieren Container-Neustarts). Pipeline-Daten liegen im Repository unter `data/` (host-gemountet).


## Repository-Struktur

- `dags/`  
  Airflow DAGs (Orchestrierung der Pipeline)

- `scripts/`  
  Python-Skripte für Fetch/Preprocess/Load/Checks sowie ES-Setup

- `db/elastic/`  
  Elasticsearch-Konfiguration „as code“:
  - `index-template.json`
  - `ingest-pipeline.json`
  - `aliases.json`

- `data/raw/`  
  Rohdaten (JSON) pro Run und Provider

- `data/processed/`  
  Normalisierte Daten (NDJSON) pro Run und Provider

- `airflow_runtime/`  
  Airflow Runtime (Logs/Config/Plugins) außerhalb des Images

- `.env.example`  
  Vorlage für konfigurierbare Umgebungsvariablen

Hinweis zur Python-Struktur: `scripts/__init__.py` markiert `scripts/` als Package und ermöglicht Imports aus Airflow-Tasks (z. B. `from scripts.load_to_es import main`).


## Konfiguration

### `.env` / `.env.example`

Docker Compose liest `.env` automatisch ein. `.env.example` ist die Vorlage für:
- Elasticsearch-Version/Clustername/Heap
- Airflow Secrets/Auth
- Provider-spezifische API Parameter (z. B. Koordinaten, Base URLs)

### `scripts/config.py`

Zentrale Runtime-Konfiguration über `SETTINGS`:
- Pfade: `data/raw`, `data/processed` (ab Projekt-Root)
- Elasticsearch: `ES_URL`, `ES_INDEX`, `ES_ALIAS`
- Dateinamenskonventionen (`raw_`, `processed_`)


## Datenquellen

### BrightSky API
- Standortbasiert über `lat/lon`
- Zeitreihen (typisch stündliche Werte pro Datum)
- Response wird unverändert im Raw-Layer gespeichert, anschließend in einzelne Messpunkte normalisiert

### HS-Worms Wetterstation API
- Aktuelle Messwerte der lokalen Station
- Ein Dokument pro Fetch (Snapshot)
- Response wird unverändert im Raw-Layer gespeichert, anschließend auf ein Messwert-Dokument normalisiert


## Daten-Layer und Namenskonventionen

### Raw Layer
Unveränderte API-Responses als JSON:

- `data/raw/raw_<run_id>__<provider>.json`

Inhalt (technischer Rahmen):
- `fetched_at`
- `provider`
- `endpoint`
- `payload` (Originalresponse)

### Processed Layer
Normalisierte Daten als NDJSON (ein JSON-Objekt pro Zeile):

- `data/processed/processed_<run_id>__<provider>.ndjson`

Konvention:
- deterministische `doc_id` pro Messpunkt (Idempotenz)
- `timestamp` als ISO-8601 / UTC (wo möglich)
- `processed_at` als technischer Zeitpunkt der Transformation


## Orchestrierung (Airflow DAG)

### DAG
- Name: `scrape_and_load`
- Datei: `dags/scrape_and_load.py`
- Schedule: `@daily`
- `catchup=False`
- Run-Identifier: `run_id = {{ ds }}` (Format `YYYY-MM-DD`)

### Aufgabenfolge (fachlich)
1. `apply_es`  
2. `fetch_brightsky` → `preprocess_brightsky`  
3. `fetch_hs` → `preprocess_hs`  
4. `load_to_es`  
5. `post_checks`

`load_to_es` startet erst, wenn alle gewünschten `processed_<run_id>__*.ndjson` vorliegen.


## Pipeline-Skripte (scripts/)

### `apply_es.py`
Automatisiert die Elasticsearch-Konfiguration:
- Index-Template anlegen/aktualisieren
- Ingest-Pipeline anlegen/aktualisieren
- Indizes erstellen (idempotent; „already exists“ ist erwartbar)
- Alias-Konfiguration setzen
- Health-Minicheck

Konfiguration wird aus `db/elastic/` geladen.

### `fetch_<provider>.py`
Aufgabe: Rohdatenabruf und Speicherung als Raw JSON.
- baut die Provider-URL deterministisch (inkl. Query-Parameter)
- führt HTTP GET mit Timeout aus
- speichert `payload` unverändert unter `data/raw/` als `raw_<run_id>__<provider>.json`

Implementiert im Projekt:
- `fetch_brightsky.py`
- `fetch_hs_wetter.py`

### `preprocess_<provider>.py`
Aufgabe: Transformation Raw → Processed.
- liest `raw_<run_id>__<provider>.json`
- extrahiert relevante Felder aus dem Provider-Payload
- normalisiert Zeitstempel (ISO-8601/UTC, soweit verfügbar)
- erzeugt deterministische `doc_id`
- schreibt NDJSON nach `data/processed/processed_<run_id>__<provider>.ndjson`

Implementiert im Projekt:
- `preprocess_brightsky.py`
- `preprocess_hs_wetter.py`

### `load_to_es.py`
Bulk-Ingestion der Processed-Daten nach Elasticsearch.
- lädt für einen `run_id` alle Dateien: `processed_<run_id>__*.ndjson`
- schreibt gegen Alias (z. B. `all-data`), falls gesetzt; sonst gegen `ES_INDEX`
- nutzt Bulk API: `POST /_bulk?pipeline=standardize-v1`
- setzt `refresh_interval=-1` während Bulk, danach `refresh_interval=1s` + `_refresh`
- Idempotenz über `_id = doc_id`

### `post_checks.py`
Technische Validierung nach dem Import:
- Cluster Health
- `_count` gegen Alias/Ziel
- Beispielabfrage der zuletzt indexierten Dokumente (Sortierung nach `timestamp`)
- einfache Aggregation (z. B. Terms nach `provider`)

### Optional/Tooling
- `debug_es.py`: manuelle Debug-Ausgaben (`_cat/indices`, `_cat/aliases`, Sample Docs)
- `inspect_processed.py`: lokale Kontrolle einer Processed-Datei (Schema-/Feldcheck)

Diese Tools sind nicht Teil der DAG-Execution, sondern für Debug/Validierung.


## Elasticsearch-Konfiguration (db/elastic/)

### `index-template.json`
Definiert Settings und Basismapping für Indizes, die auf `index_patterns` matchen.
- Settings: `number_of_shards`, `number_of_replicas`, `refresh_interval`
- Mappings: Basisschema

Hinweis: Wenn Processed-Dokumente zusätzliche Felder enthalten, die nicht explizit im Template gemappt sind, werden sie (je nach Cluster-Defaults) dynamisch gemappt. Für stabile Typen (Messwerte/keyword/date) sollte das Template explizit erweitert werden.

### `ingest-pipeline.json`
Definiert eine Ingest-Pipeline (z. B. `standardize-v1`), die beim Indexieren angewendet wird.
Typische Aufgaben:
- `timestamp` Normalisierung (date processor)
- technisches Feld `processed_at` setzen
- harmlose Feld-Transformationen mit `ignore_missing`

Die Pipeline wird beim Bulk-Load über `?pipeline=<name>` aktiviert.

### `aliases.json`
Definiert Alias-Actions (z. B. `all-data`):
- Alias zeigt auf mehrere Indizes
- `is_write_index=true` markiert das Schreibziel

Beispielprinzip:
- `data-2024` als Write-Index
- `data-archive` als zusätzlicher Read-Index unter demselben Alias


## Erweiterung um weitere APIs (Kurzstandard)

1. Neues Fetch-Skript: `scripts/fetch_<provider>.py`
   - Raw JSON: `raw_<run_id>__<provider>.json`
   - Metadaten: `fetched_at`, `endpoint`, `provider`, `payload`

2. Neues Preprocess-Skript: `scripts/preprocess_<provider>.py`
   - NDJSON: `processed_<run_id>__<provider>.ndjson`
   - deterministische `doc_id` pro Messpunkt
   - `timestamp` und Messwerte normalisieren

3. DAG erweitern (`dags/scrape_and_load.py`)
   - Fetch/Preprocess Tasks hinzufügen
   - Dependency so setzen, dass `load_to_es` nach allen Preprocess-Schritten läuft

4. Elasticsearch Mapping ggf. anpassen (`db/elastic/index-template.json`)
   - stabile Typen für neue Felder (date/keyword/float/int)
   - Vermeidung unerwünschter dynamischer Typen


## Betrieb / technische Checks

Elasticsearch:
- `_cluster/health`
- `_cat/nodes?v`
- `_cat/shards?v`
- Alias/Counts: `/<alias>/_count`

Airflow:
- `airflow dags list`
- `airflow dags list-import-errors`
- Logs über `docker compose logs <service>`

Daten-Layer:
- `data/raw/` enthält pro Provider eine Raw-Datei je Run
- `data/processed/` enthält pro Provider eine NDJSON-Datei je Run
