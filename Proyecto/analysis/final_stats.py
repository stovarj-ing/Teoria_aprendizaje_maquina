import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
# base load: full days, local 00-06
full=["2026-10-07","2026-10-08","2026-10-18","2026-10-19","2026-10-23","2026-10-24","2026-10-25","2026-10-26","2026-10-27","2026-10-28","2026-10-29","2026-10-30","2026-10-31","2026-11-04","2026-11-07","2026-11-08"]
ps=[]; pfs=[]; qs=[]
for d in full:
    a=rd(f"data_zip/Analizador-200_{d}.csv",parse_dates=["ts_local"])
    a["ts"]=pd.to_datetime(a["ts_local"],utc=True).dt.tz_convert("America/Bogota")
    night=a[(a.ts.dt.hour<6)]
    ps.append(night["active_power_total"].median())
    pfs.append(a["power_factor"].median()); qs.append(a["reactive_power_total"].median())
print("night median P per day:",np.round(ps,3))
print("mean night median P:",round(np.mean(ps),3),"-> kWh/day",round(np.mean(ps)*24,1))
print("median PF:",round(np.median(pfs),3),"median Q:",round(np.median(qs),3))
# 201 L2 negative
for meter in ["200","201"]:
    neg=0; tot=0; med=[]
    for d in ["2026-10-08","2026-11-08"]:
        a=rd(f"data_zip/Analizador-{meter}_{d}.csv")
        x=a["active_power_l2"]; neg+=int((x<0).sum()); tot+=len(x); med.append(round(x.median(),3))
    print(meter,"L2 P<0:",neg,"/",tot,"median",med)
# PF correction
P=5.3; pf=0.48
S=P/pf; Q=np.sqrt(S**2-P**2); Qc=P*np.tan(np.arccos(0.95))
print("P",P,"PF",pf,"S",round(S,2),"Q",round(Q,2),"Qc_para_0.95",round(Q-Qc,2),
      "I_actual",round(S*1000/(np.sqrt(3)*208),1),"I_corregida",round((P/0.95)*1000/(np.sqrt(3)*208),1))
