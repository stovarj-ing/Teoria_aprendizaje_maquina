"""R² por fold y descomposición del último fold por día objetivo."""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

ROOT = Path(__file__).resolve().parent.parent
TAB = ROOT / "reports" / "tables"
TAB.mkdir(parents=True, exist_ok=True)

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
            "origin": t, "target": tt, "origin_day": t.date(), "target_day": tt.date(),
            "horizon": k, "y": y,
            "P_origin": p0, "lag1": lag1, "lag24": lag24, "lag168": lag168,
            "roll3": roll3, "roll6": roll6, "roll24": roll24, "std24": std24,
            "prev_day": prev_day, "prev_week": prev_week,
            "target_hour": tt.hour, "target_dow": tt.dayofweek,
            "target_weekend": int(tt.dayofweek >= 5),
            "origin_hour": t.hour, "origin_dow": t.dayofweek,
            "hour_sin1": np.sin(a1), "hour_cos1": np.cos(a1),
            "hour_sin2": np.sin(2 * a1), "hour_cos2": np.cos(2 * a1),
            "hour_sin3": np.sin(3 * a1), "hour_cos3": np.cos(3 * a1),
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

r2_rows = []
parts = []
for k in range(1, 6):
    train_days = set().union(*blocks[:k])
    test_days = set(blocks[k])
    tr = df[df.origin_day.isin(train_days)].copy()
    te = df[df.origin_day.isin(test_days)].copy()

    clim = tr.groupby(["target_hour", "target_weekend"])["y"].mean()
    for x in (tr, te):
        x["clim"] = [clim.get((a, b), tr["y"].mean())
                     for a, b in zip(x.target_hour, x.target_weekend)]

    tr["resid"] = tr["y"] - tr["clim"]
    gbm_res = HistGradientBoostingRegressor(
        max_depth=3, learning_rate=0.03, max_iter=150,
        l2_regularization=10.0, min_samples_leaf=30, random_state=0)
    gbm_res.fit(tr[features], tr["resid"])
    te["pred_hyb"] = te["clim"] + gbm_res.predict(te[features])

    gbm = HistGradientBoostingRegressor(
        max_depth=4, learning_rate=0.05, max_iter=500,
        l2_regularization=1.0, min_samples_leaf=15, random_state=0)
    gbm.fit(tr[features], tr["y"])
    te["pred_gbm"] = gbm.predict(te[features])

    te["fold"] = k
    parts.append(te)
    r2_rows.append({
        "fold": k,
        "R2_climatologia": r2_score(te["y"], te["clim"]),
        "R2_gbm": r2_score(te["y"], te["pred_gbm"]),
        "R2_hibrido": r2_score(te["y"], te["pred_hyb"]),
        "MAE_test_hibrido": mean_absolute_error(te["y"], te["pred_hyb"]),
        "RMSE_test_hibrido": mean_squared_error(te["y"], te["pred_hyb"]) ** 0.5,
    })

r2 = pd.DataFrame(r2_rows)
r2.to_csv(TAB / "01_r2_folds.csv", index=False)
print("R² por fold")
print(r2.round(4).to_string(index=False))

pred = pd.concat(parts, ignore_index=True)
f5 = pred[pred.fold == 5].copy()

per_day = []
for day, g in f5.groupby("target_day"):
    per_day.append({
        "target_day": day,
        "n": len(g),
        "MAE_hibrido": mean_absolute_error(g["y"], g["pred_hyb"]),
        "MAE_climatologia": mean_absolute_error(g["y"], g["clim"]),
        "sesgo_hibrido": float((g["pred_hyb"] - g["y"]).mean()),
    })
per_day = pd.DataFrame(per_day).sort_values("target_day")
per_day.to_csv(TAB / "01_fold5_por_dia.csv", index=False)
print("\nFold 5 por día objetivo")
print(per_day.round(4).to_string(index=False))

holiday = pd.Timestamp("2026-11-16").date()
no_hol = f5[f5.target_day != holiday]
comp = pd.DataFrame([
    {"conjunto": "fold_5_completo", "n": len(f5),
     "MAE_hibrido": mean_absolute_error(f5["y"], f5["pred_hyb"]),
     "MAE_climatologia": mean_absolute_error(f5["y"], f5["clim"]),
     "R2_hibrido": r2_score(f5["y"], f5["pred_hyb"]),
     "R2_climatologia": r2_score(f5["y"], f5["clim"])},
    {"conjunto": "fold_5_sin_2026-11-16", "n": len(no_hol),
     "MAE_hibrido": mean_absolute_error(no_hol["y"], no_hol["pred_hyb"]),
     "MAE_climatologia": mean_absolute_error(no_hol["y"], no_hol["clim"]),
     "R2_hibrido": r2_score(no_hol["y"], no_hol["pred_hyb"]),
     "R2_climatologia": r2_score(no_hol["y"], no_hol["clim"])},
])
comp.to_csv(TAB / "01_fold5_sin_feriado.csv", index=False)
print("\nFold 5 con y sin el festivo")
print(comp.round(4).to_string(index=False))

train_mae = 0.15003812782728232
full = comp.iloc[0]
no = comp.iloc[1]
print(f"\nBrecha completa: {full.MAE_hibrido - train_mae:.4f}")
print(f"Brecha sin 11-16: {no.MAE_hibrido - train_mae:.4f}")
print(f"Parte de la brecha atribuible a 11-16: "
      f"{(full.MAE_hibrido - no.MAE_hibrido) / (full.MAE_hibrido - train_mae):.1%}")
