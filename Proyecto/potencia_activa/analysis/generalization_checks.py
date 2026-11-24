"""Pruebas de generalización del híbrido: brecha, etiquetas barajadas, curva y ablación."""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

ROOT = Path(__file__).resolve().parent.parent
h = pd.read_csv(ROOT / "data" / "processed" / "potencia_horaria.csv", index_col=0)
h.index = pd.to_datetime(h.index, utc=True).tz_convert("America/Bogota")
h = h[["P", "n"]].copy()

H = 24
h["lag1"] = h["P"].shift(1)
h["lag24"] = h["P"].shift(24)
h["lag168"] = h["P"].shift(168)
h["roll3"] = h["P"].rolling(3).mean()
h["roll6"] = h["P"].rolling(6).mean()
h["roll24"] = h["P"].rolling(24).mean()
h["std24"] = h["P"].rolling(24).std()

rows = []
for t in h.index:
    if t + pd.Timedelta(hours=H) > h.index.max():
        break
    p0 = h.loc[t, "P"]
    if np.isnan(p0):
        continue
    def g(col, default):
        v = h.loc[t, col]
        return default if np.isnan(v) else v
    lag24 = g("lag24", p0); lag168 = g("lag168", lag24)
    roll3 = g("roll3", p0); roll6 = g("roll6", p0); roll24 = g("roll24", p0)
    std24 = g("std24", 0.0); lag1 = g("lag1", p0)
    for k in range(1, H + 1):
        tt = t + pd.Timedelta(hours=k)
        y = h.loc[tt, "P"]
        if np.isnan(y):
            continue
        prev_day = h["P"].get(tt - pd.Timedelta(hours=24), np.nan)
        if np.isnan(prev_day):
            continue
        prev_week = h["P"].get(tt - pd.Timedelta(hours=168), np.nan)
        if np.isnan(prev_week):
            prev_week = prev_day
        a1 = 2 * np.pi * tt.hour / 24
        ad = 2 * np.pi * tt.dayofweek / 7
        rows.append({
            "origin_day": t.date(), "horizon": k, "y": y,
            "P_origin": p0, "lag1": lag1, "lag24": lag24, "lag168": lag168,
            "roll3": roll3, "roll6": roll6, "roll24": roll24, "std24": std24,
            "prev_day": prev_day, "prev_week": prev_week,
            "target_hour": tt.hour, "target_dow": tt.dayofweek,
            "target_weekend": int(tt.dayofweek >= 5),
            "origin_hour": t.hour, "origin_dow": t.dayofweek,
            "hour_sin1": np.sin(a1), "hour_cos1": np.cos(a1),
            "hour_sin2": np.sin(2*a1), "hour_cos2": np.cos(2*a1),
            "hour_sin3": np.sin(3*a1), "hour_cos3": np.cos(3*a1),
            "dow_sin": np.sin(ad), "dow_cos": np.cos(ad),
        })

df = pd.DataFrame(rows)
features = ["horizon", "P_origin", "lag1", "lag24", "lag168",
            "roll3", "roll6", "roll24", "std24",
            "prev_day", "prev_week", "target_hour", "target_dow",
            "target_weekend", "origin_hour", "origin_dow",
            "hour_sin1", "hour_cos1", "hour_sin2", "hour_cos2",
            "hour_sin3", "hour_cos3", "dow_sin", "dow_cos"]

days = np.array(sorted(set(df["origin_day"])))
train_days = set(days[:-5]); test_days = set(days[-5:])
tr = df[df.origin_day.isin(train_days)].copy()
te = df[df.origin_day.isin(test_days)].copy()

def fit_hybrid(train, test, feats=features, seed=0):
    clim = train.groupby(["target_hour", "target_weekend"])["y"].mean()
    train = train.copy(); test = test.copy()
    train["clim"] = [clim.get((a, b), train["y"].mean()) for a, b in zip(train.target_hour, train.target_weekend)]
    test["clim"] = [clim.get((a, b), train["y"].mean()) for a, b in zip(test.target_hour, test.target_weekend)]
    train["resid"] = train["y"] - train["clim"]
    gbm = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.03, max_iter=150,
                                        l2_regularization=10.0, min_samples_leaf=30,
                                        random_state=seed)
    gbm.fit(train[feats], train["resid"])
    train_pred = train["clim"] + gbm.predict(train[feats])
    test_pred = test["clim"] + gbm.predict(test[feats])
    return train_pred, test_pred

