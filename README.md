# Elastic Weather Data Engineering Project

End-to-End-Datenpipeline mit Apache Airflow und einem 3-Node-Elasticsearch-Cluster.  
Ziel ist die periodische Erfassung, Vorverarbeitung und Speicherung von Wetterdaten aus mehreren APIs.

---

## Projektarchitektur (Kurzüberblick)

1. **Airflow** orchestriert die Pipeline (`@daily`).
2. **Fetch-Skripte** holen Rohdaten von externen APIs.
3. **Preprocess-Skripte** normalisieren die Daten in ein einheitliches Schema.
4. **Elasticsearch (3 Nodes)** speichert die Daten via Bulk-API.
5. **Post-Checks** validieren Clusterzustand und Datenbestand.

---

## Verzeichnisstruktur

### `/dags`
Airflow-DAGs  
- `scrape_and_load.py` – Orchestriert Fetch → Preprocess → Load → Checks

---

### `/scripts`
Pipeline-Logik (Python)

**Infrastruktur**
- `apply_es.py` – Erstellt Template, Pipeline, Indizes, Alias
- `config.py` – Zentrale Projekt- und ES-Konfiguration
- `load_to_es.py` – Bulk-Import inkl. refresh-Optimierung
- `post_checks.py` – Health-, Count- und Aggregations-Checks

**Datenquellen**
- `fetch_brightsky.py` – Abruf BrightSky API
- `preprocess_brightsky.py` – Normalisierung BrightSky-Daten
- `fetch_hs_wetter.py` – Abruf HS-Worms Wetterstation
- `preprocess_hs_wetter.py` – Normalisierung HS-Daten

---

### `/db/elastic`
Elasticsearch-Konfiguration als Code

- `index-template.json` – Mapping & Settings
- `ingest-pipeline.json` – Ingest-Prozessoren
- `aliases.json` – Alias-Definition (z. B. `all-data`)

---

### `/data`
Persistente Daten-Layer

- `raw/` – Unveränderte API-Rohdaten (JSON)
- `processed/` – Normalisierte NDJSON-Dateien (Bulk-Ready)

---

### `/airflow_runtime`
Airflow-interne Laufzeitdaten (Logs, Config, Plugins)

---

### `/docs`
Detaillierte Projektdokumentation (Architektur, Designentscheidungen, Datenmodell, Queries, etc.)

---

## Infrastruktur

- 3-Node Elasticsearch Cluster (`es01`, `es02`, `es03`)
- Persistente Docker Volumes
- Airflow mit CeleryExecutor (Postgres + Redis)
- Komplettes Setup per `docker compose`

---

## Grundlegender Ablauf

```bash
docker compose up -d
