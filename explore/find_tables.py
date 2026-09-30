import sys

import requests 

BASE = "https://servicios.ine.es/wstempus/js/en"
op_id = sys.argv[1]

r = requests.get(f"{BASE}/TABLAS_OPERACION/{op_id}", timeout=60)
r.raise_for_status()
tables = r.json()
if not isinstance(tables, list) or not tables:
    raise SystemExit(f"Unexpected response:  {str(tables)[:3000]}")

print(len(tables), "tables; keys:", list(tables[0].keys()))
for t in tables:
    print(t.get("Id"), "|", t.get("Nombre"))


