"""Extract Barcelona series from INE tables into data/raw/ine/."""
import json
import re
import time
from datetime import date
from pathlib import Path

import requests

BASE_URL = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "ine"

# nult = how manmy latest periods to request. It is relative to the newest data,
# so the window slides as INE publishes new periods. Revisit if years start dropping
TABLES = {
        "30896": {
            "label": "income_adrh",
            "nult": 10,
            "name_re": r"^Barcelona( district \d+)?\. ",
            "expected": 77,
            },
        "59061": {
            "label": "rent_index_districts",
            "nult": 20,
            "name_re": r"^Barcelona district \d+\. ",
            "expected": 20,
            },
        "24081": {
            "label": "cpi_province",
            "nult": 200,
            "name_re": r"^Barcelona\. Overall index\. Index",
            "expected": 1,
            },
        }

def fetch_table(table_id: str, nult: int) -> list[dict]:
    r = requests.get(f"{BASE_URL}/{table_id}", params={"nult": nult}, timeout=300)
    r.raise_for_status()
    data = r.json()

    if not isinstance(data, list) or not data:
        raise ValueError(f"INE table {table_id}: unexpected response: {str(data)[:200]}")
    return data

def extract(table_id: str, cfg: dict) -> Path:
    data = fetch_table(table_id, cfg["nult"])
    pattern = re.compile(cfg["name_re"])
    series = [s for s in data if pattern.match(s["Nombre"])]
    if len(series) != cfg["expected"]:
        raise ValueError(
            f"INE table {table_id}: expected {cfg['expected']} series, got {len(series)}"
            )
    path = RAW_DIR / cfg["label"] / f"{date.today().isoformat()}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"table_id": table_id, "series": series}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path

def main() -> None:
    for table_id, cfg in TABLES.items():
        path = extract(table_id, cfg)
        print(f"{table_id} {cfg['label']}: saved {path.relative_to(RAW_DIR.parent.parent)}")
        time.sleep(1)

if __name__ == "__main__":
    main()


