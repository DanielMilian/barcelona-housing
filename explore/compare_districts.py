import re

import requests


BASE = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA"
INCOME_RE = re.compile(r"^Barcelona district (\d+)\. Base data\. Average household net income\.")
RENT_RE = re.compile(r"^Barcelona district (\d+)\. Index\. Total\.")

def fetch(table_id, nult):
    r = requests.get(f"{BASE}/{table_id}", params={"nult": nult}, timeout=300)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise SystemExit(f"{table_id}: {str(data)[:300]}")
    return data

def by_year(s):
    return {d["Anyo"]: d["Valor"] for d in s["Data"]}

income = {m.group(1): by_year(s) for s in fetch("30896", 10) if (m := INCOME_RE.match(s["Nombre"]))}
rent = {m.group(1): by_year(s) for s in fetch("59061", 20) if (m := RENT_RE.match(s["Nombre"]))}

print("district     rent2015    income_idx_2023    rent_idx_2023  gap")
for d in sorted(income):
    inc, rn = income[d], rent.get(d, {})
    if not (inc.get(2015) and inc.get(2023) and rn.get(2015) and rn.get(2023)):
        print(f"{d:>8} missing data")
        continue
    inc_idx = inc[2023] / inc[2015] * 100
    print(f"{d:>8} {rn[2015]:8.1f}  {inc_idx:15.1f} {rn[2023]:13.1f}    {inc_idx - rn[2023]:6.1f}")



