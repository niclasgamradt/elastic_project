# Cluster Design

## Aufbau
- 3-Node Elasticsearch Cluster (es01, es02, es03)
- Docker Compose Orchestrierung
- Persistente Volumes

## Node-Rollen
- Master
- Data
- Ingest

## Shard-Konzept
- Primary + Replica
- Verteilung über Nodes


# docker-compose.yml

## Zweck

Die `docker-compose.yml` definiert die vollständige Laufzeitumgebung des Projekts.

Sie orchestriert:

- einen 3-Node Elasticsearch-Cluster
- einen vollständigen Airflow-Stack (API, Scheduler, Worker, Triggerer)
- Postgres als Airflow-Metadatenbank
- Redis als Celery-Broker
- persistente Volumes für Daten und Logs

Das Setup ist vollständig reproduzierbar und benötigt keine manuelle Konfiguration.

---

## Architekturüberblick

### Elasticsearch

- 3 Nodes: `es01`, `es02`, `es03`
- gemeinsames Cluster (`cluster.name`)
- automatische Node-Discovery
- persistente Datenhaltung über Docker Volumes
- Healthcheck bis mindestens `yellow`

Ziel: Redundanz, Shard-Verteilung und Cluster-Prinzip demonstrieren.

---

### Airflow

Executor: `CeleryExecutor`

Komponenten:

- `airflow-api-server`
- `airflow-scheduler`
- `airflow-dag-processor`
- `airflow-triggerer`
- `airflow-worker`

Airflow bindet das Projektverzeichnis ein:

- Host: `./`
- Container: `/opt/airflow/project`

Dadurch sind im Container direkt verfügbar:

- `dags/`
- `scripts/`
- `db/`
- `data/`

---

### Abhängigkeiten

Postgres:

- speichert Airflow-Metadaten

Redis:

- Celery-Broker für Task-Verteilung

Beide Services besitzen Healthchecks und werden vor Airflow gestartet.

---

## Persistenz

Elasticsearch:

- `esdata01`
- `esdata02`
- `esdata03`

Airflow:

- `airflow_postgres`
- `airflow_logs`
- `airflow_config`
- `airflow_plugins`

Daten bleiben beim Container-Neustart erhalten.

