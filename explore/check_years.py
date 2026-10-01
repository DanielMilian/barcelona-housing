import requests 

BASE = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA"

def fetch(table_id, nult):
    r = requests.get(f"{BASE}/{table_id}", params={"nult": nult}, timeout=300)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise SystemExit(f"{table_id}: {str(data)[:300]}")
    return data

def show(data, name_part):
    for s in data:
        if name_part in s["Nombre"]:
            print(s["Nombre"])
            print(" ", sorted((d.get("Anyo"), d["Valor"]) for d in s["Data"]))
            return
    print("Not found:", name_part)

income = fetch("30896", 10)
show(income, "Barcelona district 02. Base data. Average household net income")

rent = fetch("59061", 20)
show(rent, "Barcelona district 02. Index. Total")
