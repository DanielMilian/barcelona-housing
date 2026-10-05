"""Load raw extracts into the Postgres warehouse (schema raw). Safe to rerun."""
import json
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import Json

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT/ ".env")

INE_DIR = ROOT / "data" / "raw" / "ine"
SERPAVI_CSV = ROOT / "data" /"raw" / "serpavi" / "barcelona_districts_long.csv"

DDL  = """
CREATE TABLE IF NOT EXISTS raw.ine_raw (
    source_label    text NOT NULL,
    table_id        text NOT NULL,
    extract_date    date NOT NULL,
    payload         jsonb NOT NULL,
    loaded_at       timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (source_label, extract_date)
);
CREATE TABLE IF NOT EXISTS raw.serpavi_long (
    district_code   text NOT NULL,
    metric          text NOT NULL,
    statistic       text,
    housing_type    text NOT NULL,
    year            integer NOT NULL,
    value           double precision,
    loaded_at       timestamptz NOT NULL DEFAULT now()
);
"""

UPSERT_INE = """
INSERT INTO raw.ine_raw (source_label, table_id, extract_date, payload)
VALUES (%s, %s, %s, %s)
ON CONFLICT (source_label, extract_date)
DO UPDATE SET table_id = EXCLUDED.table_id, payload = EXCLUDED.payload, loaded_at = now()
WHERE raw.ine_raw.payload IS DISTINCT FROM EXCLUDED.payload
"""
COPY_SERPAVI = """
COPY raw.serpavi_long (district_code, metric, statistic, housing_type, year, value)
FROM STDIN WITH (FORMAT csv, HEADER true)
"""

def connect():
    return psycopg2.connect(
            host=os.getenv("WAREHOUSE_HOST", "localhost"),
            port=os.environ["WAREHOUSE_PORT"],
            user=os.environ["WAREHOUSE_USER"],
            password=os.environ["WAREHOUSE_PASSWORD"],
            dbname=os.environ["WAREHOUSE_DB"],
            )

def load_ine(cur) -> None:
    for label_dir in sorted(p for p in INE_DIR.iterdir() if p.is_dir()):
        for path in sorted(label_dir.glob("*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            cur.execute(
                    UPSERT_INE, (label_dir.name, payload["table_id"], path.stem, Json(payload))
                    )
def load_serpavi(cur) -> None:
    cur.execute("TRUNCATE raw.serpavi_long")
    with SERPAVI_CSV.open(encoding="utf-8") as f:
        cur.copy_expert(COPY_SERPAVI, f)


def main() -> None:
    with connect() as conn, conn.cursor() as cur:
        cur.execute(DDL)
        load_ine(cur)
        load_serpavi(cur)

    with connect() as conn, conn.cursor() as cur:
        cur.execute(
                "SELECT source_label, extract_date, jsonb_array_length(payload->'series') "
                "FROM raw.ine_raw ORDER BY 1, 2"
                )
        for row in cur.fetchall():
            print("ine_raw:", row)
        cur.execute("SELECT count(*), count(value), count(statistic) FROM raw.serpavi_long")
        print("serpavi_long (rows, non-null values, non_null statistic):", cur.fetchone())

if __name__ == "__main__":
    main()



