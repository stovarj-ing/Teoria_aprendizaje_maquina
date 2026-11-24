import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
names=[n for n in Z.namelist() if re.search(r"/Analizador-\d+_.*\.csv$",n)]
rows=[]
for n in sorted(names):
    m=re.search(r"Analizador-(\d+)_(\d{4}-\d{2}-\d{2})",n)
    meter,day=m.group(1),m.group(2)
    a=rd(n,parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True); a=a.sort_values("ts")
    dt=a["ts"].diff().dt.total_seconds()
    pf=a["power_factor"]; p=a["active_power_total"]; v=a["voltage_vll_avg"]; f=a["frequency"]; i=a["current_avg"]
    rows.append({"meter":meter,"dia":day,"n":len(a),"dup_ts":int(a["ts"].duplicated().sum()),
                 "dt_med":round(dt.median(),1),"dt_max":round(dt.max(),1) if dt.notna().any() else None,
                 "pf_min":round(pf.min(),3),"pf_max":round(pf.max(),3),"pf_gt1":int((pf>1.0001).sum()),
                 "p_min":round(p.min(),3),"p_max":round(p.max(),3),"p_neg":int((p<0).sum()),
                 "v_min":round(v.min(),1),"v_max":round(v.max(),1),
                 "f_min":round(f.min(),3),"f_max":round(f.max(),3),
                 "i_zero_p":int(((i<0.5)&(p>1)).sum())})
t=pd.DataFrame(rows)
print(t.to_string(index=False))
print("\nTOTALS: dup_ts",t.dup_ts.sum(),"pf_gt1",t.pf_gt1.sum(),"p_neg",t.p_neg.sum(),"i_zero_p",t.i_zero_p.sum())
