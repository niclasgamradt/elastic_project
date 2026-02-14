# Elasticsearch Index Design

Die Elasticsearch-Konfiguration erfolgt automatisiert und reproduzierbar über:

- `db/elastic/index-template.json`
- `db/elastic/aliases.json`
- `db/elastic/ingest-pipeline.json`
- `scripts/apply_es.py`

Das Projekt verwendet ein **provider-unabhängiges Kernschema**.  
Alle APIs werden im `preprocess_*`-Schritt auf dieses Schema normalisiert.  
Provider-spezifische Felder werden nicht indexiert.

Die Ingestion erfolgt ausschließlich über den Alias `all-data`.

## Index Template

### Settings

Das Template definiert die grundlegenden Index-Einstellungen:

- `number_of_shards`
- `number_of_replicas`
- `refresh_interval`

Während der Bulk-Ingestion wird `refresh_interval` temporär auf `-1` gesetzt und anschließend wieder auf `1s` zurückgestellt.

### Mapping

Das Projekt verwendet ein fest definiertes Kernschema.

```json
{
  "dynamic": false
}
```

Bedeutung von `dynamic: false`:

- Zusätzliche Felder werden beim Indexieren ignoriert.
- Das Mapping wächst nicht dynamisch.
- Das Schema bleibt stabil und kontrollierbar.
- Neue APIs erfordern keine Template-Anpassung, solange sie das Kernschema befüllen.

#### Aktuelles Kernschema

**Identifikationsfelder**

- `doc_id` (`keyword`)
- `provider` (`keyword`)
- `source_id` (`keyword`)
- `timestamp` (`date`)
- `processed_at` (`date`)

**Meteorologische Messwerte**

- `temperature` (`float`)
- `relative_humidity` (`integer`)
- `dew_point` (`float`)
- `pressure_msl` (`float`)
- `precipitation` (`float`)
- `wind_speed` (`float`)
- `wind_direction` (`integer`)
- `wind_gust_speed` (`float`)
- `wind_gust_direction` (`integer`)
- `cloud_cover` (`integer`)
- `sunshine` (`float`)
- `visibility` (`integer`)
- `condition` (`keyword`)
- `icon` (`keyword`)
- `solar` (`float`)

Alle Felder sind optional. Fehlende Werte werden als `null` gespeichert.

#### String-Felder: `text` vs. `keyword`

Im aktuellen Projekt werden ausschließlich `keyword`-Felder für String-Werte verwendet, da:

- keine Volltextsuche erforderlich ist
- Filter- und Aggregationsabfragen im Vordergrund stehen

`text`-Felder werden im Kernschema nicht verwendet.

#### Numerische Felder

Numerische Messwerte werden als:

- `float` (z. B. Temperatur, Windgeschwindigkeit)
- `integer` (z. B. Windrichtung, Luftfeuchtigkeit)

definiert, um Aggregationen und Range-Queries zu ermöglichen.

#### Date-Felder

Zeitstempel (`timestamp`, `processed_at`) sind als `date` typisiert.  
Es wird das ISO-8601-Format in UTC verwendet.

## Alias-Konfiguration (`aliases.json`)

### Zweck

Ein Alias ist ein logischer Name, der auf einen oder mehrere physische Indizes verweist.

Im Projekt wird ausschließlich der Alias `all-data` verwendet.

### Aktuelle Konfiguration

```json
{
  "actions": [
    { "add": { "index": "data-2026", "alias": "all-data", "is_write_index": true } },
    { "add": { "index": "data-archive", "alias": "all-data" } }
  ]
}
```

### Bedeutung der Felder

- `index`: Konkreter physischer Indexname.
- `alias`: Logischer Name für Lese- und Schreiboperationen.
- `is_write_index`: Definiert den aktiven Zielindex für Schreiboperationen.

### Funktion im Projekt

Der Alias `all-data`:

- bündelt mehrere Indizes
- dient als zentrales Schreibziel in `load_to_es.py`
- ermöglicht spätere Index-Rotation ohne Codeänderung

Bulk-Ingestion erfolgt immer gegen den Alias, nicht gegen einen festen Indexnamen.

### Vorteile

- Entkopplung von Anwendung und Indexnamen
- Unterstützung von Index-Rotation
- Vereinfachte Abfragen über mehrere Indizes
- Trennung von aktivem und archiviertem Datenbestand

## `apply_es.py`

`apply_es.py` initialisiert und konfiguriert den Elasticsearch-Cluster vollständig automatisiert.

Das Skript:

- registriert das Index-Template
- registriert die Ingest-Pipeline
- erstellt die benötigten Indizes (`data-2026`, `data-archive`)
- setzt die Alias-Konfiguration (inklusive Write-Index)
- führt eine grundlegende Cluster-Health-Prüfung durch

Bereits existierende Indizes können eine `resource_already_exists_exception` erzeugen.  
Dieses Verhalten ist erwartbar und beeinträchtigt die Funktion nicht.

## `index-template.json`

### Zweck

`index-template.json` definiert das verbindliche Index-Template des Projekts.

Es legt fest:

- Index-Settings
- das Kern-Mapping
- die Schema-Strategie (`dynamic: false`)

Neue Indizes mit Pattern:

- `data-*`
- `processed-*`

übernehmen automatisch diese Konfiguration.

### Rolle in der Pipeline

- `apply_es.py` registriert das Template.
- Der Zielindex (`data-2026`) wird erstellt.
- `load_to_es.py` schreibt über den Alias.
- Das Template garantiert konsistente Typisierung.

## `ingest-pipeline.json`

Die Datei `db/elastic/ingest-pipeline.json` definiert eine Elasticsearch-Ingest-Pipeline.  
Sie wird durch `apply_es.py` automatisch im Cluster registriert.

Die Pipeline wird beim Bulk-Import über folgendes Endpoint aktiviert:

```http
POST /_bulk?pipeline=standardize-v1
```

### Aktuelle Prozessoren

- `date`: Normalisiert das Feld `timestamp`.
- `set`: Setzt `processed_at` auf `_ingest.timestamp`.

Die Pipeline enthält keine fachliche Transformationslogik.  
Fachliche Normalisierung erfolgt ausschließlich im `preprocess_*`-Schritt.

## Architekturprinzip

- Rohdaten -> `fetch_*`
- Normalisierung -> `preprocess_*`
- Indexnahe Standardisierung -> Ingest-Pipeline
- Speicherung -> Zielindex über Alias

Dieses Design ermöglicht:

- reproduzierbare Cluster-Konfiguration
- provider-unabhängiges Schema
- kontrollierte Mapping-Strategie
- skalierbare Integration weiterer APIs
