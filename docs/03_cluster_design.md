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
- Ziel: Redundanz + Parallelisierung
