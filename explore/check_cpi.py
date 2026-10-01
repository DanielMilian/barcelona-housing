import requests

URL = "https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/24081"
data = requests.get(URL, params={"nult": 150}, timeout=300).json()
if not isinstance(data, list):
    raise SystemExit(str(data)[:300])

print(len(data), "series; first 3:", [s["Nombre"] for s in data[:3]])

for s in data:
    if s["Nombre"].startswith("Barcelona. Overall index. Index"):
        pts = sorted((d["Anyo"], d["FK_Periodo"], d["Valor"]) for d in s["Data"])
        print(len(pts), "points; first:", pts[0], "last:", pts[-1])
        months = {}
        for year, month, _ in pts:
            months.setdefault(year, []).append(month)
        print("months per year:", {y: len(m) for y, m in months.items()})
