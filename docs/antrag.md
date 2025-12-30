## 1. Projekttitel
**Qualitätssicherung und Vergleichsanalyse: Hochschul-Wetterstation vs. externe Wetterstationen**

## 2. Ausgangslage / Motivation
An der Hochschule existiert eine Wetterstation mit API-Zugriff. Einzelmessungen sind jedoch nur begrenzt aussagekräftig, solange keine Referenz gegenüber offiziellen oder anderen offenen Wetterstationen besteht. Ziel ist eine reproduzierbare Datenpipeline, die Messdaten regelmäßig erfasst, bereinigt, versioniert speichert und systematisch mit Referenzdaten vergleicht.

## 3. Zielsetzung
- Periodische Erfassung der Hochschul-Wetterstationsdaten über die vorhandene API.
- Ergänzende Erfassung von Referenzdaten (z. B. 1–3 externe Wetterstationen / offene Wetterdaten).
- Einheitliche Vorverarbeitung (Schema, Datentypen, Zeitzonen, Einheiten) und Deduplikation.
- Speicherung der normalisierten Daten in Elasticsearch.
- Berechnung und Speicherung von Vergleichskennzahlen (z. B. Abweichung/Bias, Missing-Rate, einfache Qualitätsflags).
- Nachweis der Nutzbarkeit durch wenige Beispielabfragen/Aggregationen (keine umfangreiche Data-Science-Analyse).

## 4. Scope / Abgrenzung
Im Fokus steht Data Engineering (Pipeline, Datenmodell, Speicherung, Automatisierung, Reproduzierbarkeit). Eine Visualisierung oder tiefgehende statistische Modellierung ist optional und nicht Kernbestandteil.

## 5. Datenquellen
- **Primärquelle:** Hochschul-Wetterstation (API)
- **Referenzquellen:** offene Wetterdaten (z. B. DWD-nahe Stationen oder vergleichbare offene Quellen)
- **Metadaten:** Stationen (Koordinaten, Höhe, Sensortyp, Quelle)

## 6. Technischer Ansatz (Architektur)
### 6.1 Ingestion / Scheduling
- Orchestrierung über **Apache Airflow** (z. B. stündlich oder täglich)
- Fehlerbehandlung mit Retries und Logging

### 6.2 Raw Layer
- Speicherung der unveränderten Rohdaten (JSON) zur Reproduzierbarkeit und für Debugging/Reprocessing

### 6.3 Externe Vorverarbeitung (Python)
- Normalisierung auf ein einheitliches Schema (Feldnamen, Datentypen)
- Timestamp-Parsing und Zeitzonen-Normalisierung (UTC)
- Einheiten-Konvertierung (falls notwendig)
- Deduplikation über deterministische Dokument-IDs (`_id`)
- Qualitätschecks (Range-Checks, Missing-Flags, einfache Sprungdetektion)

### 6.4 Speicherung / Optimierung (Elasticsearch)
- Deployment als **3-Node-Cluster** via Docker Compose
- Index-Templates, Mappings, Aliases und optional Pipelines **als Code**
- Bulk-Ingest mit (temporärer) Optimierung von `refresh_interval` während großer Loads

## 7. Datenmodell (grobe Indizes)
- `weather-raw-*` (optional): Rohdaten je Quelle
- `weather-processed-*`: normalisierte Messwerte + QC-Flags
- `stations-meta`: Station-Metadaten
- `weather-compare-*`: Vergleichsergebnisse (z. B. `delta_temp`, `mae_24h`, Missing-Rate)

## 8. Deliverables
- Git-Repository mit vollständigem Setup „as code“ (Docker Compose, Airflow DAGs, Skripte, Index-Templates)
- Reproduzierbarer Pipeline-Lauf inkl. Rohdatenablage und Bulk-Ingest
- Dokumentation der Designentscheidungen (Schema, `_id`, Shards/Replicas, Aliase, QC-Regeln)
- Smoke-Tests (Cluster Health, `_count`, Beispielquery, Beispielaggregation)
- Kurze Demo-Abfragen (z. B. Abweichung pro Tag, Ausfallzeiten, Top-Abweichungen)
