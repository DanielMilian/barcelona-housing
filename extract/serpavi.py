""" Extract Barcelona districts from the SERPAVI Excel and reshape to long format."""
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "raw" / "serpavi" / "serpavi_2011-2024.xlsx"
OUT = ROOT / "data" / "raw" / "serpavi" / "barcelona_districts_long.csv"

BARCELONA_MUN = "08019"
COL_RE = re.compile(
    r"^(?P<metric>BI_ALVHEPCO|ALQM2_LV|ALQTBID12|SLVM2)"
    r"_(?:(?P<statistic>M|25|75)_)?(?P<housing_type>T?V[CU])_(?P<yy>\d{2})$"
)
EXPECTED_COLUMNS = 280
EXPECTED_ROWS = 2800

def main() -> None:
    df = pd.read_excel(
            SRC, sheet_name="Distritos", dtype={"CPRO": str, "CUMUN": str, "CUDIS": str}
            )
    bcn = df[df["CUMUN"] == BARCELONA_MUN]

    value_cols = [c for c in bcn.columns if COL_RE.match(c)]
    if len(value_cols) != EXPECTED_COLUMNS:
        raise ValueError(f"expected {EXPECTED_COLUMNS} value columns, got {len(value_cols)}")

    long = bcn.melt(
            id_vars="CUDIS", value_vars=value_cols, var_name="column", value_name="value"
            )
    parts = long["column"].str.extract(COL_RE)
    long = pd.concat(
            [long[["CUDIS", "value"]].rename(columns={"CUDIS": "district_code"}), parts], axis=1
            )
    long["housing_type"] = long["housing_type"].str.lstrip("T")
    long["year"] = 2000 + long["yy"].astype(int)
    long = long[["district_code", "metric", "statistic", "housing_type", "year", "value"]]

    if long["district_code"].nunique() != 10 or len(long) != EXPECTED_ROWS:
        raise ValueError(
                f"expected 10 districts / {EXPECTED_ROWS} rows, "
                f"got {long['distric_code'].nunique()} / {len(long)}"
                )
    long.to_csv(OUT, index=False, encoding="utf-8")
    print(f"saved {OUT.relative_to(ROOT)}: {len(long)} rows")
    print(long.isna().groupby(long["metric"]).sum()["value"].rename("null values per metric"))
    sample = long[
            (long["metric"] == "ALQTBID12")
            & (long["statistic"] == "M")
            & (long["housing_type"] == "VC")
            & (long["year"] == 2023)
            ]
    print(sample.to_string(index=False))

if __name__ == "__main__":
    main()

