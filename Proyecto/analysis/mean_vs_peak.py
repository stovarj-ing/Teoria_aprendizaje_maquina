"""¿Un buen pronóstico de la media sirve para detectar picos? Evidencia."""

import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
d = pd.read_csv(ROOT / "data" / "processed" / "medidor200_1min.csv",
                parse_dates=["ts_utc"], index_col="ts_utc")
d.index = pd.to_datetime(d.index, utc=True)
P = d["P"]

d["P_max15"] = P.rolling(15, min_periods=8).max()
d["P_mean15"] = P.rolling(15, min_periods=8).mean()
loc = d.index.tz_convert("America/Bogota")
d["hour"] = loc.hour
d["is_weekend"] = (loc.dayofweek >= 5).astype(int)
d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)
d["Y_mean"] = P.rolling(15, min_periods=15).mean().shift(-15)
d["Y_max"] = P.rolling(15, min_periods=15).max().shift(-15)
d["Y_peak"] = (d["Y_max"] > 12).astype(float)

features = ["P_max15", "P_mean15", "V", "PF", "hour_sin", "hour_cos", "is_weekend"]
data = d.dropna(subset=features + ["Y_mean", "Y_max", "Y_peak"]).copy()

days = np.array(sorted(set(data.index.tz_convert("America/Bogota").date)))
blocks = np.array_split(days, 6)
dev_days = set().union(*blocks[:5])
hold_days = set(blocks[5])
dev = data[np.isin(data.index.tz_convert("America/Bogota").date, list(dev_days))]
hold = data[np.isin(data.index.tz_convert("America/Bogota").date, list(hold_days))]

model = Pipeline([("sc", StandardScaler()), ("m", Ridge(alpha=1.0))])
model.fit(dev[features], dev["Y_mean"])
pred = model.predict(hold[features])
hold = hold.assign(pred=pred)

mae = mean_absolute_error(hold["Y_mean"], pred)
rmse = mean_squared_error(hold["Y_mean"], pred) ** 0.5
mae_p = mean_absolute_error(hold["Y_mean"], hold["P"])
print(f"Holdout: MAE {mae:.4f} | RMSE {rmse:.4f} | MAE persistencia {mae_p:.4f} | "
      f"skill {1 - mean_squared_error(hold['Y_mean'], pred)/mean_squared_error(hold['Y_mean'], hold['P']):.4f}")

print("\nSesgo por valor real del máximo futuro:")
bins = [0, 8, 10, 12, 14, 20]
hold["bin_max"] = pd.cut(hold["Y_max"], bins)
g = hold.groupby("bin_max", observed=True).agg(
    n=("pred", "size"),
    Y_mean=("Y_mean", "mean"),
    Y_max=("Y_max", "mean"),
    pred=("pred", "mean"),
)
g["pred_menos_Ymean"] = g["pred"] - g["Y_mean"]
g["Ymax_menos_pred"] = g["Y_max"] - g["pred"]
print(g.round(3).to_string())

print("\nCobertura de picos si se alerta con el pronóstico de la media:")
for thr in [8, 9, 10, 11, 12]:
    alert = hold["pred"] >= thr
    tp = int((alert & (hold["Y_peak"] == 1)).sum())
    fp = int((alert & (hold["Y_peak"] == 0)).sum())
    fn = int((~alert & (hold["Y_peak"] == 1)).sum())
    print(f"  umbral {thr:>2}: precision {tp/(tp+fp) if tp+fp else 0:.3f} | "
          f"recall {tp/(tp+fn) if tp+fn else 0:.3f} | alertas {alert.mean()*100:.1f}% | "
          f"TP {tp} FP {fp} FN {fn}")

print("\nDistribución del pronóstico en filas con pico real:")
print(hold.loc[hold.Y_peak == 1, ["pred", "Y_mean", "Y_max"]].describe().round(3).to_string())
