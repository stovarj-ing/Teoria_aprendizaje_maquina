import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
ana = {re.search(r"Analizador-200_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Analizador-200_.*\.csv$",n)}
rows=[]
for d,n in sorted(ana.items()):
    a=rd(n,parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True); a=a.sort_values("ts").set_index("ts")
    p=a["active_power_total"]
    base=p.rolling(31,center=True,min_periods=10).median()
    res=p-base
    high=res>2
    dt=a.index.to_series().diff().dt.total_seconds().fillna(10)
    hours=(a.index[-1]-a.index[0]).total_seconds()/3600
    e=a["energy_import"]; de=e.iloc[-1]-e.iloc[0]
    contrib=(res.where(high,0)*dt).sum()/3600
    rows.append({"dia":d,"dow":pd.Timestamp(d).day_name()[:3],"horas":round(hours,1),
                 "n":len(p),"rate_h":round(high.sum()/hours,2),"high_pct":round(100*high.mean(),2),
                 "max_res":round(res.max(),2),"p99_res":round(res.quantile(.99),2),
                 "contrib_kWh":round(contrib,2),"dE_kWh":round(de,1),
                 "contrib_pct":round(100*contrib/de,2) if de else None})
t=pd.DataFrame(rows)
print(t.to_string(index=False))
print("\nweekday mean rate:",round(t[~t.dow.isin(["Sat","Sun"])].rate_h.mean(),2),
      " weekend mean rate:",round(t[t.dow.isin(["Sat","Sun"])].rate_h.mean(),2))
print("weekday mean contrib%:",round(t[~t.dow.isin(["Sat","Sun"])].contrib_pct.mean(),2),
      " weekend:",round(t[t.dow.isin(["Sat","Sun"])].contrib_pct.mean(),2))
