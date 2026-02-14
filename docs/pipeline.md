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

Ziel: Deterministische Reproduzierbarkeit.
