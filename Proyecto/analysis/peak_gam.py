"""Descriptor GAM para el riesgo de pico: base de splines + logística."""

import zipfile
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import SplineTransformer, StandardScaler
from sklearn.metrics import average_precision_score, brier_score_loss

Z = zipfile.ZipFile("analizador 200.zip")
frames = []
for n in Z.namelist():
    if not n.lower().endswith(".csv") or "NILM" in n.upper():
        continue
    with Z.open(n) as f:
        d = pd.read_csv(f)
    if len(d) == 0:
        continue
    d["ts"] = pd.to_datetime(d["ts_utc"], utc=True)
    frames.append(d[["ts", "active_power_total", "current_avg", "voltage_vll_avg",
                     "power_factor", "reactive_power_total"]])

raw = pd.concat(frames).sort_values("ts").drop_duplicates("ts").set_index("ts")
agg = raw.resample("1min").agg({
    "active_power_total": "mean", "current_avg": "mean",
    "voltage_vll_avg": "mean", "power_factor": "mean",
    "reactive_power_total": "mean"})
agg["n"] = raw["active_power_total"].resample("1min").count()
agg = agg.reindex(pd.date_range(agg.index.min(), agg.index.max(), freq="1min", tz="UTC"))

d = agg.copy()
d["P"] = d["active_power_total"]
d["I"] = d["current_avg"]
d["V"] = d["voltage_vll_avg"]
d["PF"] = d["power_factor"]
d["Q"] = d["reactive_power_total"]
for w in [5, 15, 60]:
    d[f"P_mean{w}"] = d["P"].rolling(w, min_periods=max(1, w // 2)).mean()
    d[f"P_max{w}"] = d["P"].rolling(w, min_periods=max(1, w // 2)).max()
    d[f"P_std{w}"] = d["P"].rolling(w, min_periods=max(1, w // 2)).std()
d["Q_over_P"] = d["Q"] / d["P"].replace(0, np.nan)
loc = d.index.tz_convert("America/Bogota")
d["hour"] = loc.hour
d["dow"] = loc.dayofweek
d["is_weekend"] = (d["dow"] >= 5).astype(int)
d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)

H, THR = 15, 12.0
fm = d["P"].rolling(H, min_periods=H).max().shift(-H)
d["Y"] = (fm > THR).astype(float)
d.loc[fm.isna(), "Y"] = np.nan

cont = ["P", "P_max15", "P_mean15", "V", "PF", "Q_over_P", "hour_sin", "hour_cos"]
binv = ["is_weekend"]
data = d.dropna(subset=cont + binv + ["Y"]).copy()
print("Filas", len(data), "positivos", int(data.Y.sum()), "tasa", round(data.Y.mean(), 4))

days = np.array(sorted(set(data.index.tz_convert("America/Bogota").date)))
blocks = np.array_split(days, 6)

def make_gam():
    pre = ColumnTransformer([
        ("spl", SplineTransformer(n_knots=6, degree=3, include_bias=False), cont),
        ("bin", "passthrough", binv),
    ])
    return Pipeline([("pre", pre),
                     ("log", LogisticRegression(C=1.0, max_iter=5000))])

def make_logit():
    pre = ColumnTransformer([
        ("num", StandardScaler(), cont + binv),
    ])
    return Pipeline([("pre", pre),
                     ("log", LogisticRegression(C=1.0, max_iter=5000))])

rows = []
for k in range(1, 6):
    train_days = set().union(*blocks[:k])
    test_days = set(blocks[k])
    tr = data[np.isin(data.index.tz_convert("America/Bogota").date, list(train_days))]
    te = data[np.isin(data.index.tz_convert("America/Bogota").date, list(test_days))]
    for name, model in [("logit", make_logit()), ("gam", make_gam())]:
        model.fit(tr[cont + binv], tr["Y"])
        p = model.predict_proba(te[cont + binv])[:, 1]
        rows.append({"fold": k, "model": name,
                     "PR": round(average_precision_score(te["Y"], p), 4),
                     "Brier": round(brier_score_loss(te["Y"], p), 4),
                     "base": round(te["Y"].mean(), 4)})
    print("fold", k, "ok")

res = pd.DataFrame(rows)
print(res.pivot(index="fold", columns="model", values=["PR", "Brier"]).to_string())
print("\nMedianas:")
print(res.groupby("model")[["PR", "Brier"]].median().round(4).to_string())

# Coeficientes del logit estandarizado en el último fold
tr = data[np.isin(data.index.tz_convert("America/Bogota").date, list(set().union(*blocks[:5])))]
logit = make_logit().fit(tr[cont + binv], tr["Y"])
coefs = pd.Series(logit.named_steps["log"].coef_[0], index=cont + binv).sort_values(key=abs, ascending=False)
print("\nLogit estandarizado (coeficientes):")
print(coefs.round(3).to_string())
print("intercepto:", round(logit.named_steps["log"].intercept_[0], 3))

clean = ["P_max15", "P_mean15", "V", "PF", "hour_sin", "hour_cos", "is_weekend"]
logit_c = Pipeline([("num", StandardScaler()),
                    ("log", LogisticRegression(C=1.0, max_iter=5000))])
logit_c.fit(tr[clean], tr["Y"])
coefs_c = pd.Series(logit_c.named_steps["log"].coef_[0], index=clean).sort_values(key=abs, ascending=False)
print("\nLogit limpio (sin P ni Q/P):")
print(coefs_c.round(3).to_string())
print("intercepto:", round(logit_c.named_steps["log"].intercept_[0], 3))
