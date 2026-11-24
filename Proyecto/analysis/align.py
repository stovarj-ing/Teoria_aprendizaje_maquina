import zipfile, pandas as pd
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
for d in ["2026-10-08","2026-10-18"]:
    r=rd(f"data_zip/Resumen_{d}.csv",parse_dates=["ts_utc"])
    a=rd(f"data_zip/Analizador-200_{d}.csv",parse_dates=["ts_utc"])
    r["ts"]=pd.to_datetime(r["ts_utc"],utc=True); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True)
    print("="*80); print(d)
    print("Resumen first rows:")
    print(r[["ts","200_active_power_total"]].head(6).to_string(index=False))
    print("Analizador first rows:")
    print(a[["ts","active_power_total"]].head(10).to_string(index=False))
    # exact match search for first resumen value in analyzer
    v=r["200_active_power_total"].iloc[0]
    m=a[a["active_power_total"].round(4)==round(v,4)]
    print("matches for first Resumen value",v,":",len(m))
    print(m[["ts","active_power_total"]].head(5).to_string(index=False))
