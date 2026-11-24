import zipfile, pandas as pd, numpy as np, re
from pathlib import Path
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
names = [n for n in Z.namelist() if re.search(r"/Resumen_.*\.csv$", n)]
frames = []
for n in names:
    d = rd(n)
    d["ts"] = pd.to_datetime(d["ts_utc"], utc=True)
    frames.append(d[["ts","200_active_power_total","200_active_power_l1","200_active_power_l2","200_active_power_l3",
                     "200_current_avg","200_current_l1","200_current_l2","200_current_l3",
                     "200_apparent_power_total","200_reactive_power_total","200_power_factor",
                     "200_voltage_vll_avg","200_voltage_vln_avg","200_frequency","200_energy_import","200_energy_export"]])
df = pd.concat(frames).sort_values("ts").reset_index(drop=True)
df = df.rename(columns=lambda c: c.replace("200_",""))
df["base"] = df["active_power_total"].rolling(31, center=True, min_periods=10).median()
df["resid"] = df["active_power_total"] - df["base"]
print("rows", len(df), "range", df.ts.min(), df.ts.max())
print(df["active_power_total"].describe(percentiles=[.01,.05,.25,.5,.75,.95,.99]).round(3))
print("\nTOP +resid")
cols=["ts","active_power_total","base","resid","current_avg","apparent_power_total","power_factor","voltage_vll_avg","frequency"]
print(df.nlargest(15,"resid")[cols].to_string(index=False))
print("\nTOP -resid")
print(df.nsmallest(15,"resid")[cols].to_string(index=False))
df.to_pickle("analysis/resumen200.pkl")
