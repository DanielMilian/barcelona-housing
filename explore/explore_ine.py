import sys

import requests
import pandas as pd

TABLE_ID=sys.argv[1] if len(sys.argv) > 1 else "67536"
url=f"https://servicios.ine.es/wstempus/js/en/DATOS_TABLA/{TABLE_ID}"

r = requests.get(url, params={"nult":2}, timeout=60)
r.raise_for_status()
data = r.json()
if not isinstance(data, list):
    raise SystemExit(f"Unexpected response: {str(data)[:300]}")

rows = [
        {"series": s["Nombre"], "period": d["NombrePeriodo"], "value": d["Valor"], "secret": d["Secreto"]}
        for s in data
        for d in s["Data"]
        ]

df = pd.DataFrame(rows)

print(f"{len(data)} series, {len(df)} points, {df['value'].isna().sum()} null values")
print(df.head(10).to_string())