# 1. Brecha train/test
p_tr, p_te = fit_hybrid(tr, te)
print(f"MAE train {mean_absolute_error(tr.y, p_tr):.4f} | "
      f"MAE test {mean_absolute_error(te.y, p_te):.4f} | "
      f"brecha {mean_absolute_error(te.y, p_te) - mean_absolute_error(tr.y, p_tr):.4f}")
print(f"RMSE test {mean_squared_error(te.y, p_te)**0.5:.4f} | "
      f"MAE media {mean_absolute_error(te.y, np.full(len(te), tr.y.mean())):.4f}")

# 2. Etiquetas barajadas
print("\nEtiquetas barajadas (5 repeticiones):")
scores = []
for seed in range(5):
    tr_sh = tr.copy()
    tr_sh["y"] = np.random.RandomState(seed).permutation(tr_sh["y"].values)
    _, p = fit_hybrid(tr_sh, te, seed=seed)
    scores.append(mean_absolute_error(te.y, p))
print("MAE test media %.4f | rango [%.4f, %.4f] | MAE media %.4f" % (
    np.mean(scores), np.min(scores), np.max(scores),
    mean_absolute_error(te.y, np.full(len(te), tr.y.mean()))))

# 3. Curva de aprendizaje
print("\nCurva de aprendizaje:")
curve = []
for n in [5, 10, 15, 20, 25]:
    dtr = set(days[:n])
    sub = df[df.origin_day.isin(dtr)].copy()
    p_tr, p_te = fit_hybrid(sub, te)
    curve.append({"dias_train": n, "filas_train": len(sub),
                  "MAE_train": mean_absolute_error(sub.y, p_tr),
                  "MAE_test": mean_absolute_error(te.y, p_te)})
print(pd.DataFrame(curve).round(3).to_string(index=False))

# 4. Ablación de features
print("\nAblación (MAE test):")
ablations = {
    "completo": features,
    "sin prev_day": [f for f in features if f != "prev_day"],
    "sin prev_day/prev_week": [f for f in features if f not in ("prev_day", "prev_week")],
    "sin lags": [f for f in features if f not in ("lag1", "lag24", "lag168")],
    "sin calendario": [f for f in features if f not in ("target_hour", "target_dow", "target_weekend",
                                                         "hour_sin1", "hour_cos1", "hour_sin2", "hour_cos2",
                                                         "hour_sin3", "hour_cos3", "dow_sin", "dow_cos")],
}
for name, feats in ablations.items():
    _, p = fit_hybrid(tr, te, feats=feats)
    print(f"  {name:24s} MAE {mean_absolute_error(te.y, p):.4f}")

# 5. Comparación de modelos de residuo
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

def fit_hybrid_model(train, test, model):
    clim = train.groupby(["target_hour", "target_weekend"])["y"].mean()
    train = train.copy(); test = test.copy()
    train["clim"] = [clim.get((a, b), train["y"].mean()) for a, b in zip(train.target_hour, train.target_weekend)]
    test["clim"] = [clim.get((a, b), train["y"].mean()) for a, b in zip(test.target_hour, test.target_weekend)]
    train["resid"] = train["y"] - train["clim"]
    model.fit(train[features], train["resid"])
    return (train["clim"] + model.predict(train[features]),
            test["clim"] + model.predict(test[features]))

print("\nModelos de residuo (último fold):")
models = {
    "ridge": Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))]),
    "gbm_regularizado": HistGradientBoostingRegressor(
        max_depth=3, learning_rate=0.03, max_iter=150, l2_regularization=10.0,
        min_samples_leaf=30, random_state=0),
    "gbm_actual": HistGradientBoostingRegressor(
        max_depth=4, learning_rate=0.03, max_iter=400, l2_regularization=1.0,
        min_samples_leaf=15, random_state=0),
}
for name, model in models.items():
    ptr, pte = fit_hybrid_model(tr, te, model)
    print(f"  {name:18s} train {mean_absolute_error(tr.y, ptr):.4f} | "
          f"test {mean_absolute_error(te.y, pte):.4f} | "
          f"brecha {mean_absolute_error(te.y, pte) - mean_absolute_error(tr.y, ptr):.4f}")
