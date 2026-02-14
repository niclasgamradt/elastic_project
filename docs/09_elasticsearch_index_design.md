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


