import zipfile, pandas as pd, numpy as np, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
a=rd("data_zip/Analizador-200_2026-10-08.csv",parse_dates=["ts_utc"])
a["ts"]=pd.to_datetime(a["ts_utc"],utc=True).dt.tz_convert("America/Bogota")
a=a.sort_values("ts").set_index("ts")
r=rd("data_zip/Resumen_2026-10-08.csv",parse_dates=["ts_utc"])
r["ts"]=pd.to_datetime(r["ts_utc"],utc=True).dt.tz_convert("America/Bogota")
r=r.sort_values("ts").set_index("ts")
fig,axes=plt.subplots(2,1,figsize=(13,8),sharey=True)
for ax,(t0,t1,title) in zip(axes,[
    ("2026-10-08 14:10","2026-10-08 14:26","Caso A: el pico real NO aparece en el Resumen (se toma la primera muestra del minuto)"),
    ("2026-10-08 16:10","2026-10-08 16:26","Caso B: el mismo tipo de pico SI aparece en el Resumen (se toma la primera muestra del minuto)")]):
    t0=pd.Timestamp(t0,tz="America/Bogota"); t1=pd.Timestamp(t1,tz="America/Bogota")
    s=a.loc[t0:t1,"active_power_total"]
    m=s.resample("1min").mean()
    rr=r.loc[t0:t1,"200_active_power_total"]
    ax.plot(s.index,s.values,"-o",ms=4,lw=1,label="Analizador 200 (cada 10 s)")
    ax.step(m.index,m.values,where="post",lw=2,label="media real del minuto")
    ax.plot(rr.index,rr.values,"rD",ms=8,label="Resumen 1 min (una muestra)")
    ax.set_title(title,fontsize=11)
    ax.set_ylabel("P activa total (kW)")
    ax.legend(loc="upper left",fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
    ax.grid(alpha=.3)
fig.autofmt_xdate()
plt.tight_layout()
plt.savefig("analysis/fig_aliasing.png",dpi=150)
print("saved fig_aliasing.png")
