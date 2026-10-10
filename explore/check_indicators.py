import re
from collections import defaultdict

import requests

URL = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/30896"
NAME_RE = re.compile(r"^Barcelona district (\d+)\. Base data\. (.+?)\.\s*$")

data = requests.get(URL, params={"nult": 10}, timeout=300).json()
if not isinstance(data, list):
    raise SystemExit(str(data)[:300])

gaps = defaultdict(set)
for s in data:
    m = NAME_RE.match(s["Nombre"])
    if not m:
        continue
    years = {d["Anyo"]: d["Valor"] for d in s["Data"]}
    gaps[m.group(2)] |= {y for y in range(2015, 2024) if years.get(y) is None}

for indicator, missing in gaps.items():
    print(f"{indicator}: missing {sorted(missing) or 'none'}")


