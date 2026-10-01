import sys

import requests

BASE = "https://servicios.ine.es/wstempus/js/en"
keywords = [k.lower() for k in sys.argv[1:]]

ops = requests.get(f"{BASE}/OPERACIONES_DISPONIBLES", timeout=60).json()
for op in ops:
    if any(k in op["Nombre"].lower() for k in keywords):
        print(op["Id"], "|", op["Codigo"], "|", op["Nombre"])
