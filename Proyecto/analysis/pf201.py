import zipfile, pandas as pd, numpy as np
Z = zipfile.ZipFile(r"data_zip.zip")
def rd(n, **k):
    with Z.open(n) as f: return pd.read_csv(f, **k)
for meter in ["200","201"]:
    a=rd(f"data_zip/Analizador-{meter}_2026-11-08.csv")
    p=a[f"active_power_total"]; s=a[f"apparent_power_total"]; pf=a[f"power_factor"]
    q=a[f"reactive_power_total"]
    print("="*70); print("meter",meter,"n",len(a))
    print("PF describe"); print(pf.describe().round(4).to_string())
    for name,x in [("P/S",p/s),("S/P",s/p),("1/PF",1/pf),("Q/P",q/p),("sqrt(S2-P2)/P",np.sqrt((s*s-p*p).clip(lower=0))/p)]:
        print(f"{name:16s} median={x.median():.4f} corr_with_PF={x.corr(pf):.4f}")
    # per-phase PF
    for ph in ["l1","l2","l3"]:
        vln=a[f"voltage_v{ {'l1':'an','l2':'bn','l3':'cn'}[ph] }"]
        iph=a[f"current_{ph}"]
        spp=vln*iph/1000
        ppp=a[f"active_power_{ph}"]
        r=(ppp/spp)
        print(f"  phase {ph}: median P/(Vln*I)={r.median():.4f}  corr_with_PF={r.corr(pf):.4f}")
