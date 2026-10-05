"""Export the final mart to a small CSV for the dashboard"""
from pathlib import Path

from load.load_raw import connect

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "app" / "mart_district_affordability.csv"
EXPECTED_ROWS = 90

COPY_SQL = """
COPY (
    SELECT * FROM analytics.mart_district_affordability
    ORDER BY district_code, year
) TO STDOUT WITH (FORMAT csv, HEADER true)
"""
def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    tmp = OUT.with_suffix(".csv.tmp")
    with connect() as conn, conn.cursor() as cur, tmp.open("w", encoding="utf-8", newline="") as f:
        cur.copy_expert(COPY_SQL, f)
    rows = len(tmp.read_text(encoding="utf-8").splitlines()) - 1
    if rows != EXPECTED_ROWS:
        tmp.unlink()
        raise ValueError(f"expected {EXPECTED_ROWS} rows, exported {rows}")
    tmp.replace(OUT)
    print(f"saved {OUT.relative_to(ROOT)}: {rows} rows")


if __name__ == "__main__":
    main()
