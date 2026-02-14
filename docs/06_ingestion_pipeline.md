# Ingestion Details

## Fetch
- HTTP GET Requests
- Fehlerbehandlung (HTTP Status, Timeout)
- Speicherung als raw JSON

## Run-ID
- run_id basiert auf Airflow Execution Date
- Dateibenennung: raw_<run_id>__provider.json

## Reproduzierbarkeit
Rohdaten bleiben erhalten (Reprocessing möglich).


## Neue API anbinden: Anforderungen an `fetch_<provider>.py`

Um eine weitere API einzubinden, wird ein neues Fetch-Skript nach dem Muster  
`scripts/fetch_<provider>.py` erstellt. Das Skript ist ausschließlich für den
**Rohdatenabruf** zuständig (keine Normalisierung).

### Muss-Aufgaben im Fetch-Skript

1. **Parameter / Konfiguration lesen**
   - z. B. API-Base-URL, Token, Standortparameter, etc. (über `os.getenv()` oder `SETTINGS`)
   - optional: Provider-Name festlegen (`provider = "<provider>"`)

2. **Run-ID / Datum ableiten**
   - `run_id` (z. B. `YYYY-MM-DD`) aus Airflow übernehmen, falls vorhanden
   - Fallback auf aktuelles Datum, wenn `run_id` nicht gesetzt ist

3. **API-Endpunkt/URL bauen**
   - URL inkl. Query-Parametern deterministisch zusammensetzen
   - Endpoint-URL in den Rohdaten mit abspeichern (Nachvollziehbarkeit)

4. **HTTP-Request durchführen**
   - `GET` Request mit sinnvollen Headers (Accept, Auth)
   - Timeout setzen
   - HTTP-Fehler sauber behandeln (Statuscodes, Exceptions)

5. **Rohdaten unverändert speichern (Raw Layer)**
   - Ziel: `data/raw/`
   - Dateiname: `raw_<run_id>__<provider>.json`
   - Inhalt enthält Metadaten + Original-Payload, z. B.:
     - `fetched_at`
     - `provider`
     - `endpoint`
     - `payload` (unverändert)

6. **Deterministische Ausgaben**
   - `print()` mit Endpoint + Output-Datei (Debug/Logging)
   - Keine Seiteneffekte außerhalb von `data/raw`

### Wichtig (Abgrenzung)
- Keine Feldnamen ändern
- Keine Typkonvertierung
- Keine Deduplikation
- Keine NDJSON-Erzeugung  
Diese Schritte gehören ausschließlich in `preprocess_<provider>.py`.


### Template: `scripts/fetch_<provider>.py`

```python
import json
import os
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

from scripts.config import SETTINGS


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def main(run_id: str | None = None) -> None:
    """
    Fetches raw data from <provider> API and stores it unchanged
    in data/raw as JSON.
    """

    ensure_dir(SETTINGS.raw_dir)

    provider = "<provider-name>"

    # 1) Determine run date
    if run_id:
        date_str = run_id
    else:
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # 2) Build API URL
    base_url = os.getenv("<PROVIDER>_BASE_URL", "https://api.example.com")
    url = f"{base_url}/endpoint?date={date_str}"

    print(f"Fetching {provider}: {url}")

    # 3) HTTP request
    try:
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                raise RuntimeError(f"HTTP {resp.status}")
            payload = json.loads(resp.read().decode("utf-8"))

    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTPError {e.code}: {e.reason}")
    except Exception as e:
        raise RuntimeError(f"Fetch failed: {e}")

    # 4) Store raw data
    raw = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "provider": provider,
        "run_id": date_str,
        "endpoint": url,
        "payload": payload,
    }

    out_file = SETTINGS.raw_dir / f"raw_{date_str}__{provider}.json"
    out_file.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote raw file: {out_file}")


if __name__ == "__main__":
    main()
