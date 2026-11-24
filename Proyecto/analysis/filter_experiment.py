"""¿Filtrar la potencia ayuda a predecir la próxima ventana? Experimento de ablación."""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy.signal import savgol_filter
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge
from sklearn.metrics import average_precision_score, brier_score_loss, mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data" / "processed" / "medidor200_1min.csv",
                parse_dates=["ts_utc"], index_col="ts_utc")
d.index = pd.to_datetime(d.index, utc=True)
P = d["P"]

# Targets: media y pico de los próximos 15 min
Y_mean = P.rolling(15, min_periods=15).mean().shift(-15)
Y_max = P.rolling(15, min_periods=15).max().shift(-15)
Y_peak = (Y_max > 12).astype(float)
Y_mean_sg_target = None  # se define después del filtro

# Filtros causales
P_ma = P.rolling(15, min_periods=8).mean()
P_ema = P.ewm(span=15, adjust=False).mean()
P_interp = P.interpolate(limit_direction="both")
sg = savgol_filter(P_interp.to_numpy(), 15, 2, mode="interp")
P_sg = pd.Series(sg, index=P.index).shift(7)  # centrado desplazado = causal

Y_mean_sg_target = P_sg.rolling(15, min_periods=15).mean().shift(-15)

d["P_max15"] = P.rolling(15, min_periods=8).max()
d["P_mean15"] = P.rolling(15, min_periods=8).mean()
loc = d.index.tz_convert("America/Bogota")
d["hour"] = loc.hour
d["is_weekend"] = (loc.dayofweek >= 5).astype(int)
d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)

d["P_lag1"] = P.shift(1)
d["P_lag5"] = P.shift(5)
d["P_lag15"] = P.shift(15)
d["P_ma"] = P_ma
d["P_ma_lag1"] = P_ma.shift(1)
d["P_ma_lag5"] = P_ma.shift(5)
d["P_ma_lag15"] = P_ma.shift(15)
d["P_ema"] = P_ema
d["P_sg"] = P_sg
d["P_sg_lag5"] = P_sg.shift(5)
d["Y_mean"] = Y_mean
d["Y_peak"] = Y_peak
d["Y_mean_sg"] = Y_mean_sg_target

common = ["P_max15", "V", "PF", "hour_sin", "hour_cos", "is_weekend"]
raw_feats = common + ["P", "P_lag1", "P_lag5", "P_lag15", "P_mean15"]
ma_feats = common + ["P_ma", "P_ma_lag1", "P_ma_lag5", "P_ma_lag15"]
ema_feats = common + ["P_ema", "P_lag5", "P_lag15"]
sg_feats = common + ["P_sg", "P_sg_lag5", "P_lag15"]

def make_ridge():
    return Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])

def make_logit():
    return Pipeline([("sc", StandardScaler()), ("m", LogisticRegression(C=1.0, max_iter=5000))])

def folds(df):
    days = np.array(sorted(set(df.index.tz_convert("America/Bogota").date)))
    blocks = np.array_split(days, 6)
    for k in range(1, 6):
        tr_days = set().union(*blocks[:k])
        te_days = set(blocks[k])
        tr = df[np.isin(df.index.tz_convert("America/Bogota").date, list(tr_days))]
        te = df[np.isin(df.index.tz_convert("America/Bogota").date, list(te_days))]
        yield tr, te

# ---------- Regresión: media de los próximos 15 min ----------
reg_rows = []
for name, feats in [("crudo", raw_feats), ("MA15", ma_feats), ("EMA15", ema_feats), ("SG15", sg_feats)]:
    for k, (tr, te) in enumerate(folds(d.dropna(subset=feats + ["Y_mean"])), start=1):
        tr = tr.dropna(subset=feats + ["Y_mean"])
        te = te.dropna(subset=feats + ["Y_mean"])
        m = make_ridge().fit(tr[feats], tr["Y_mean"])
        pred = m.predict(te[feats])
        # persistencia: P actual
        pers = te["P"].values
        reg_rows.append({
            "features": name, "fold": k,
            "MAE": mean_absolute_error(te["Y_mean"], pred),
            "RMSE": mean_squared_error(te["Y_mean"], pred) ** 0.5,
            "MAE_pers": mean_absolute_error(te["Y_mean"], pers),
            "skill": 1 - mean_squared_error(te["Y_mean"], pred) / mean_squared_error(te["Y_mean"], pers),
        })
reg = pd.DataFrame(reg_rows)
print("=== Regresión: media de los próximos 15 min (mediana de 5 folds) ===")
print(reg.groupby("features")[["MAE", "RMSE", "MAE_pers", "skill"]].median().round(4).to_string())

# Trampa: entrenar con target suavizado y evaluar contra el target crudo
trap_rows = []
for k, (tr, te) in enumerate(folds(d.dropna(subset=raw_feats + ["Y_mean", "Y_mean_sg"])), start=1):
    tr = tr.dropna(subset=raw_feats + ["Y_mean", "Y_mean_sg"])
    te = te.dropna(subset=raw_feats + ["Y_mean", "Y_mean_sg"])
    m = make_ridge().fit(tr[raw_feats], tr["Y_mean_sg"])
    pred_raw = m.predict(te[raw_feats])
    trap_rows.append({
        "fold": k,
        "MAE_contra_target_suavizado": mean_absolute_error(te["Y_mean_sg"], pred_raw),
        "MAE_contra_target_crudo": mean_absolute_error(te["Y_mean"], pred_raw),
    })
trap = pd.DataFrame(trap_rows)
print("\n=== Trampa: entrenar con target suavizado ===")
print(trap.median().round(4).to_string())
print("(comparar MAE_contra_target_crudo con el MAE de 'crudo' arriba)")

# ---------- Clasificación: pico en los próximos 15 min ----------
clf_rows = []
for name, feats in [("crudo", raw_feats), ("MA15", ma_feats), ("EMA15", ema_feats), ("SG15", sg_feats)]:
    for k, (tr, te) in enumerate(folds(d.dropna(subset=feats + ["Y_peak"])), start=1):
        tr = tr.dropna(subset=feats + ["Y_peak"])
        te = te.dropna(subset=feats + ["Y_peak"])
        m = make_logit().fit(tr[feats], tr["Y_peak"])
        p = m.predict_proba(te[feats])[:, 1]
        clf_rows.append({
            "features": name, "fold": k,
            "PR": average_precision_score(te["Y_peak"], p),
            "Brier": brier_score_loss(te["Y_peak"], p),
            "base": te["Y_peak"].mean(),
        })
clf = pd.DataFrame(clf_rows)
print("\n=== Clasificación: pico >12 kW en los próximos 15 min (mediana de 5 folds) ===")
print(clf.groupby("features")[["PR", "Brier"]].median().round(4).to_string())
print("tasa base mediana:", round(clf.groupby("fold")["base"].first().median(), 4))

reg.to_csv("analysis/filter_experiment_reg.csv", index=False)
clf.to_csv("analysis/filter_experiment_clf.csv", index=False)
trap.to_csv("analysis/filter_experiment_trap.csv", index=False)
print("\nOK")
