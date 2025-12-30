Du:
welches projekt kann man in einem team als vier leute durchführen
ChatGPT:

Ein Teamprojekt zu viert sollte so geschnitten sein, dass jede Person ein klar abgegrenztes Teilpaket verantwortet und ihr am Ende ein integriertes, lauffähiges System habt. Realistisch funktionieren Projekte am besten, die Datenpipeline + Speicherung + API/Analyse + Deployment/Monitoring kombinieren.
Option 1: End-to-End Data-Engineering-Pipeline (Scraping → Processing → Elasticsearch)

Passt sehr gut zu eurem bestehenden Kontext.

Aufgabe: Regelmäßig Daten aus 1–2 Quellen sammeln (RSS/HTML/API), extern vorverarbeiten (Cleaning, Normalisierung, Deduplikation), in Elasticsearch speichern, dann eine kleine Demo-Analyse/Query-UI liefern.

Rollen (4 Personen):

    Ingestion & Scheduling: Airflow DAGs, Retries, Logging, Rohdaten-Layer

    Preprocessing: Schema, Timestamp/Timezone, Deduplikation (_id Hash), Enrichment

    Elasticsearch & Index-Design: Templates, Mappings, Aliases, Shards/Replicas, Pipelines

    Demo + QA/Monitoring: Smoke Tests, _cluster/health Checks, Beispiel-Queries, Doku

Ergebnis: Reproduzierbares „Alles als Code“-Projekt (Docker Compose + Skripte + DAGs).
Option 2: Preis-/Verfügbarkeitsmonitor (E-Commerce/Tech-Produkte) mit Alerting

Aufgabe: Crawlt Produktseiten/APIs, extrahiert Preis/Status, speichert Historie, zeigt Trends + Benachrichtigungen (Mail/Discord/Webhook).

Rollen:

    Scraper/Parser + Anti-Bot-Respekt (Rate Limit, Robots.txt)

    Datenmodell + DB/ES + Historisierung

    Alerting-Engine + Regeln (Thresholds, Prozentänderung)

    Dashboard (kleines Web-UI) + Deployment

Risiko: Websites ändern Layout häufig; APIs sind stabiler.
Option 3: Log-/Security-Analytics „Mini-SIEM“ (harte, aber sehr vorzeigbare Nummer)

Aufgabe: Generiert oder sammelt Logs (z. B. Nginx, SSH, App-Logs), normalisiert sie, speichert sie (Elastic), baut Detection-Rules (Bruteforce, 4xx/5xx Spikes), liefert Reports.

Rollen:

    Log-Collector + Pipeline (Filebeat/Vector oder eigener Collector)

    Parsing/Enrichment (GeoIP, User-Agent, Tags)

    Elastic-Mappings + Dashboards/Queries + Aggregationen

    Detection/Rule-Engine + Alerts + Tests

Vorteil: Sehr klarer Nutzen, gute Story für Präsentation.
Option 4: „Open-Data“-Pipeline + API (z. B. Verkehr, Wetter, Energie, Behörden)

Aufgabe: Holt periodisch Open-Data, bereinigt und versioniert, stellt eine kleine REST-API bereit (FastAPI) + Suchindex.

Rollen:

    Datenabgriff + Scheduling

    Transformations/Schema + Quality Checks

    Storage/Index + Performance/Optimierung

    API + Doku + Deployment

Vorteil: Datenquellen sind meist stabil und legal sauber.
Empfehlung (ohne Schönreden)

Wenn ihr schnell zu einem sauberen Ergebnis wollt: Option 1 oder 4.
Wenn ihr etwas „krasser“ und CV-tauglicher wollt, aber mit mehr Aufwand: Option 3.

Wenn du mir sagst, wie viel Zeit ihr habt (z. B. 2 Wochen / 6 Wochen) und ob es eher Data Engineering oder eher Softwareprodukt sein soll, kann ich eine konkrete Projektdefinition mit Milestones und Tech-Stack vorschlagen.
Du:
was kann man als daten alles sammeln
ChatGPT:

Grundsätzlich kann man alles sammeln, was (a) digital verfügbar ist, (b) rechtlich zulässig ist und (c) einen sinnvollen Use-Case hat. Praktisch unterscheidet man Daten nach Quelle und Struktur.
1) Web- und Plattformdaten

    RSS/News/Blogs: Titel, URL, Veröffentlichungsdatum, Kategorien, Textauszug

    Webseiten (HTML): Produktinfos, Stellenanzeigen, Veranstaltungsseiten, Speisekarten, Öffnungszeiten

    Foren/Q&A: Threads, Kommentare, Upvotes (Achtung: Nutzungsbedingungen)

    Open-Data-Portale: Behördenstatistiken, Verkehr, Umwelt, Energie

