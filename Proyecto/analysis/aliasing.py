import zipfile, pandas as pd, numpy as np
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
for d,minutes in [("2026-10-08",["19:16","21:18"]),("2026-10-26",["15:48","20:11"])]:
    a=rd(f"data_zip/Analizador-200_{d}.csv",parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True)
    r=rd(f"data_zip/Resumen_{d}.csv",parse_dates=["ts_utc"]); r["ts"]=pd.to_datetime(r["ts_utc"],utc=True)
    print("="*90); print(d)
    for hm in minutes:
        t=pd.Timestamp(d+" "+hm,tz="UTC")
        sel=a[(a.ts>=t)&(a.ts<t+pd.Timedelta(minutes=1))]
        rv=r[r.ts==t]["200_active_power_total"]
        print(f"\nMinute {hm}  Resumen={rv.iloc[0] if len(rv) else None:.4f}")
        print(sel[["ts","active_power_total","current_avg","power_factor","voltage_vll_avg"]].round(3).to_string(index=False))
        print("minute mean=",round(sel.active_power_total.mean(),3),"max=",round(sel.active_power_total.max(),3),
              "min=",round(sel.active_power_total.min(),3),"n=",len(sel))
