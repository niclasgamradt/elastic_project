from pathlib import Path
import json

from scripts.config import SETTINGS


def main() -> None:
    files = sorted(SETTINGS.processed_dir.glob("processed_*.ndjson"))
    if not files:
        print("No processed_*.ndjson found.")
        return

    f = files[-1]
    lines = f.read_text(encoding="utf-8").splitlines()
    print("file:", f)
    print("lines:", len(lines))

    if lines:
        first = json.loads(lines[0])
        print("first keys:", sorted(first.keys()))
        print("doc_id:", first.get("doc_id"))
        print("timestamp:", first.get("timestamp"))
        print("title:", first.get("title"))


if __name__ == "__main__":
    main()
