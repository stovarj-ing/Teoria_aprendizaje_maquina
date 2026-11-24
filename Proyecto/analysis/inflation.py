import zipfile, pandas as pd, numpy as np, re
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
for d,resn in [("2026-10-08","data_zip/Resumen_2026-10-08.csv"),("2026-10-26","data_zip/Resumen_2026-10-26.csv")]:
    a=rd(f"data_zip/Analizador-200_{d}.csv",parse_dates=["ts_utc"]); a["ts"]=pd.to_datetime(a["ts_utc"],utc=True); a=a.sort_values("ts").set_index("ts")
    r=rd(resn,parse_dates=["ts_utc"]); r["ts"]=pd.to_datetime(r["ts_utc"],utc=True); r=r.set_index("ts")
    g=a["active_power_total"].resample("1min")
    m=pd.DataFrame({"mean":g.mean(),"max":g.max(),"min":g.min(),"n":g.count()})
    m["ratio_max"]=m["max"]/m["mean"]; m["ratio_min"]=m["min"]/m["mean"]
    print("="*80); print(d)
    print("ratio max/mean percentiles:",m["ratio_max"].quantile([.5,.9,.95,.99]).round(3).to_dict())
    print("ratio min/mean percentiles:",m["ratio_min"].quantile([.5,.1,.05,.01]).round(3).to_dict())
    print("minutes with max-mean>3kW:",int(((m["max"]-m["mean"])>3).sum()),"of",len(m))
    # top resumen peaks
    top=r["200_active_power_total"].nlargest(8)
    out=[]
    for t,v in top.items():
        mm=m.loc[m.index.floor("min")==t.floor("min")]
        if len(mm):
            row=mm.iloc[0]
            out.append({"t":t,"res":round(v,3),"min_mean":round(row["mean"],3),"min_max":round(row["max"],3),
                        "infl_vs_mean_pct":round(100*(v/row["mean"]-1),1)})
    print(pd.DataFrame(out).to_string(index=False))
