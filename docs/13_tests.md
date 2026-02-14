# Testdokumentation – Weather Data Pipeline

Diese Dokumentation beschreibt die implementierten Unit- und Integrationstests
für die Weather Data Pipeline (Airflow + Elasticsearch).

Ziel der Tests ist die technische Absicherung von:

- Kernschema-Konsistenz
- Idempotenz
- Mapping-Stabilität
- Alias-Konfiguration
- Bulk-Fehlerbehandlung
- Query-Fähigkeit

---
# Testausführung

Die Tests werden mit **pytest** in einer virtuellen Python-Umgebung ausgeführt.

## Umgebung vorbereiten

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip pytest
```

Tests ausführen

Alle Tests:

```bash
pytest -q
```
Einzelner Test:

```bash
pytest tests/test_dateiname.py -q
```
Voraussetzung für Integrationstests

Elasticsearch muss laufen:
```bash
curl http://localhost:9200/_cluster/health?pretty
```

---

# 1. Unit-Tests

## 1.1 Preprocess – Kernschema (HS-Worms)

**Datei:**  
`test_preprocess_hs_worms_core_schema.py`

**Zweck:**
- Sicherstellen, dass `preprocess_hs_wetter.py` nur Felder des definierten Kernschemas erzeugt.
- Überprüfung, dass kein API-spezifisches Feld ins finale Dokument gelangt.
- Validierung von `doc_id`, `timestamp` und `provider`.

**Bedeutung:**
Garantiert Schema-Stabilität bei Erweiterung um weitere APIs.

---

## 1.2 Preprocess – Kernschema (BrightSky)

**Datei:**  
`test_preprocess_brightsky_core_schema.py`

**Zweck:**
- Verifikation, dass BrightSky-Daten korrekt normalisiert werden.
- Sicherstellung, dass alle erwarteten Kernfelder vorhanden sind.
- Typische Wetterfelder sind korrekt gesetzt.

**Bedeutung:**
Validiert die Vereinheitlichung mehrerer Datenquellen.

---

## 1.3 Bulk-Body Builder

**Datei:**  
`test_load_to_es_bulk_body.py`

### Test 1 – Gültige NDJSON-Struktur
- Prüft korrekte Action-/Document-Paare.
- Validiert `_id`-Verwendung.
- Sicherstellung gültiger NDJSON-Formatierung.

### Test 2 – Fail-Fast bei fehlender `doc_id`
- Erwartet `ValueError`, wenn `doc_id` fehlt.
- Verhindert stillen Datenverlust.

**Bedeutung:**
Garantiert korrekte Idempotenz-Mechanik.

---

## 1.4 Bulk-Response Parser

**Datei:**  
`test_load_to_es_parse_bulk_response.py`

**Testfälle:**
- Erfolgreiche Bulk-Response (`errors=false`)
- Leere Response (Fehlerfall)
- `errors=true` mit Item-Fehler
- `errors=true` ohne Item-Details

**Bedeutung:**
Stellt robustes Fehlerhandling im Loader sicher.

---

## 1.5 Processed-File-Selektion

**Datei:**  
`test_load_to_es_processed_files_for_run.py`

**Zweck:**
- Lädt nur Dateien mit passendem `run_id`.
- Fallback ohne `run_id` lädt nur neueste Datei.
- Fehler bei fehlenden Dateien.

**Bedeutung:**
Verhindert falsche oder doppelte Ingestion.

---

# 2. Integrationstests (gegen Elasticsearch)

## 2.1 Idempotenz-Test

**Datei:**  
`test_integration_idempotent_load.py`

**Zweck:**
- Lädt denselben `run_id` zweimal.
- `_count` darf sich beim zweiten Lauf nicht erhöhen.

**Bedeutung:**
Beweist funktionierende deterministische `_id`-Strategie.

---

## 2.2 Alias- und Write-Index-Prüfung

**Datei:**  
`test_integration_alias_and_mapping.py`

**Zweck:**
- Verifiziert, dass `all-data` existiert.
- `data-2026` ist `is_write_index=true`.
- Keine HS-Spezialfelder im Mapping.

**Bedeutung:**
Sichert Alias-Architektur und Mapping-Stabilität.

---

## 2.3 Query-/Aggregation-Smoke-Test

**Datei:**  
`test_integration_queries_smoke.py`

**Zweck:**
- Terms-Aggregation nach `provider`
- Average-Aggregation auf `temperature`

**Bedeutung:**
Beweist korrekte Mapping-Typisierung und Query-Fähigkeit.

---

## 2.4 dynamic:false Schutz

**Datei:**  
`test_integration_dynamic_false_protection.py`

**Zweck:**
- Dokument mit unbekanntem Feld indexieren.
- Feld darf nicht im Mapping erscheinen.
- Feld darf nicht suchbar sein.

**Bedeutung:**
Verhindert unkontrollierte Schema-Erweiterung.

---

## 2.5 Bulk-Negativtest (Mapping-Konflikt)

**Datei:**  
`test_integration_bulk_fails_on_item_error.py`

**Zweck:**
- Absichtlicher Typkonflikt (`temperature` als String).
- Bulk-Response muss `errors=true` liefern.

**Bedeutung:**
Validiert korrektes Fehlerverhalten bei Mapping-Verletzungen.

---

# 3. Testabdeckung (Fachlich)

Die Tests decken folgende Aspekte der Pipeline ab:

- Datenmodell-Konsistenz
- Idempotenz der Ingestion
- Mapping-Kontrolle (`dynamic=false`)
- Alias-Architektur
- Fehlerbehandlung im Bulk-Prozess
- Aggregationsfähigkeit der Messdaten

---

# 4. Einordnung im Projekt

Die Tests unterstützen:

- Reproduzierbarkeit (Infrastructure as Code)
- Produktionsnähe
- Technische Robustheit
- Wartbarkeit bei API-Erweiterung
- Nachweisbare Datenqualität

Sie bilden eine vollständige technische Absicherung
für eine containerisierte, alias-basierte Elasticsearch-Datenpipeline.
