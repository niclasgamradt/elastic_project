# Projektüberblick

Dieses Projekt implementiert eine vollständige Data-Engineering-Pipeline zur
periodischen Erfassung, Vorverarbeitung und Speicherung von Wetterdaten
in einem 3-Node-Elasticsearch-Cluster.

## Architektur (High-Level)

Airflow orchestriert:
Fetch → Raw → Preprocess → Bulk-Load → Post-Checks

Datenquellen:
- BrightSky API
- HS-Worms Wetterstation API

Speicherung:
- Elasticsearch (3 Nodes, Alias-basiert)

Ziel:
Reproduzierbare, containerisierte End-to-End-Datenpipeline.
