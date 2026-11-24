import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
res = {re.search(r"Resumen_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Resumen_.*\.csv$",n)}
ana = {re.search(r"Analizador-200_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Analizador-200_.*\.csv$",n)}
rows=[]
for d in sorted(set(res)&set(ana)):
    a=rd(ana[d],parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True)
    a=a.sort_values("ts").set_index("ts")
    dt=a.index.to_series().diff().dt.total_seconds().fillna(10)
    p=a["active_power_total"]
    pint=(p*dt).sum()/3600
    e=a["energy_import"]
    de=e.iloc[-1]-e.iloc[0]
    r=rd(res[d]); rp=r["200_active_power_total"]
    rint=rp.sum()/60  # 1-min samples, kWh
    rows.append({"dia":d,"horas":round((a.index[-1]-a.index[0]).total_seconds()/3600,2),
                 "dE_kWh":round(de,3),"intP10s_kWh":round(pint,3),"intP1min_kWh":round(rint,3),
                 "ratio10s":round(pint/de,4) if de else None,"ratio1min":round(rint/de,4) if de else None,
                 "P_mean":round(p.mean(),3),"P_median":round(p.median(),3)})
t=pd.DataFrame(rows)
print(t.to_string(index=False))
print("\nmedian ratio 10s:",t.ratio10s.median()," 1min:",t.ratio1min.median())
