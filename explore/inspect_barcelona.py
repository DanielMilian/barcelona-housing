import collections

import requests

URL = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/30896"

data = requests.get(URL, params={"nult": 1}, timeout=300).json()
if not isinstance(data, list):
    raise SystemExit(f"Unexpected response: {str(data)[:300]}")

levels = collections.defaultdict(list)
indicators = collections.Counter()

for s in data:
    name = s["Nombre"]
    if not name.startswith("Barcelona"):
        continue
    geo, _, rest = name.partition(". ")
    if "sección" in geo or "section" in geo:
        level = "census section"
    elif "district" in geo:
        level = "district"
    else:
        level = "municipality/other"
    levels[level].append(name)
    indicators[rest] += 1

for level, names in levels.items():
    print(f"\n{level}: {len(names)} series")
    for n in names[:3]:
        print("  ", n)

print("\nindicators (series count each):")
for ind, n in indicators.most_common(15):
    print(f" {n:5d} {ind}")

sample = next(s for s in data if s["Nombre"].startswith("Barcelona"))
print("\nperiod in sample:", sample["Data"][:3]])


