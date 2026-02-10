# TODO - Projektstatus und naechste Schritte

## Gesamtfazit
Das Projekt ist bereits als lauffaehige End-to-End-Pipeline umgesetzt:
- Reproduzierbares Deployment per Docker Compose
- Orchestrierung per Airflow
- Daten-Layer (`raw`/`processed`)
- Elasticsearch-Setup mit 3 Nodes, Templates, Pipeline und Aliases

Es ist damit klar im **Implementierungsstatus** (nicht mehr reine Planung).

## Bereits umgesetzt (nachweisbar)

### 1) Deployment und Reproduzierbarkeit
- `docker-compose.yml` umfasst:
  - Elasticsearch-Cluster mit 3 Nodes (`es01`, `es02`, `es03`)
  - Persistente Volumes fuer alle Nodes
  - Airflow-Stack (API-Server, Scheduler, Worker, Triggerer, DAG-Processor) mit Postgres + Redis + CeleryExecutor
- Airflow-Container binden das Projekt nach `/opt/airflow/project` und setzen `PYTHONPATH` korrekt.
- Ergebnis: Setup ist reproduzierbar und als Code abbildbar (ohne manuelle Klick-Konfiguration).

### 2) Elasticsearch-Zustand
- Clusterstatus: `GREEN`
- 3 Nodes aktiv, keine `unassigned_shards`
- Indizes vorhanden: `data-2024`, `data-archive`
- Alias vorhanden: `all-data` (`count=7`)
- Shards/Replicas:
  - `data-2024`: `1 primary + 1 replica`
  - `data-archive`: `1 primary + 1 replica`
- Verteilung ueber mehrere Nodes ist vorhanden.

### 3) Infrastructure-as-Code fuer ES
- Konfigurationsdateien:
  - `db/elastic/index-template.json`
  - `db/elastic/ingest-pipeline.json`
  - `db/elastic/aliases.json`
- Automatisierung ueber `scripts/apply_es.py`:
  - legt Index Template an
  - legt Ingest Pipeline an
  - erstellt `data-2024` und `data-archive`
  - setzt Alias `all-data` inkl. `write_index`
  - prueft Cluster Health

### 4) Pipeline-Logik und Daten-Layer
- DAG: `dags/scrape_and_load.py`
- Schedule: `@daily` (`catchup=False`)
- Taskfolge: `apply_es -> fetch_raw -> preprocess -> load_to_es -> post_checks`
- Daten-Layer:
  - `data/raw/*` (JSON-Rohdaten)
  - `data/processed/*` (NDJSON)
- Skripte:
  - `fetch_raw.py`: erzeugt aktuell Dummy-Rohdaten
  - `preprocess.py`: normalisiert Rohdaten zu NDJSON (`doc_id`, `timestamp`, `message`, ...)
  - `load_to_es.py`: idempotenter Bulk-Import (`_id=doc_id`), nutzt Pipeline `standardize-v1`, optimiert `refresh_interval` waehrend Bulk
  - `post_checks.py`: `health`, `count`, `last_docs` (timestamp desc), `aggregation by_source`

## Offene Punkte (priorisiert)

### A) Pflicht (hoch): Echte Datenquellen anbinden
- **Ist:** `fetch_raw.py` nutzt Dummy-Daten.
- **Risiko:** Scraping/periodischer Realabgriff ist nicht ausreichend nachgewiesen.
- **To-do:**
  - Hochschul-Wetterstation (API) anbinden
  - Mindestens 1 Referenzquelle anbinden
  - Timeout-/HTTP-/Empty-Response-Handling ergaenzen
  - Rohformat unveraendert als JSON in `raw` speichern

### B) Pflicht (hoch): Alignment mit `docs/antrag.md`
- **Ist:** Antrag beschreibt Wetterdaten inkl. Qualitaetsvergleich, Umsetzung wirkt aktuell generisch.
- **Risiko:** Inkonsistenz zwischen Antrag und Implementierung.
- **To-do (empfohlen):**
  - Indexe fachlich umbenennen:
    - `weather-raw-*`
    - `weather-processed-*`
    - `weather-compare-*` (optional zuerst nur `processed`)
    - `stations-meta` (optional)
  - `ES_INDEX`/`ES_ALIAS` anpassen (z. B. `weather-processed-2026`, `weather-all`)
  - Felder in `preprocess.py` auf Wetterdaten ausrichten (`temp`, `humidity`, `pressure`, `qc_flags`)

