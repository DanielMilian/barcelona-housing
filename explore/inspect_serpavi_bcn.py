import sys

import pandas as pd

path = sys.argv[1]

meta = pd.read_excel(path, sheet_name="Metadatos", header=None)
print(meta.to_string(max_colwidth=120))

df = pd.read_excel(path, sheet_name="Distritos", dtype={"CPRO": str, "CUMUN": str, "CUDIS": str})
bcn = df[df["CUMUN"] == "08019"]
print(f"\n{len(bcn)} Barcelona districts:", list(bcn["CUDIS"]))

for metric in ("BI_ALVHEPCO_TVC", "ALQM2_LV_M_VC", "ALQTBID12_M_VC"):
    cols = [f"{metric}_{y}" for y in range(11, 25) if f"{metric}_{y}" in bcn.columns]
    print(f"\n{metric}")
    print(bcn.set_index("CUDIS")[cols].round(1).to_string())
