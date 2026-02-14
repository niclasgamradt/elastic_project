# Index Template

## Settings
- number_of_shards
- number_of_replicas
- refresh_interval

## Mapping
- text vs keyword
- numerische Felder
- date Felder

## Alias
- all-data als Write-Target


## apply_es.py

`apply_es.py` initialisiert und konfiguriert den Elasticsearch-Cluster vollständig automatisiert.

Dieses Skript:

- legt das Index-Template an (Settings und Mapping)
- erstellt die Ingest-Pipeline (sofern definiert)
- erzeugt die benötigten Indizes (idempotent)
- setzt die Alias-Konfiguration (inkl. Write-Index)
- führt eine grundlegende Cluster-Health-Prüfung durch


# aliases.json

## Header für die Datei (Beispiel)

Da JSON offiziell keine Kommentare unterstützt, kann man einen dokumentarischen Hinweis oberhalb der Datei oder in der Doku platzieren.

Beispiel für einen Header-Kommentar (nicht produktiv verwenden):

{
  "_comment": "Defines Elasticsearch alias configuration. Applied automatically by apply_es.py during cluster initialization."
}

---

## Zweck

aliases.json definiert die Alias-Konfiguration für den Elasticsearch-Cluster.

Ein Alias ist ein logischer Name, der auf einen oder mehrere physische Indizes verweist.  
Er ermöglicht es, Indexnamen vom Anwendungscode zu entkoppeln.

---

## Beispielkonfiguration

{
  "actions": [
    { "add": { "index": "data-2024", "alias": "all-data", "is_write_index": true } },
    { "add": { "index": "data-archive", "alias": "all-data" } }
  ]
}

---

## Bedeutung der Felder

index  
Konkreter physischer Indexname.

alias  
Logischer Name, unter dem ein oder mehrere Indizes zusammengefasst werden.

is_write_index  
Legt fest, welcher Index bei Schreiboperationen verwendet wird.

---

## Funktion im Projekt

Der Alias "all-data":

- bündelt mehrere Indizes
- dient als zentrales Schreibziel in load_to_es.py
- erlaubt spätere Index-Rotation ohne Codeänderung

Die Bulk-Ingestion erfolgt immer gegen den Alias, nicht gegen einen festen Index.

---

## Vorteile

- Entkopplung von Anwendung und Indexnamen  
- Unterstützung von Index-Rotation  
- Vereinfachte Abfragen über mehrere Indizes  
- Trennung von aktivem und archiviertem Datenbestand  

---

## Rolle in der Pipeline

apply_es.py setzt die Alias-Konfiguration automatisch beim Start.

Alle weiteren Komponenten (Ingestion, Abfragen, Post-Checks) greifen ausschließlich auf den Alias zu.


# index-template.json

## Zweck

index-template.json definiert das Elasticsearch Index-Template für das Projekt.

Ein Index-Template legt fest:

- Settings (z. B. Shards, Replicas, refresh_interval)
- Mapping (Datentypen der Felder)
- optionale Analyzer oder Normalizer

Es wird automatisch von apply_es.py beim Start angewendet.

---

## Funktion im Projekt

Das Template sorgt dafür, dass alle Indizes mit Muster:

data-*  
processed-*  

ein einheitliches Schema erhalten.

Neue Indizes, die diesem Pattern entsprechen, übernehmen automatisch die definierten Einstellungen und Mappings.

---

## Beispielstruktur

{
  "index_patterns": ["data-*", "processed-*"],
  "template": {
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 1,
      "refresh_interval": "1s"
    },
    "mappings": {
      "properties": {
        "doc_id": { "type": "keyword" },
        "provider": { "type": "keyword" },
        "timestamp": { "type": "date" },
        "temperature": { "type": "float" }
      }
    }
  }
}

---

## Bedeutung der wichtigsten Einstellungen

number_of_shards  
Anzahl der Primary Shards pro Index.  
Beeinflusst Parallelisierung und Skalierung.

number_of_replicas  
Anzahl der Replica Shards.  
Erhöht Ausfallsicherheit und Leseskalierung.

refresh_interval  
Intervall, in dem neue Dokumente suchbar werden.

---

## Mapping

Das Mapping definiert Datentypen, z. B.:

keyword  
Nicht analysierter String. Geeignet für:
- Filter
- term-Queries
- Aggregationen
- Sortierung

text  
Analyzierter String. Geeignet für Volltextsuche.

date  
Zeitstempel im ISO-8601-Format.

float / integer  
Numerische Felder für Messwerte.

---

## Vorteile eines Templates

- Einheitliches Schema über alle Indizes
- Vermeidung dynamischer Mapping-Fehler
- Reproduzierbare Index-Struktur
- Keine manuelle Konfiguration in Kibana

---

## Rolle in der Pipeline

apply_es.py lädt das Template vor dem Erstellen der Indizes.

load_to_es.py schreibt Daten anschließend in Indizes, die dieses Template automatisch verwenden.




# ingest-pipeline.json

Die Datei `db/elastic/ingest-pipeline.json` definiert eine **Elasticsearch Ingest Pipeline**.  
Sie wird beim Setup durch `apply_es.py` automatisch im Cluster registriert.

Eine Ingest-Pipeline verarbeitet Dokumente **beim Indexieren** und kann Felder:

- transformieren  
- berechnen  
- umbenennen  
- validieren  
- normalisieren  

Die Pipeline wird beim Bulk-Import über den Parameter  
`?pipeline=standardize-v1` aktiviert.

---

## Zweck im Projekt

Die Ingest-Pipeline übernimmt einfache Standardisierungen direkt im Cluster, z. B.:

- Vereinheitlichung von Feldnamen  
- Setzen von Default-Werten  
- Konvertierungen (z. B. Typanpassungen)  
- Ergänzung technischer Metadaten  

Damit bleibt:

- `preprocess_*.py` für fachliche Transformation zuständig  
- Elasticsearch für indexnahe technische Verarbeitung zuständig  

---

## Architekturprinzip

1. Rohdaten → `fetch_*`
2. Normalisierung → `preprocess_*`
3. Indexnahe Standardisierung → **Ingest Pipeline**
4. Speicherung → Zielindex (über Alias)

Die Pipeline ist Teil des Infrastructure-as-Code-Konzepts und wird reproduzierbar über `apply_es.py` angelegt.

---

## Dokumentationsverweis

Details zur Pipeline-Konfiguration befinden sich in:

`docs/08_elasticsearch_configuration.md`
