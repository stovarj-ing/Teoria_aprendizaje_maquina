"""¿Un modelo híbrido climatología + GBM de residuos mejora el pronóstico a 24 h?"""

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
            "origin": t, "target": tt, "origin_day": t.date(), "horizon": k,
            "y": y, "P_origin": p0, "lag1": lag1, "lag24": lag24, "lag168": lag168,
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
blocks = np.array_split(days, 6)
rows_out = []
for k in range(1, 6):
    tr_days = set().union(*blocks[:k]); te_days = set(blocks[k])
    tr = df[df.origin_day.isin(tr_days)].copy()
    te = df[df.origin_day.isin(te_days)].copy()
    if len(te) == 0:
        continue

    clim = tr.groupby(["target_hour", "target_weekend"])["y"].mean()
    tr["clim"] = [clim.get((a, b), tr["y"].mean()) for a, b in zip(tr.target_hour, tr.target_weekend)]
    te["clim"] = [clim.get((a, b), tr["y"].mean()) for a, b in zip(te.target_hour, te.target_weekend)]

    gbm = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.05, max_iter=500,
                                        l2_regularization=1.0, min_samples_leaf=15,
                                        random_state=0)
    gbm.fit(tr[features], tr["y"])
    te["pred_gbm"] = gbm.predict(te[features])

    # Híbrido: GBM sobre el residuo de la climatología
    tr["resid"] = tr["y"] - tr["clim"]
    gbm_res = HistGradientBoostingRegressor(max_depth=4, learning_rate=0.03, max_iter=400,
                                            l2_regularization=1.0, min_samples_leaf=15,
                                            random_state=0)
    gbm_res.fit(tr[features], tr["resid"])
    te["pred_hyb"] = te["clim"] + gbm_res.predict(te[features])

    for name, pred in [("climatologia", te["clim"]), ("gbm", te["pred_gbm"]),
                       ("hibrido", te["pred_hyb"])]:
        rows_out.append({"fold": k, "modelo": name, "MAE": mean_absolute_error(te["y"], pred),
                         "RMSE": mean_squared_error(te["y"], pred) ** 0.5, "n": len(te)})

res = pd.DataFrame(rows_out)
print(res.pivot(index="fold", columns="modelo", values="MAE").round(3).to_string())
print("\nMedianas:")
print(res.groupby("modelo")[["MAE", "RMSE"]].median().round(3).to_string())
