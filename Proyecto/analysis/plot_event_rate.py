import zipfile, pandas as pd, numpy as np, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
ana = {re.search(r"Analizador-200_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Analizador-200_.*\.csv$",n)}
rows=[]
for d,n in sorted(ana.items()):
    a=rd(n,parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True); a=a.sort_values("ts").set_index("ts")
    p=a["active_power_total"]; base=p.rolling(31,center=True,min_periods=10).median(); res=p-base
    dt=a.index.to_series().diff().dt.total_seconds().fillna(10)
    high=res>2; hours=(a.index[-1]-a.index[0]).total_seconds()/3600
    e=a["energy_import"]; de=e.iloc[-1]-e.iloc[0]
    rows.append({"dia":d,"dow":pd.Timestamp(d).day_name()[:3],"rate_h":high.sum()/hours,
                 "contrib_pct":100*(res.where(high,0)*dt).sum()/3600/de if de else np.nan,
                 "dE":de,"intP":(p*dt).sum()/3600,"max_res":res.max()})
t=pd.DataFrame(rows); t["weekend"]=t.dow.isin(["Sat","Sun"])
t.to_csv("analysis/event_rate_table.csv",index=False)
fig,axes=plt.subplots(1,2,figsize=(15,5.5))
ax=axes[0]; cols=np.where(t.weekend,"#e08a3c","#2f6db3")
ax.bar(range(len(t)),t.rate_h,color=cols)
ax.set_xticks(range(len(t))); ax.set_xticklabels([x[5:] for x in t.dia],rotation=60,fontsize=8)
ax.set_ylabel("eventos >2 kW sobre la base local por hora")
ax.set_title("Tasa de eventos por dia (azul=laboral, naranja=fin de semana)")
ax.axhline(t[~t.weekend].rate_h.mean(),color="#2f6db3",ls="--",lw=1,label="media laboral")
ax.axhline(t[t.weekend].rate_h.mean(),color="#e08a3c",ls="--",lw=1,label="media fin de semana")
ax.legend(fontsize=8); ax.grid(axis="y",alpha=.3)
ax=axes[1]
ax.scatter(t.dE,t.intP,s=45,c=cols,zorder=3)
lim=[min(t.dE.min(),t.intP.min())*.95,max(t.dE.max(),t.intP.max())*1.03]
ax.plot(lim,lim,"k--",lw=1,label="1:1")
for _,row in t.iterrows():
    if abs(row.intP/row.dE-1)>0.02:
        ax.annotate(row.dia[5:],(row.dE,row.intP),textcoords="offset points",xytext=(6,-10),fontsize=8)
ax.set_xlabel("delta energy_import del medidor (kWh)")
ax.set_ylabel("integral de P de las muestras (kWh)")
ax.set_title("Balance de energia: integral de P vs contador")
ax.legend(fontsize=8); ax.grid(alpha=.3)
plt.tight_layout(); plt.savefig("analysis/fig_rate_energy.png",dpi=150)
print("saved")
print(t[["dia","dow","rate_h","contrib_pct"]].round(2).to_string(index=False))