2) API-Daten (meist am saubersten)

    Wetter/Geodaten: Temperatur, Niederschlag, Warnungen, Koordinaten

    Finanzdaten: Aktien-/Krypto-Kurse, Handelsvolumen, Indikatoren

    ÖPNV/Verkehr: Verspätungen, Störungen, Fahrplandaten (GTFS/GTFS-RT)

    Soziale Medien (offizielle APIs): Posts/Metadaten (oft stark limitiert)

3) Maschinendaten / Telemetrie / Logs

    Server-Logs: Nginx/Apache, Application Logs, Error Logs

    Security-Logs: Login-Versuche, Firewall Events, IDS/IPS Events

    Systemmetriken: CPU/RAM/IO, Latenzen, Request-Raten

    IoT-Sensordaten: Temperatur, Luftqualität, Bewegung (falls vorhanden)

4) Dateien und Dokumente

    PDFs/Reports: Metadaten + extrahierter Text (aufwendig, aber möglich)

    CSV/Excel-Datensätze: Tabellen aus Open Data oder internen Quellen

    E-Mails/Tickets/Chats: Kategorien, Zeiten, Zuständigkeiten (Datenschutz sehr kritisch)

5) Nutzer- und Interaktionsdaten (intern)

    Clickstream: Seitenaufrufe, Events, Session-Dauer

    App-Events: Feature-Nutzung, Fehler, Performance

    Support-Daten: Ticket-Tags, Lösungszeiten, Themencluster

6) Inhaltliche/semantische Daten (aus Texten abgeleitet)

    Keywords/Tags, Named Entities (Person/Ort/Organisation)

    Sentiment oder Themencluster

    Duplikat-Erkennung, Ähnlichkeit (z. B. Near-Duplicates)

Was man realistisch gut sammeln kann (typische Teamprojekte)

    News/RSS + Volltext (wenn erlaubt)

    Open-Data (CSV/JSON)

    Verkehr/ÖPNV (GTFS)

    Wetter + Warnungen

    Produkt-/Job-Listings (mit Vorsicht)

    Webserver-/App-Logs (selbst erzeugt oder aus Demo-Setup)

Harte Grenzen (wichtig)

    Personenbezogene Daten (Namen, E-Mail, IDs, Standort, IPs) → nur mit Rechtsgrundlage, Minimierung, Anonymisierung/Pseudonymisierung.

    Scraping gegen Nutzungsbedingungen oder ohne Rate-Limits → Risiko von Sperren/Abmahnung.

    Paywalls / geschützte Inhalte → meist tabu.

Wenn du mir sagst, ob das Projekt eher „Scraping“, „APIs“ oder „Logs/Telemetry“ sein soll, kann ich dir 3–5 konkrete Datensets nennen, die technisch gut funktionieren und rechtlich weniger stressig sind.
Du:
wir haben bei uns an der hochschule eine wetterstation, die per api erreichbar ist, reicht das oder was kann man noch dazu nehmen
ChatGPT:

Ja, eine einzelne Wetterstations-API reicht grundsätzlich für ein solides Data-Engineering-Projekt – wenn ihr daraus mehr macht als “Daten abholen und speichern”. Bewertungsrelevant wird es durch: sauberes Schema, Zeitreihen-Design, Deduplikation, Qualitätschecks, sinnvolle Indizes/Aliases und eine kleine Nutzungsdemo.

Wenn ihr das Projekt inhaltlich und technisch aufwerten wollt, nehmt 1–3 zusätzliche Datenquellen dazu, die klar begründbar sind:
Sinnvolle Ergänzungen zur Hochschul-Wetterstation
1) Referenzdaten zum Vergleich (Plausibilitätscheck)

    DWD Open Data (Messwerte/Beobachtungen, Klima/CDC, Radar/Modelldaten): gut als “Ground Truth”/Vergleich in Deutschland.
    Deutscher Wetterdienst+2Deutscher Wetterdienst+2

    Alternativ/zusätzlich: Bright Sky als einfache JSON-Schnittstelle auf DWD-Daten (für schnellen Einstieg).
    Bright Sky

Use-Case: Abweichungen zwischen eurer Station und nächster offizieller Station erkennen (Bias, Sensorfehler, Ausfälle).
2) Historische Daten für Langzeit-Analysen

    Open-Meteo Historical Weather API (Reanalyse-basierte Historie): liefert lange Zeiträume, sinnvoll für “letzte 5–10 Jahre” als Kontext.
    open-meteo.com+1

    Meteostat (historische Stationen; auch Lückenfüllung): geeignet, wenn ihr viele Stationen/Standorte vergleichen wollt.
    dev.meteostat.net+1

