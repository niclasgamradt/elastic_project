# Pipeline

## Orchestrierung
Airflow DAG: scrape_and_load

## Task-Reihenfolge
apply_es →
fetch_brightsky / fetch_hs →
preprocess_brightsky / preprocess_hs →
load_to_es →
post_checks

## Run-ID Konzept
Dateibenennung:
raw_<run_id>__provider.json
processed_<run_id>__provider.ndjson


# load_to_es.py

## Zweck

`load_to_es.py` lädt die vorverarbeiteten NDJSON-Dateien (`data/processed/*.ndjson`) in den Elasticsearch-Cluster.  
Es bildet den finalen Schritt der Datenpipeline zwischen Preprocessing und persistenter Speicherung.

---

## Rolle in der Pipeline

Ablauf der gesamten Pipeline:

fetch_* → preprocess_* → load_to_es → post_checks

- `fetch_*`: Abruf externer Wetterdaten
- `preprocess_*`: Normalisierung und Schemaangleichung
- `load_to_es`: Bulk-Ingestion in Elasticsearch
- `post_checks`: Validierung und Beispielabfragen

---

## Dateiauswahl pro Run

Das Skript unterstützt Airflow-Runs mit `run_id`.

Namensschema:

processed_<run_id>__<provider>.ndjson

Beispiel:

processed_2026-02-12__brightsky.ndjson  
processed_2026-02-12__hs-worms.ndjson  

Falls keine `run_id` übergeben wird, wird die neueste `processed_*.ndjson` geladen.

---

## Bulk-API Nutzung

Die Dokumente werden über die Elasticsearch Bulk-API geladen:

POST /_bulk?pipeline=standardize-v1

Merkmale:

- NDJSON-Format
- Chunk-Verarbeitung (CHUNK_SIZE)
- Nutzung einer Ingest-Pipeline
- effiziente Mehrfach-Indexierung

---

## Idempotentes Schreiben

Jedes Dokument besitzt:

"_id": doc_id

Dadurch:

- keine Duplikate
- erneute Runs überschreiben bestehende Dokumente
- reproduzierbare Ingestion möglich

---

## Performance-Optimierung

Während des Bulk-Vorgangs wird:

refresh_interval = -1

gesetzt, um unnötige Refreshes zu vermeiden.

Nach Abschluss:

- refresh_interval wird zurückgesetzt
- _refresh wird explizit ausgeführt

Dies verbessert die Schreibperformance deutlich.

---

## Fehlerbehandlung

Das Skript prüft:

- HTTP-Statuscodes
- Bulk-Response auf "errors"
- erstes fehlerhaftes Item

Bei Fehlern wird der Prozess kontrolliert abgebrochen.





# post_checks.py

## Zweck

`post_checks.py` führt nach dem Bulk-Import eine technische Validierung der geladenen Daten im Elasticsearch-Cluster durch.

Es überprüft:

- Erreichbarkeit des Clusters
- Anzahl der gespeicherten Dokumente
- Abrufbarkeit der Daten über `_search`
- einfache Aggregationen

---

## Durchgeführte Prüfungen

1. Cluster Health  
   GET /_cluster/health  
   Prüft Status und Node-Anzahl.

2. Dokumentanzahl  
   GET /<alias>/_count  
   Verifiziert, dass Dokumente erfolgreich geschrieben wurden.

3. Beispiel-Suche  
   `_search` mit Sortierung nach `timestamp` (desc).  
   Gibt die zuletzt indexierten Dokumente zurück.

4. Aggregation  
   Terms-Aggregation (z. B. nach `provider`).  
   Prüft Funktionalität von Keyword-Feldern und Aggregationen.

---

## Rolle in der Pipeline

fetch_* → preprocess_* → load_to_es → post_checks

`post_checks` ist der finale Validierungsschritt nach der Ingestion.
