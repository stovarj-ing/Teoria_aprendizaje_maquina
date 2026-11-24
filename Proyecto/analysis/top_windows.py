import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
ana = {re.search(r"Analizador-200_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Analizador-200_.*\.csv$",n)}
events=[("2026-10-26","2026-10-26 15:48"),("2026-10-19","2026-10-19 18:21"),
        ("2026-10-30","2026-10-30 16:47"),("2026-10-27","2026-10-27 18:33"),
        ("2026-10-26","2026-10-26 20:11")]
for d,t in events:
    a=rd(ana[d],parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True); a=a.sort_values("ts").set_index("ts")
    tt=pd.Timestamp(t,tz="UTC")
    w=a.loc[tt-pd.Timedelta(minutes=2):tt+pd.Timedelta(minutes=2),
            ["active_power_total","active_power_l1","active_power_l2","active_power_l3",
             "current_avg","apparent_power_total","reactive_power_total","power_factor","voltage_vll_avg"]]
    print("\n"+"="*100); print("EVENT",t," cadence",a.index.to_series().diff().dt.total_seconds().median(),"s")
    print(w.round(3).to_string())
