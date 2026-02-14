# Architektur

## Infrastruktur
- Docker Compose Setup
- Elasticsearch Cluster (es01, es02, es03)
- Airflow (Scheduler, Worker, CeleryExecutor)
- Postgres + Redis

## Cluster-Konzept
- Primary + Replica Shards
- Alias als Write-Target
- Persistente Volumes

Ziel: Skalierung, Redundanz, Nachvollziehbarkeit.


### Python-Paketstruktur

Der Ordner `scripts/` enthält eine Datei `__init__.py`.  
Diese kennzeichnet das Verzeichnis als Python-Package und ermöglicht
Imports wie:

from scripts.load_to_es import main

Ohne `__init__.py` könnten die Module im Ordner nicht sauber
innerhalb von Airflow oder anderen Skripten importiert werden.


## config.py

`config.py` stellt die zentrale Konfigurationsbasis des Projekts dar.

Es definiert:

- Projektverzeichnisse (`data/raw`, `data/processed`)
- Elasticsearch-URL, Index-Name und Alias
- Dateinamenskonventionen für Raw- und Processed-Daten

Die Konfiguration wird über eine `Settings`-Klasse kapselt und
als globale Instanz (`SETTINGS`) bereitgestellt.

Ziel ist eine konsistente, zentrale Verwaltung aller
projektweiten Parameter ohne Hardcoding in einzelnen Skripten.
