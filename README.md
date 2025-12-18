# elastic_project

Pipeline: Daten holen -> lokal vorbereiten -> nach Elasticsearch laden.

## Ordner
- dags/          Airflow (Schedule)
- scripts/       Python: fetch / preprocess / load / checks
- data/raw/      Rohdaten (unverändert)
- data/processed/ fertige Daten (z. B. NDJSON)
- db/elastic/    ES-Settings als Code (template, mappings, alias, pipeline)
- docs/          kurze Notizen/Entscheidungen

## Ablauf
1) fetch_raw: Quelle abrufen -> data/raw/
2) preprocess: normalisieren + timestamps + cleaning + doc_id -> data/processed/
3) load_to_es: bulk import nach ES (idempotent über _id = doc_id)
4) post_checks: health + count + test query

## Regeln
- keine Klick-Konfig in Kibana
- alles über Dateien/Skripte im Repo
- Rohdaten bleiben liegen (reprocessing möglich)