Use-Case: Trend-/Saisonanalysen, Baselines, Anomalie-Erkennung.
3) Vorhersagen/Modelldaten als zusätzliche Dimension

    DWD Modell-/Forecast-Daten (Open Data), z. B. ICON-Produkte.
    Deutscher Wetterdienst

    ECMWF Open Data (Forecast-Felder; je nach Zugriff/Format teils aufwendiger).
    ECMWF+1

Use-Case: “Ist unsere Station konsistent mit Forecast?” oder Forecast vs. Ist-Messung.
4) Kontextdaten vom Standort (sehr praktisch, wenig Aufwand)

    Standort-Metadaten: Sensorhöhe, Koordinaten, Sensor-Typ, Kalibrierungsdatum, Wartungsfenster (als eigene Tabelle/Index).

    Optional: Gebäudedaten/Belegung (wenn intern verfügbar) → erklärt Temperaturspitzen, Wärmestau etc. (Datenschutz beachten).

Was ich als Minimal-Set empfehlen würde

    Eure Wetterstation (Primärquelle)

    DWD (Referenz) oder Bright Sky (Proxy)
    Deutscher Wetterdienst+1

    Open-Meteo Historical oder Meteostat für Historie
    open-meteo.com+1

Damit habt ihr: Live-Zeitreihe + Referenz + Historie. Das ist in der Regel “genug”, ohne dass ihr euch mit zu vielen APIs verzettelt.
Wichtige technische “Aufwertung”, falls ihr nur bei eurer API bleibt

    Qualitätskennzahlen pro Messpunkt (Range-Checks, Missing-Rate, Sprungdetektion)

    Idempotente Dokument-IDs pro Timestamp/Sensor

    Aggregationen (min/max/avg pro Stunde/Tag), plus Rohdaten-Layer

    Ausfall- und Drift-Erkennung (z. B. Rolling Z-Score)

Wenn du mir sagst, welche Variablen eure Station liefert (z. B. Temp, Feuchte, Druck, Wind, Regen) und in welcher Auflösung (z. B. 1 min / 10 min), kann ich dir ein konkretes Schema (Index-Mapping + _id-Strategie) und eine sinnvolle zweite Quelle passend dazu vorschlagen.
Du:
kann man also als projekt die daten der hs nehmen und diese mit anderen wetterstationen vergleichen
ChatGPT:

Ja. Das ist ein sauberes, gut begründbares Data-Engineering-Projekt: eigene Hochschul-Wetterstation als Primärquelle und Vergleich mit externen Stationen/Referenzdaten (z. B. DWD/andere offene Wetterdaten). Der Mehrwert ist klar: Qualitätssicherung, Drift-/Ausfall-Erkennung und Bias-Bewertung.
Was genau ihr vergleichen könnt

    Zeitreihen-Abgleich (Zeitfenster & Sampling)

    Resampling auf ein gemeinsames Intervall (z. B. 10-Minuten oder stündlich)

    Zeitzone/UTC-Normalisierung, saubere Timestamp-Parsing-Regeln

    Abweichungen / Bias

    Mittelwertdifferenz (Bias) pro Variable (Temp, Feuchte, Druck, Wind, Regen)

    RMSE/MAE pro Tag/Woche/Monat

    Korrelation / Cross-Correlation (falls Zeitversatz durch Mess-/Upload-Latenz)

    Plausibilitäts- und Qualitätschecks

    Range-Checks (z. B. Temperatur physikalisch plausibel)

    Sprungdetektion (plötzliche unrealistische Sprünge)

    Missing-Rate, Ausfallzeiten, “stuck sensor” (konstante Werte)

    Drift über Wochen/Monate (Sensor altert/verschmutzt)

    Standort- und Höhenunterschiede berücksichtigen

    Vergleich primär mit nächstgelegenen Stationen und ähnlicher Höhenlage

    Optional: einfache Korrektur über Lapse Rate/Metadaten (nicht übertreiben; sauber dokumentieren)

Datenquellen-Setup (realistisch für ein Teamprojekt)

    Hochschulstation (Live/Primär)

    1–3 externe Stationen als Referenz (offene Daten / API)

    Optional: Vorhersage-/Modell-Daten als dritter Blickwinkel (Ist vs. Forecast)

Wichtig: Nicht zu viele Quellen. Zwei externe Referenzen reichen meist, wenn ihr dafür sauber normalisiert und testet.
Pipeline-Design (so wirkt es “Data Engineering” und nicht nur “Daten holen”)

