"""Pruebas de generalización: brecha train/test, etiquetas barajadas y curva de aprendizaje."""

import zipfile
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score, brier_score_loss

np.random.seed(0)

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
    frames.append(d[["ts", "active_power_total", "voltage_vll_avg", "power_factor"]])

raw = pd.concat(frames).sort_values("ts").drop_duplicates("ts").set_index("ts")
agg = raw.resample("1min").agg({
    "active_power_total": "mean", "voltage_vll_avg": "mean", "power_factor": "mean"})
agg = agg.reindex(pd.date_range(agg.index.min(), agg.index.max(), freq="1min", tz="UTC"))

d = agg.copy()
d["P"] = d["active_power_total"]
d["V"] = d["voltage_vll_avg"]
d["PF"] = d["power_factor"]
d["P_max15"] = d["P"].rolling(15, min_periods=8).max()
d["P_mean15"] = d["P"].rolling(15, min_periods=8).mean()
loc = d.index.tz_convert("America/Bogota")
d["hour"] = loc.hour
d["is_weekend"] = (loc.dayofweek >= 5).astype(int)
d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)

H, THR = 15, 12.0
fm = d["P"].rolling(H, min_periods=H).max().shift(-H)
d["Y"] = (fm > THR).astype(float)
d.loc[fm.isna(), "Y"] = np.nan

features = ["P_max15", "P_mean15", "V", "PF", "hour_sin", "hour_cos", "is_weekend"]
data = d.dropna(subset=features + ["Y"]).copy()

days = np.array(sorted(set(data.index.tz_convert("America/Bogota").date)))
blocks = np.array_split(days, 6)
train_days = set().union(*blocks[:5])
test_days = set(blocks[5])
tr = data[np.isin(data.index.tz_convert("America/Bogota").date, list(train_days))]
te = data[np.isin(data.index.tz_convert("America/Bogota").date, list(test_days))]


def model():
    return Pipeline([
        ("sc", StandardScaler()),
        ("lr", LogisticRegression(C=1.0, max_iter=5000)),
    ])


m = model().fit(tr[features], tr["Y"])
p_tr = m.predict_proba(tr[features])[:, 1]
p_te = m.predict_proba(te[features])[:, 1]
print("Train: n=%d positivos=%d tasa=%.4f" % (len(tr), tr.Y.sum(), tr.Y.mean()))
print("Test : n=%d positivos=%d tasa=%.4f" % (len(te), te.Y.sum(), te.Y.mean()))
print("PR-AUC train: %.4f | test: %.4f | brecha: %.4f" % (
    average_precision_score(tr.Y, p_tr),
    average_precision_score(te.Y, p_te),
    average_precision_score(tr.Y, p_tr) - average_precision_score(te.Y, p_te)))
print("Brier train: %.4f | test: %.4f" % (
    brier_score_loss(tr.Y, p_tr), brier_score_loss(te.Y, p_te)))

print("\n--- Etiquetas barajadas (5 repeticiones) ---")
scores = []
for i in range(5):
    y_shuf = np.random.permutation(tr["Y"].values)
    ms = model().fit(tr[features], y_shuf)
    ps = ms.predict_proba(te[features])[:, 1]
    scores.append(average_precision_score(te["Y"], ps))
print("PR-AUC con etiquetas barajadas: media=%.4f  rango=[%.4f, %.4f]" % (
    np.mean(scores), np.min(scores), np.max(scores)))

print("\n--- Curva de aprendizaje (entrenando con más días) ---")
curve = []
for n_days in [6, 11, 16, 21, 26]:
    tr_days = set(list(train_days)[:n_days]) if n_days < len(train_days) else train_days
    # usar los primeros n días cronológicos, no un subconjunto arbitrario
    tr_days = set(sorted(train_days)[:n_days])
    sub = data[np.isin(data.index.tz_convert("America/Bogota").date, list(tr_days))]
    m = model().fit(sub[features], sub["Y"])
    p = m.predict_proba(te[features])[:, 1]
    curve.append({"dias_train": n_days, "n_train": len(sub),
                  "PR_train": round(average_precision_score(sub.Y, m.predict_proba(sub[features])[:, 1]), 4),
                  "PR_test": round(average_precision_score(te.Y, p), 4),
                  "Brier_test": round(brier_score_loss(te.Y, p), 4)})
print(pd.DataFrame(curve).to_string(index=False))
