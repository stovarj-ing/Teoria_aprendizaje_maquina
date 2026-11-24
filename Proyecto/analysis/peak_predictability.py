"""¿Los picos son predecibles? Experimento con el medidor 200."""

import zipfile
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import average_precision_score, brier_score_loss, precision_score, recall_score
from sklearn.inspection import permutation_importance

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
                     "power_factor", "reactive_power_total", "frequency"]])

raw = pd.concat(frames).sort_values("ts").drop_duplicates("ts").set_index("ts")
local = raw.index.tz_convert("America/Bogota")

agg = raw.resample("1min").agg({
    "active_power_total": "mean",
    "current_avg": "mean",
    "voltage_vll_avg": "mean",
    "power_factor": "mean",
    "reactive_power_total": "mean",
    "frequency": "mean",
})
agg["n"] = raw["active_power_total"].resample("1min").count()
full = pd.date_range(agg.index.min(), agg.index.max(), freq="1min", tz="UTC")
agg = agg.reindex(full)

d = agg.copy()
d["P"] = d["active_power_total"]
d["I"] = d["current_avg"]
d["V"] = d["voltage_vll_avg"]
d["PF"] = d["power_factor"]
d["Q"] = d["reactive_power_total"]
d["F"] = d["frequency"]

for k in [1, 5, 15, 60]:
    d[f"P_lag{k}"] = d["P"].shift(k)
    d[f"I_lag{k}"] = d["I"].shift(k)
    d[f"PF_lag{k}"] = d["PF"].shift(k)
