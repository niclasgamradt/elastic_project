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
