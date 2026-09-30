import requests

BASE = "https://servicios.ine.es/wstempus/js/en"
KEYWORDS = ("housing", "dwelling", "rent", "vivienda", "alquiler")

r = requests.get(f"{BASE}/OPERACIONES_DISPONIBLES", timeout=60)
r.raise_for_status()
ops = r.json()
print(len(ops), "operations; keys", list(ops[0].keys()))

for op in ops:
    name = op.get("Nombre", "")
    if any(k in name.lower() for k in KEYWORDS):
        print(op.get("Id"), "|", op.get("Codigo"), "|", name)