for w in [5, 15, 60]:
    d[f"P_mean{w}"] = d["P"].rolling(w, min_periods=max(1, w // 2)).mean()
    d[f"P_max{w}"] = d["P"].rolling(w, min_periods=max(1, w // 2)).max()
    d[f"P_std{w}"] = d["P"].rolling(w, min_periods=max(1, w // 2)).std()
d["P_slope15"] = d["P"] - d["P_lag15"]
d["Q_over_P"] = d["Q"] / d["P"].replace(0, np.nan)

loc = d.index.tz_convert("America/Bogota")
d["hour"] = loc.hour
d["dow"] = loc.dayofweek
d["is_weekend"] = (d["dow"] >= 5).astype(int)
d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)

H = 15
THR = 12.0
future_max = d["P"].rolling(H, min_periods=H).max().shift(-H)
d["Y"] = (future_max > THR).astype(float)
d.loc[future_max.isna(), "Y"] = np.nan

features = [
    "P", "I", "V", "PF", "Q", "F", "n",
    "P_lag1", "P_lag5", "P_lag15", "P_lag60",
    "I_lag1", "I_lag5", "PF_lag1", "PF_lag15",
    "P_mean5", "P_mean15", "P_mean60",
    "P_max5", "P_max15", "P_max60",
    "P_std5", "P_std15", "P_std60",
    "P_slope15", "Q_over_P",
    "hour_sin", "hour_cos", "dow", "is_weekend",
]

data = d.dropna(subset=features + ["Y"]).copy()
print("Filas utiles:", len(data), "| desde", data.index.min(), "hasta", data.index.max())
print("Tasa base Y:", round(data["Y"].mean(), 4), "| positivos:", int(data["Y"].sum()))

# Relación contemporánea y condicional
print("\n--- P(Y=1 | P actual) ---")
bins = [0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20]
data["P_bin"] = pd.cut(data["P"], bins)
print(data.groupby("P_bin", observed=True)["Y"].agg(["mean", "count"]).round(4).to_string())

print("\n--- Correlación de Y con variables (punto-biserial) ---")
corr = data[features + ["Y"]].corr()["Y"].drop("Y").sort_values(ascending=False)
print(corr.round(3).to_string())

# Precursor: promedio 15 min antes de un onset
print("\n--- Precursor: promedio en los minutos previos a un pico ---")
onsets = data[(data["Y"] == 1) & (data["Y"].shift(1) == 0)].index
print("onsets:", len(onsets))
rows = []
for off in [-15, -10, -5, -1, 0]:
    idx = onsets + pd.Timedelta(minutes=off)
    sub = data.reindex(idx)
    rows.append({"offset_min": off,
                 "P": sub["P"].mean(), "I": sub["I"].mean(),
                 "PF": sub["PF"].mean(), "Q": sub["Q"].mean(),
                 "V": sub["V"].mean()})
print(pd.DataFrame(rows).round(3).to_string(index=False))
print("Promedio global:", data[["P", "I", "PF", "Q", "V"]].mean().round(3).to_dict())

# Validación rolling-origin por bloques de días
days = np.array(sorted(set(data.index.tz_convert("America/Bogota").date)))
blocks = np.array_split(days, 6)
print("\n--- Validación rolling-origin (5 folds) ---")
print("Días por bloque:", [len(b) for b in blocks])

results = []
for k in range(1, 6):
    train_days = set().union(*blocks[:k])
    test_days = set(blocks[k])
    tr = data[np.isin(data.index.tz_convert("America/Bogota").date, list(train_days))]
    te = data[np.isin(data.index.tz_convert("America/Bogota").date, list(test_days))]
    Xtr, ytr = tr[features], tr["Y"]
    Xte, yte = te[features], te["Y"]

    base = ytr.mean()
    # Persistencia: usar la P actual como score
    pr_pers = average_precision_score(yte, te["P"])
    br_pers = brier_score_loss(yte, np.clip(te["P"] / 20, 0, 1))

    log = make_pipeline(StandardScaler(),
                        LogisticRegression(max_iter=2000, class_weight="balanced"))
    log.fit(Xtr, ytr)
    pl = log.predict_proba(Xte)[:, 1]

    gbm = HistGradientBoostingClassifier(
        max_depth=3, learning_rate=0.05, max_iter=400,
        l2_regularization=1.0, min_samples_leaf=50, random_state=0)
    gbm.fit(Xtr, ytr)
    pg = gbm.predict_proba(Xte)[:, 1]

    row = {
        "fold": k, "train_days": len(train_days), "test_days": len(test_days),
        "n_test": len(te), "base_rate": round(yte.mean(), 4),
        "PR_base": round(base, 4),
        "PR_persist": round(pr_pers, 4),
        "PR_log": round(average_precision_score(yte, pl), 4),
        "PR_gbm": round(average_precision_score(yte, pg), 4),
        "Brier_log": round(brier_score_loss(yte, pl), 4),
        "Brier_gbm": round(brier_score_loss(yte, pg), 4),
        "Brier_persist": round(br_pers, 4),
    }
    for th in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
        pred = (pg >= th).astype(int)
        row[f"prec_{th}"] = round(precision_score(yte, pred, zero_division=0), 4)
        row[f"rec_{th}"] = round(recall_score(yte, pred, zero_division=0), 4)
        row[f"alert_{th}"] = round(pred.mean(), 4)
    results.append(row)

res = pd.DataFrame(results)
print(res.to_string(index=False))
print("\nMedianas:")
print(res[["PR_base", "PR_persist", "PR_log", "PR_gbm",
           "Brier_log", "Brier_gbm", "Brier_persist"]].median().round(4).to_string())

print("\n--- GBM: precisión / recall / tasa de alerta por umbral (medianas) ---")
for th in [0.2, 0.3, 0.4, 0.5, 0.6, 0.7]:
    print(f"th={th:.1f}  precision={res[f'prec_{th}'].median():.3f}  "
          f"recall={res[f'rec_{th}'].median():.3f}  "
          f"alert_rate={res[f'alert_{th}'].median():.3f}")

# Importancia de variables en el último fold
tr = data[np.isin(data.index.tz_convert("America/Bogota").date, list(set().union(*blocks[:5])))]
te = data[np.isin(data.index.tz_convert("America/Bogota").date, list(set(blocks[5])))]
gbm = HistGradientBoostingClassifier(
    max_depth=3, learning_rate=0.05, max_iter=400,
    l2_regularization=1.0, min_samples_leaf=50, random_state=0)
gbm.fit(tr[features], tr["Y"])
imp = permutation_importance(gbm, te[features], te["Y"],
                             n_repeats=5, random_state=0,
                             scoring="average_precision")
imp = pd.DataFrame({"feature": features, "importance": imp.importances_mean,
                    "std": imp.importances_std}).sort_values("importance", ascending=False)
print("\n--- Importancia por permutación (último fold) ---")
print(imp.head(15).round(4).to_string(index=False))

# Guardar resumen
res.to_csv("analysis/peak_predictability_folds.csv", index=False)
imp.to_csv("analysis/peak_predictability_importance.csv", index=False)
data[["P", "I", "PF", "Q", "V", "Y"]].to_csv("analysis/peak_predictability_data.csv")
print("\nOK")
