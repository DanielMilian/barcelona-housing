import sys

import requests

table_id = sys.argv[1]
place = sys.argv[2].lower()
nult = sys.argv[3] if len(sys.argv) > 3 else "1"

url = f"https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/{table_id}"
data = requests.get(url, params={"nult": nult}, timeout=300).json()
if not isinstance(data, list):
    raise SystemExit(f"Unexpected response: {str(data)[:300]}")

hits = [s for s in data if place in s["Nombre"].lower()]
print(f"{len(data)} series total, {len(hits)} mention '{place}'")
for s in hits[:10]:
    print("\n", s["Nombre"])
    print("   ", s["Data"][:3])
