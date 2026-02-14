# Deployment

## Voraussetzungen
- Debian/Linux
- Docker
- Docker Compose
- Python (venv optional)

## Start
docker compose up -d

## Wichtige Befehle
- docker compose build
- docker compose up --build
- docker compose down

## Persistenz
Elasticsearch-Daten werden über Docker Volumes gespeichert.


# .env.example

## Zweck

Die Datei `.env.example` definiert alle konfigurierbaren Umgebungsvariablen für das Projekt.

Sie dient als Vorlage für eine lokale `.env`-Datei und steuert:

- Elasticsearch-Cluster-Konfiguration
- Airflow-Sicherheit und Authentifizierung
- Heap-Größe und Cluster-Parameter
- Wetterdatenquellen und API-Einstellungen

Docker Compose liest die `.env`-Datei automatisch beim Start.

---

## Elasticsearch-Konfiguration

ES_VERSION  
Version des Elasticsearch-Docker-Images.

CLUSTER_NAME  
Name des Elasticsearch-Clusters.

ES_HEAP  
Heap-Größe pro Node (z. B. 1g, 2g).

---

## Airflow-Konfiguration

AIRFLOW_UID  
Container-User-ID (wichtig für Dateirechte unter Linux).

AIRFLOW__CORE__FERNET_KEY  
Verschlüsselungsschlüssel für Airflow-Verbindungen.

AIRFLOW__API_AUTH__JWT_SECRET  
JWT-Secret für API-Authentifizierung.

AIRFLOW__API__SECRET_KEY  
Allgemeiner Secret-Key für Airflow.

AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_USERS  
Benutzerdefinition für SimpleAuthManager.

AIRFLOW__CORE__SIMPLE_AUTH_MANAGER_PASSWORDS_FILE  
Pfad zur Passwort-Datei im Container.

---

## Wetterdaten-Konfiguration

WEATHER_PROVIDER  
Standard-Datenquelle (z. B. brightsky).

WORMS_LAT  
Breitengrad für API-Anfragen.

WORMS_LON  
Längengrad für API-Anfragen.

BRIGHTSKY_BASE  
Basis-URL der BrightSky-API.

BRIGHTSKY_DATE_MODE  
Steuert, wie das Datum übergeben wird (z. B. daily, hourly).

HS_WETTER_URL  
API-Endpoint der Hochschul-Wetterstation.

---

## Nutzung

1. Datei kopieren:

   cp .env.example .env

2. Werte anpassen.

3. Infrastruktur starten:

   docker compose up

Die Konfiguration ist vollständig externalisiert und ermöglicht reproduzierbare Deployments ohne Codeänderung.
