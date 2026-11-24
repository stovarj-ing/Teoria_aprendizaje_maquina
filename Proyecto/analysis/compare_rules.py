import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
res = {re.search(r"Resumen_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Resumen_.*\.csv$",n)}
ana = {re.search(r"Analizador-200_(\d{4}-\d{2}-\d{2})",n).group(1): n for n in Z.namelist() if re.search(r"/Analizador-200_.*\.csv$",n)}
rows=[]
for d in sorted(set(res)&set(ana)):
    r=rd(res[d],parse_dates=["ts_utc"]); a=rd(ana[d],parse_dates=["ts_utc"])
    r["ts"]=pd.to_datetime(r["ts_utc"],utc=True); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True)
    r=r.set_index("ts").sort_index(); a=a.set_index("ts").sort_index()
    rr=r["200_active_power_total"]
    out={"dia":d,"n_res":len(rr)}
    for how in ["first","mean","last"]:
        s=getattr(a["active_power_total"].resample("1min"),how)()
        j=pd.concat([rr.rename("r"),s.rename("a")],axis=1,sort=True).dropna()
        out[how+"_mae"]=round((j.r-j.a).abs().mean(),3)
        out[how+"_corr"]=round(j.r.corr(j.a),4)
    rows.append(out)
t=pd.DataFrame(rows)
print(t.to_string(index=False))
print("\nmedian MAE by rule:")
print(t[["first_mae","mean_mae","last_mae"]].median())
print("median corr by rule:")
print(t[["first_corr","mean_corr","last_corr"]].median())
