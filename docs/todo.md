# TODO – Projektstatus und nächste Schritte (Fokus: offene Punkte)

## Kurzstatus

### Bereits umgesetzt (kompakt)
- [x] Docker-Compose Setup mit 3-Node Elasticsearch-Cluster
- [x] Airflow-Orchestrierung (`@daily`, `catchup=False`)
- [x] Echter API-Abgriff (BrightSky) statt Dummy-Daten
- [x] Raw-Layer speichert unveränderte API-Responses
- [x] Bulk-Import mit idempotenter `_id`-Strategie
- [x] ES-Templates, Pipeline und Alias als Code
- [x] Cluster läuft stabil (`GREEN`)

---

# Offene Punkte (priorisiert)

## 1️⃣ Pflicht: `preprocess.py` vollständig auf BrightSky umstellen

### Problem
- Aktueller Code ist noch auf Dummy-Struktur (`raw["items"]`) ausgelegt.
- BrightSky liefert `raw["payload"]["weather"]`.

### To-do
- Iteration über `payload.weather`
- Pro `timestamp` ein Dokument erzeugen
- `doc_id = sha256(provider|source_id|timestamp)`
- Felder extrahieren:
  - temperature
  - relative_humidity
  - pressure_msl
  - precipitation
  - wind_speed
  - wind_direction
  - dew_point
  - cloud_cover
  - visibility
  - condition / icon
- `timestamp` als ISO8601 übernehmen
- `processed_at` setzen

Ohne diese Anpassung funktioniert die Pipeline fachlich nicht korrekt.

---

## 2️⃣ Pflicht: Elasticsearch-Mapping auf Wetterdaten anpassen

### Problem
Aktuelles Template ist noch generisch (`title`, `message`, `url`).

### To-do
- Neues Mapping definieren:
  - `timestamp` → `date`
  - Messwerte → `float` oder `integer`
  - `provider`, `source_id` → `keyword`
  - `condition`, `icon` → `keyword`
- Alte Textfelder entfernen
- Template in `db/elastic/index-template.json` aktualisieren
- Indizes neu erstellen (falls nötig)

---

## 3️⃣ Pflichtnah: Index-Namensraum mit Antrag angleichen

### Problem
Aktuell:
- `data-2024`
- `all-data`

Antrag beschreibt:
- `weather-processed-*`
- `weather-compare-*`

### To-do
- `ES_INDEX` auf z.B. `weather-processed-2026`
- `ES_ALIAS` auf `weather-all`
- Template-Patterns anpassen
- `apply_es.py` konsistent umstellen

Ziel: Kein Widerspruch zwischen Antrag und Implementierung.

---

## 4️⃣ Fachlich zentral: Vergleichsquelle ergänzen

BrightSky ist jetzt Primärquelle.

### To-do
- Zweite Quelle anbinden (z.B. Open-Meteo)
- Gemeinsames Zielschema definieren
- Vergleichskennzahlen berechnen:
  - delta_temperature
  - delta_pressure
  - missing_rate
- Optional:
  - eigener `weather-compare-*` Index

Das ist Kernbestandteil des Antrags (Qualitätssicherung).

---

## 5️⃣ Bewertungsrelevant: Analyzer / Normalizer ergänzen

### To-do
- Subfields für Textfelder:
  - `condition.keyword`
- Lowercase-Normalizer für Sortierung
- Optional:
  - `search_as_you_type` oder `edge_ngram` für Autocomplete
- Mapping entsprechend erweitern

---

## 6️⃣ Prüfungsfest machen: Erweiterte Nachweis-Queries

Aktuell nur Basis-Checks.

### Ergänzen in `post_checks.py`:
- `term`-Query auf `provider` oder `source_id`
- `_doc/<id>` Abruf
- `range` Query (letzte 24h)
- `date_histogram`
- `avg(temperature)`
- `max(wind_speed)`

Damit deckst du die typischen ES-Query-Typen vollständig ab.

---

## 7️⃣ Optional: Shard-Konzept demonstrativer gestalten

Aktuell:
- `number_of_shards = 1`

Optional:
- 2–3 Primaries setzen
- Verteilung und Parallelisierung dokumentieren

---

# Minimaler Arbeitsplan (klar priorisiert)

1. `preprocess.py` BrightSky-kompatibel machen  
2. ES-Mapping auf Wetterdaten umstellen  
3. Indizes/Alias auf `weather-*` umbenennen  
4. Load & Post-Checks testen  
5. Zweite Datenquelle anbinden  
6. Vergleichskennzahlen implementieren  
7. Queries erweitern  

---

# Zielzustand

- Reproduzierbare, automatisierte Wetterdaten-Pipeline
- Zwei Datenquellen
- Vergleichsanalyse gespeichert
- Sauberes ES-Mapping
- Nachweis aller relevanten Query-Typen
- Vollständig konsistent mit Antrag