A) Raw Layer

    Roh-JSON unverändert speichern (Reprocessing möglich)

B) External Preprocessing

    Einheitliches Schema (Units, Feldnamen, Datentypen)

    Timestamp-Normalisierung (UTC)

    Deduplikation über deterministische _id (z. B. hash(station_id + timestamp))

    Qualitätsflags (z. B. qc_range_ok, qc_spike_ok, qc_missing)

C) Elasticsearch Modell

    weather-raw-* (optional)

    weather-processed-* (normalisiert + QC)

    stations-meta (Koordinaten, Höhe, Sensoren, Quelle)

Aliase wie weather-all für gemeinsame Queries sind sinnvoll.
Vergleichslogik (minimal, aber überzeugend)

    Schritt 1: “Nearest station” bestimmen (über geo_point in stations-meta)

    Schritt 2: Werte auf gemeinsames Intervall aggregieren

    Schritt 3: Join über (timestamp_bucket, variable) in eurer Verarbeitung (nicht in ES erzwingen)

    Schritt 4: Speichern der Vergleichsergebnisse als eigener Index, z. B. weather-compare-*:

        hs_station_id

        ref_station_id

        timestamp_bucket

        delta_temp, delta_rh, rmse_24h, missing_ref, missing_hs, etc.

Teamaufteilung (4 Personen, klare Verantwortung)

    Ingestion + Airflow Scheduling + Raw Layer

    Preprocessing + Schema + QC + Deduplikation

    Elasticsearch: Templates/Mappings/Aliase + Bulk-Load-Optimierung

    Compare-Job + Smoke Tests + Demo (3–5 Queries/Aggregationen, kleines Dashboard optional)

Typische Fallstricke (die ihr früh lösen müsst)

    Zeitstempel (UTC vs. lokal, Sommerzeit)

    Unterschiedliche Einheiten (m/s vs. km/h, hPa vs. Pa)

    Messhöhen/Standort (Wind ist extrem standortabhängig)

    Datenlücken bei Referenzquellen → sauber als “missing” markieren statt stillschweigend interpolieren

Wenn du mir die Variablen und das Intervall eurer HS-API nennst (z. B. Temp/RH/Druck/Wind/Regen, 1-min/10-min), kann ich dir ein konkretes Normalisierungsschema (Feldnamen/Datentypen) und eine robuste _id-Strategie formulieren.
Du:
gib mir dazu einen simplen projektantrag
ChatGPT:

Projektantrag (simpel): Vergleich von Hochschul-Wetterstationsdaten mit Referenzstationen

1. Projekttitel
Qualitätssicherung und Vergleichsanalyse: Hochschul-Wetterstation vs. externe Wetterstationen

2. Ausgangslage / Motivation
An der Hochschule existiert eine Wetterstation mit API-Zugriff. Einzelmessungen sind jedoch nur begrenzt aussagekräftig, solange keine Referenz gegenüber offiziellen oder anderen offenen Wetterstationen besteht. Ziel ist eine reproduzierbare Datenpipeline, die Messdaten regelmäßig erfasst, bereinigt, versioniert speichert und systematisch mit Referenzdaten vergleicht.

3. Zielsetzung

    Periodische Erfassung der Hochschul-Wetterstationsdaten über die vorhandene API.

    Ergänzende Erfassung von Referenzdaten (z. B. 1–3 externe Wetterstationen / offene Wetterdaten).

    Einheitliche Vorverarbeitung (Schema, Datentypen, Zeitzonen, Einheiten) und Deduplikation.

    Speicherung der normalisierten Daten in Elasticsearch.

    Berechnung und Speicherung von Vergleichskennzahlen (z. B. Abweichung/Bias, Missing-Rate, einfache Qualitätsflags).

    Nachweis der Nutzbarkeit durch wenige Beispielabfragen/Aggregationen (keine umfangreiche Data-Science-Analyse).

4. Scope / Abgrenzung
Im Fokus steht Data Engineering (Pipeline, Datenmodell, Speicherung, Automatisierung, Reproduzierbarkeit). Eine Visualisierung oder tiefgehende statistische Modellierung ist optional und nicht Kernbestandteil.

5. Datenquellen

    Primärquelle: Hochschul-Wetterstation (API).

    Referenzquellen: offene Wetterdaten (z. B. DWD-nahe Stationen oder vergleichbare offene Quellen).

    Metadaten: Stationen (Koordinaten, Höhe, Sensortyp, Quelle).

