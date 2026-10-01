import requests

URL = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/24081"
data = requests.get(URL, params={"nult": 150}, timeout=300).json()
if not isinstance(data, list):
    raise SystemExit(str(data)[:300])

s = next(s for s in data if s["Nombre"].startswith("Barcelona. Overall index. Index"))

by_year = {}
for d in s["Data"]:
    by_year.setdefault(d["Anyo"], []).append(d["Valor"])

annual = {}
for y in range(2015, 2024):
    vals = by_year[y]
    assert len(vals) == 12 and None not in vals, f"{y}: incomplete"
    annual[y] = sum(vals) / 12

for y, v in annual.items():
    print(y, round(v, 3))
print(f"inflation 2015->2023: {(annual[2023] / annual[2015] - 1) * 100:1f}%")


