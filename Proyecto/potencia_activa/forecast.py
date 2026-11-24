"""Funcionalidad de pronóstico: 24 h de potencia activa a partir de la historia reciente."""

import numpy as np
import pandas as pd


def _get(series: pd.Series, ts, default):
    try:
        v = series.loc[ts]
        return float(v) if not pd.isna(v) else default
    except KeyError:
        return default


def forecast_day(history: pd.Series, bundle: dict) -> pd.DataFrame:
    """Pronostica las próximas 24 h desde el último timestamp válido de `history`.

    `history`: serie horaria de potencia (kW), índice datetime local. Puede tener huecos.
    `bundle`: dict con `features`, `clim` (Series multiíndice), `fallback`, `gbm_res`.
    """
    history = history.sort_index()
    history = history[~history.index.duplicated()]
    valid = history.dropna()
    if len(valid) < 24:
        raise ValueError("Se necesitan al menos 24 horas válidas de historia.")
    origin = valid.index[-1]
    p0 = float(valid.iloc[-1])

    # Rejilla horaria completa: los lags son por calendario, no por fila válida
    full = history.reindex(pd.date_range(history.index.min(), history.index.max(), freq="1h"))
    lag1 = _get(full, origin - pd.Timedelta(hours=1), p0)
    lag24 = _get(full, origin - pd.Timedelta(hours=24), p0)
    lag168 = _get(full, origin - pd.Timedelta(hours=168), lag24)
    roll3 = full.loc[origin - pd.Timedelta(hours=2):origin].mean()
    roll6 = full.loc[origin - pd.Timedelta(hours=5):origin].mean()
    roll24 = full.loc[origin - pd.Timedelta(hours=23):origin].mean()
    std24 = full.loc[origin - pd.Timedelta(hours=23):origin].std()
    roll3 = p0 if pd.isna(roll3) else float(roll3)
    roll6 = p0 if pd.isna(roll6) else float(roll6)
    roll24 = p0 if pd.isna(roll24) else float(roll24)
    std24 = 0.0 if pd.isna(std24) else float(std24)

    rows = []
    for k in range(1, 25):
        target = origin + pd.Timedelta(hours=k)
        prev_day = _get(full, target - pd.Timedelta(hours=24), p0)
        prev_week = _get(full, target - pd.Timedelta(hours=168), prev_day)
        a1 = 2 * np.pi * target.hour / 24
        ad = 2 * np.pi * target.dayofweek / 7
        rows.append({
            "horizon": k, "P_origin": p0, "lag1": lag1, "lag24": lag24, "lag168": lag168,
            "roll3": roll3, "roll6": roll6, "roll24": roll24, "std24": std24,
            "prev_day": prev_day, "prev_week": prev_week,
            "target_hour": target.hour, "target_dow": target.dayofweek,
            "target_weekend": int(target.dayofweek >= 5),
            "origin_hour": origin.hour, "origin_dow": origin.dayofweek,
            "hour_sin1": np.sin(a1), "hour_cos1": np.cos(a1),
            "hour_sin2": np.sin(2 * a1), "hour_cos2": np.cos(2 * a1),
            "hour_sin3": np.sin(3 * a1), "hour_cos3": np.cos(3 * a1),
            "dow_sin": np.sin(ad), "dow_cos": np.cos(ad),
        })

    X = pd.DataFrame(rows)
    clim = np.array([bundle["clim"].get((h, w), bundle["fallback"])
                     for h, w in zip(X.target_hour, X.target_weekend)])
    resid = bundle["gbm_res"].predict(X[bundle["features"]])
    out = pd.DataFrame({
        "target": [origin + pd.Timedelta(hours=k) for k in range(1, 25)],
        "P_hat": clim + resid,
        "P_clim": clim,
        "resid_hat": resid,
    })
    out["hora"] = out["target"].dt.strftime("%H:%M")
    return out


def summary_forecast(fc: pd.DataFrame) -> dict:
    idx = fc["P_hat"].idxmax()
    return {
        "energia_kwh": float(fc["P_hat"].sum()),
        "pico_kw": float(fc["P_hat"].max()),
        "hora_pico": str(fc.loc[idx, "target"]),
    }


if __name__ == "__main__":
    import joblib
    from pathlib import Path

    root = Path(__file__).resolve().parent
    h = pd.read_csv(root / "data" / "processed" / "potencia_horaria.csv", index_col=0)
    h.index = pd.to_datetime(h.index, utc=True).tz_convert("America/Bogota")
    bundle = joblib.load(root / "models" / "pronostico_24h.joblib")
    hist = h["P"].dropna()
    fc = forecast_day(hist, bundle)
    print(fc.round(3).to_string(index=False))
    print(summary_forecast(fc))