6. Technischer Ansatz (Architektur)

    Ingestion/Scheduling: Apache Airflow (z. B. stündlich).

    Raw Layer: Speicherung der unveränderten Rohdaten (JSON) zur Reproduzierbarkeit und für Debugging/Reprocessing.

    Externe Vorverarbeitung (Python):

        Normalisierung auf ein einheitliches Schema

        Zeitzonen-/Timestamp-Normalisierung (UTC)

        Einheiten-Konvertierung (falls notwendig)

        Deduplikation über deterministische Dokument-IDs (_id)

        Qualitätschecks (Range-Checks, Missing-Flags, einfache Sprungdetektion)

    Speicherung/Optimierung: Elasticsearch 3-Node-Cluster (Docker Compose), Index-Templates/Mappings/Aliase als Code, Bulk-Load.

7. Datenmodell (grobe Indizes)

    weather-raw-* (optional): Rohdaten je Quelle

    weather-processed-*: normalisierte Messwerte + QC-Flags

    stations-meta: Station-Metadaten

    weather-compare-*: Vergleichsergebnisse (z. B. delta_temp, mae_24h, Missing-Rate)

8. Deliverables

    Git-Repository mit vollständigem Setup „as code“ (Docker Compose, Airflow DAGs, Skripte, Index-Templates).

    Reproduzierbarer Pipeline-Lauf inkl. Rohdatenablage und Bulk-Ingest.

    Dokumentation der Designentscheidungen (Schema, _id, Shards/Replicas, Aliase, QC-Regeln).

    Smoke-Tests (Cluster Health, _count, Beispielquery, Beispielaggregation).

    Kurze Demo-Abfragen (z. B. Abweichung pro Tag, Ausfallzeiten, Top-Abweichungen).

9. Arbeitspakete / Teamaufteilung (4 Personen)

    Ingestion & Airflow (DAG, Raw Layer, Logging)

    Preprocessing (Schema, Timestamp/Units, Deduplikation, QC)

    Elasticsearch (Cluster, Templates/Mappings/Aliase, Bulk-Optimierung)

    Vergleichsjob + Tests/Doku (Kennzahlen, Validierung, Demo-Queries)

10. Risiken / Maßnahmen

    Unterschiedliche Zeitauflösungen/Zeitzonen → strikte UTC-Normalisierung und Resampling.

    Datenlücken/Fehlmessungen → QC-Flags, keine stillschweigende Interpolation.

    Standort-/Höhenunterschiede → Auswahl nahegelegener Referenzstationen, Dokumentation der Limitationen.

11. Erfolgskriterien

    Pipeline läuft automatisiert und idempotent (keine Duplikate bei Wiederholung).

    Daten sind sauber normalisiert, durchsuchbar und aggregierbar in Elasticsearch.

    Vergleichsindex liefert nachvollziehbare Abweichungskennzahlen und Ausfall-/Qualitätsindikatoren.

    Setup ist reproduzierbar auf neuer Maschine (1 Command: Docker Compose + Scripts).

Wenn du willst, kann ich das in eurem Stil (1 Seite PDF/Word) formatieren und um konkrete Tools (z. B. DWD vs. Meteostat) ergänzen.
Du:
alles als markdown 
ChatGPT:

# Projektantrag: Vergleich von Hochschul-Wetterstationsdaten mit Referenzstationen

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

## 9. Arbeitspakete / Teamaufteilung (4 Personen)
1. **Ingestion & Airflow:** DAG, Raw Layer, Logging
2. **Preprocessing:** Schema, Timestamp/Units, Deduplikation, QC
3. **Elasticsearch:** Cluster, Templates/Mappings/Aliase, Bulk-Optimierung
4. **Vergleichsjob + Tests/Doku:** Kennzahlen, Validierung, Demo-Queries

## 10. Risiken / Maßnahmen
- **Unterschiedliche Zeitauflösungen/Zeitzonen:** strikte UTC-Normalisierung und Resampling
- **Datenlücken/Fehlmessungen:** QC-Flags, keine stillschweigende Interpolation
- **Standort-/Höhenunterschiede:** Auswahl nahegelegener Referenzstationen, Dokumentation der Limitationen

## 11. Erfolgskriterien
- Pipeline läuft automatisiert und idempotent (keine Duplikate bei Wiederholung)
- Daten sind sauber normalisiert, durchsuchbar und aggregierbar in Elasticsearch
- Vergleichsindex liefert nachvollziehbare Abweichungskennzahlen und Ausfall-/Qualitätsindikatoren
- Setup ist reproduzierbar auf neuer Maschine (Docker Compose + Skripte)


ChatGPT kann Fehler machen. Überprüfe wichtige Informationen. Siehe Cookie-Voreinstellungen.
