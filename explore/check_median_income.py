import re

import requests

URL = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/30896"
NAME_RE = re.compile(r"^Barcelona district (\d+)\. Base data\. Median household income\.")

data = requests.get(URL, params={"nult": 10}, timeout=300).json()
print([s["Nombre"] for s in data if s["Nombre"].startswith("Barcelona district 02")])
if not isinstance(data, list):
    raise SystemExit(str(data)[:300])

for s in data:
    m = NAME_RE.match(s["Nombre"])
    if m:
        years = {d["Anyo"]: d["Valor"] for d in s["Data"]}
        missing = [y for y in range(2015, 2024) if years.get(y) is None]
        print(m.group(1), years.get(2015), years.get(2023), "missing:", missing)