### C) Pflicht/nah an Pflicht: Mapping-Optimierung (bewertungsrelevant)
- **Ist:** Minimales Mapping ohne Analyzer/Normalizer/Subfields.
- **Risiko:** Bewertungsrelevante Anforderungen (Analyzer/Tokenizer/Normalizer) nicht sichtbar.
- **To-do (Minimalversion):**
  - Textfelder mit Subfields:
    - `field` als `text`
    - `field.keyword` als `keyword` (term/sort/aggs)
    - optional `field.sort` mit lowercase-normalizer
  - Autocomplete via `search_as_you_type` oder `edge_ngram`
  - In `db/elastic/index-template.json` umsetzen

### D) Sinnvoll: Shard-Konzept sichtbarer machen
- **Ist:** `number_of_shards = 1`
- **To-do (optional):**
  - Hauptindex auf 2-3 Primaries setzen (`replica=1` beibehalten)
  - Als Demo fuer Verteilung/Parallelisierung begruenden

### E) Sinnvoll + pruefungsfest: Nachweis-Queries ausbauen
- **Ist:** `post_checks.py` zeigt Basischecks.
- **To-do:**
  - `term`-Query auf `keyword`-Feld (z. B. `source`, `station_id`)
  - Dokumentabruf per `_doc/<id>` anhand `doc_id`
  - Wetterbezogen statt `match` eher:
    - `range` (letzte 24h, Temperaturbereich)
    - `date_histogram` (pro Stunde/Tag)
    - Kennzahlen: `avg(temp)`, `max(delta)`, `missing_rate`

### F) Pflichtnah: Dokumentation/Runbook vervollstaendigen
- **Ist:** README ist nutzbar, aber knapp.
- **To-do:**
  - Quellen (Name/URL) dokumentieren
  - Intervall (`daily`/`hourly`) und Begruendung angeben
  - Datenmodell (`raw` vs. `processed`) erklaeren
  - Reproduktionsablauf dokumentieren (`docker compose up`, optional Airflow Trigger, erwartete Outputs)
  - Klarstellen: keine manuellen Schritte, alles per Skripten

## Statusuebersicht

### Fertig / Nachweisbar
- [x] 3-Node Elasticsearch-Cluster mit Persistenz (`GREEN`, Shards verteilt)
- [x] Airflow in Compose, DAG vorhanden, periodischer Schedule
- [x] Raw-/Processed-Layer vorhanden
- [x] Externe Vorverarbeitung + idempotentes Bulk-Loading
- [x] ES-Infrastruktur als Code (Template, Pipeline, Alias)
- [x] Post-Checks inkl. Aggregation

### Offen / Muss ergaenzt werden
- [ ] Echte Datenabgriffe (Wetterstation + Referenzquelle)
- [ ] Konsistente Benennung und Schema laut Wetter-Antrag
- [ ] Analyzer/Normalizer/Autocomplete/Sortfelder im Mapping
- [ ] Erweiterte Nachweis-Queries (`term`, `_doc`, `range`, `date_histogram`)
- [ ] Optional: Mehr Primaries fuer bessere Shard-Demo
- [ ] Dokumentation: Quellen, Entscheidungen, reproduzierbarer Ablauf

## Konkreter Arbeitsplan (minimal und sinnvoll)
1. `fetch_raw.py` auf echte API(s) umbauen, Rohdaten unveraendert speichern.
2. `preprocess.py` auf Wetter-Schema + `qc_flags` umstellen.
3. `db/elastic/index-template.json` um Mapping/Normalizer/Autocomplete erweitern.
4. `post_checks.py` um `_doc`, `term`, `range`, `date_histogram`, Kennzahlen erweitern.
5. README mit Quellen, Intervall, Ablauf und Erwartungswerten aktualisieren.
