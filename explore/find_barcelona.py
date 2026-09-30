import time

import requests

BASE = "https://servicios.ine.es/wstempus/js/en"
OP_ID = "353"
NAME = "Mean and median income indicators"
PLACE = "barcelona"

tables = requests.get(f"{BASE}/TABLAS_OPERACION/{OP_ID}", timeout=60).json()
ids = [t["Id"] for t in tables if t["Nombre"].startswith(NAME)]
print(len(ids), "candidate tables")

for tid in ids:
    try:
        r = requests.get(f"{BASE}/DATOS_TABLA/{tid}", params={"nult": 1}, timeout=120)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(tid, "ERROR", e)
        time.sleep(1)
        continue
    if not isinstance(data, list):
        print(tid, "unexpected:", str(data)[:200])
        time.sleep(1)
        continue
    hits = [s["Nombre"] for s in data if PLACE in s["Nombre"].lower()]
    first = data[0]["Nombre"] if data else "(empty)"
    print(tid, f"{len(data)} series, {len(hits)} mention '{PLACE}' | first: {first[:90]}")
    for h in hits[:3]:
        print("    ", h)
    time.sleep(1)

print("done")
