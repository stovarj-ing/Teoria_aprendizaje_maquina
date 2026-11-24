"""Genera y ejecuta los notebooks 01 y 02 del proyecto."""

from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
MD = new_markdown_cell
CODE = new_code_cell


def build(cells, filename):
    path = ROOT / filename
    nb = new_notebook(
        cells=cells,
        metadata={
            "kernelspec": {"display_name": "Python 3", "language": "python",
                           "name": "python3"},
            "language_info": {"name": "python"},
        },
    )
    nbformat.write(nb, path)
    print(f"Ejecutando {filename} ...")
    client = NotebookClient(
        nb, timeout=900, kernel_name="python3",
        resources={"metadata": {"path": str(ROOT)}},
    )
    try:
        client.execute()
        nbformat.write(nb, path)
        print(f"OK {filename}")
    except Exception as exc:
        nbformat.write(nb, path)
        print(f"ERROR en {filename}: {exc}")
        raise


# =========================================================================
# 01 — Auditoría y pipeline
# =========================================================================
cells_01 = [
    MD("""# 01 · Auditoría y pipeline de datos

**Objetivo:** leer los ZIP del analizador 200 y 201, construir la serie de 1 min como media de las muestras de alta resolución, auditar huecos/cadencia y validar la física.

**Entradas:** `analizador 200.zip`, `analizador 201.zip` en la raíz del proyecto.

**Salidas:** `data/processed/medidor200_1min.csv`, tablas y figuras en `reports/`.
"""),
    CODE("""import io, re, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import display

pd.set_option("display.width", 170)
pd.set_option("display.max_columns", 60)
plt.rcParams.update({"figure.figsize": (12, 4.5), "axes.grid": True, "grid.alpha": 0.3})

ROOT = Path(".").resolve()
Z200 = ROOT / "analizador 200.zip"
Z201 = ROOT / "analizador 201.zip"
OUT = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
for p in (OUT, FIG, TAB):
    p.mkdir(parents=True, exist_ok=True)
print("ZIP 200:", Z200.exists(), "| ZIP 201:", Z201.exists())"""),
    MD("""## 1. Inventario de archivos

Se leen solo los CSV del analizador (no los XLSX ni los NILM) y se descartan los archivos vacíos (solo encabezado)."""),
    CODE("""def read_analyzer_zip(zpath, meter):
    z = zipfile.ZipFile(zpath)
    frames, inv = [], []
    for name in z.namelist():
        if not name.lower().endswith(".csv") or "nilm" in name.lower():
            continue
        with z.open(name) as f:
            d = pd.read_csv(f)
        if len(d) == 0:
            continue
        d["ts_utc"] = pd.to_datetime(d["ts_utc"], utc=True)
        d = d.sort_values("ts_utc")
        dt = d["ts_utc"].diff().dt.total_seconds()
        inv.append({
            "archivo": name.split("/")[-1],
            "filas": len(d),
            "inicio": d["ts_utc"].min(),
            "fin": d["ts_utc"].max(),
            "dt_med_s": dt.median(),
            "dt_max_s": dt.max(),
            "pf_max": d["power_factor"].max(),
            "pf_gt1": int((d["power_factor"] > 1.0001).sum()),
        })
        d["archivo"] = name.split("/")[-1]
        frames.append(d)
    data = pd.concat(frames, ignore_index=True).sort_values("ts_utc")
    return data, pd.DataFrame(inv)

raw200, inv200 = read_analyzer_zip(Z200, "200")
raw201, inv201 = read_analyzer_zip(Z201, "201")
print(f"200: {len(raw200):,} filas | {raw200.ts_utc.min()} -> {raw200.ts_utc.max()}")
print(f"201: {len(raw201):,} filas | {raw201.ts_utc.min()} -> {raw201.ts_utc.max()}")
display(inv200.sort_values("inicio").head(40).round(1))
display(inv201.sort_values("inicio").head(40).round(1))"""),
    MD("""## 2. Serie de 1 min

Cada minuto se calcula como **media** de las muestras disponibles. `n` es la cantidad de muestras por minuto: 6–7 en días de 8–10 s, 2 en días de 30 s, 0 en huecos. Un minuto con `n = 0` es un hueco y no se imputa."""),
    CODE("""def build_1min(raw, meter):
    raw = raw.drop_duplicates("ts_utc").set_index("ts_utc").sort_index()
    cols = {
        "active_power_total": "P", "current_avg": "I",
        "voltage_vll_avg": "V", "power_factor": "PF",
        "reactive_power_total": "Q", "apparent_power_total": "S",
        "frequency": "F",
    }
    agg = raw[list(cols)].resample("1min").mean().rename(columns=cols)
    agg["n"] = raw["active_power_total"].resample("1min").count()
    full = pd.date_range(agg.index.min(), agg.index.max(), freq="1min", tz="UTC")
    agg = agg.reindex(full)
    agg["gap"] = agg["n"].fillna(0) == 0
    agg["low_quality"] = agg["n"].fillna(0) < 2
    agg["meter"] = meter
    agg.index.name = "ts_utc"
    return agg

p1 = build_1min(raw200, "200")
print(f"Serie 1 min: {len(p1):,} filas | {p1.index.min()} -> {p1.index.max()}")
display(p1.head())
display(p1[["P", "I", "V", "PF", "Q", "S", "F", "n"]].describe().round(3).T)"""),
    MD("""## 3. Calidad y validación física

Se verifican las identidades `S = √3·V·I`, `P_total = P_L1+P_L2+P_L3` y `PF = P/S`. Si no se cumplen, hay un problema de registro o de configuración, no una carga."""),
    CODE("""def quality_checks(raw, name):
    p = raw["active_power_total"]; s = raw["apparent_power_total"]
    pf = raw["power_factor"]; v = raw["voltage_vll_avg"]; i = raw["current_avg"]
    return pd.Series({
        "S_vs_sqrt3VI_med_abs": (s - np.sqrt(3) * v * i / 1000).abs().median(),
        "P_vs_sum_fases_med_abs": (p - (raw["active_power_l1"] + raw["active_power_l2"] + raw["active_power_l3"])).abs().median(),
        "PF_vs_P_over_S_corr": pf.corr(p / s),
        "PF_gt1_pct": 100 * (pf > 1.0001).mean(),
        "P_neg_pct": 100 * (p < 0).mean(),
    }, name=name)

checks = pd.concat([quality_checks(raw200, "200"), quality_checks(raw201, "201")], axis=1)
display(checks.round(4))"""),
    CODE("""cov = (p1.assign(dia=p1.index.tz_convert("America/Bogota").date)
         .groupby("dia")
         .agg(minutos=("P", "count"), n_medio=("n", "mean"), n_min=("n", "min"))
         .reset_index())
cov["cobertura_pct"] = 100 * cov["minutos"] / 1440

g = p1["gap"]
runs = (g != g.shift()).cumsum()
gap_df = (p1.assign(run=runs)
          .query("gap == True")
          .groupby("run")
          .agg(inicio=("P", lambda s: s.index.min()),
               fin=("P", lambda s: s.index.max()),
               minutos=("P", "size"))
          .sort_values("minutos", ascending=False))

print("Días con datos:", len(cov), "| Días con cobertura < 80%:", int((cov.cobertura_pct < 80).sum()))
print("Minutos faltantes:", int(p1["gap"].sum()), f"({100*p1['gap'].mean():.1f}% del total)")
display(cov.round(2).to_string(index=False))
display(gap_df.head(10).to_string())"""),
    MD("""## 4. Figuras de auditoría"""),
    CODE("""fig, ax = plt.subplots()
p1["P"].plot(ax=ax, lw=0.55, color="#2f6db3")
ax.set_title("Potencia activa — medidor 200 (1 min)")
ax.set_ylabel("kW"); ax.set_xlabel("")
fig.savefig(FIG / "01_serie_P.png", dpi=150, bbox_inches="tight")
plt.show()"""),
    CODE("""fig, ax = plt.subplots()
tmp = inv200.sort_values("inicio")
ax.plot(tmp["inicio"], tmp["dt_med_s"], "o-", color="#2f6db3")
ax.set_title("Cadencia mediana por archivo — medidor 200")
ax.set_ylabel("segundos entre muestras"); ax.set_xlabel("")
fig.savefig(FIG / "01_cadencia.png", dpi=150, bbox_inches="tight")
plt.show()"""),
    CODE("""fig, ax = plt.subplots(figsize=(12, 4))
ax.bar(range(len(cov)), cov["cobertura_pct"], color="#2e8b57")
ax.set_xticks(range(0, len(cov), 2))
ax.set_xticklabels([str(d)[5:] for d in cov["dia"]][::2], rotation=60, fontsize=8)
ax.set_ylabel("cobertura (%)"); ax.set_title("Cobertura diaria — medidor 200")
ax.axhline(80, color="#d9822b", ls="--", lw=1)
fig.savefig(FIG / "01_cobertura.png", dpi=150, bbox_inches="tight")
plt.show()"""),
    CODE("""loc = p1.index.tz_convert("America/Bogota")
weekend = pd.Series(loc.dayofweek >= 5, index=p1.index)
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
axes[0].hist(p1["P"].dropna(), bins=60, color="#2f6db3")
axes[0].set_title("Distribución de P (1 min)"); axes[0].set_xlabel("kW")
axes[1].boxplot([p1.loc[~weekend, "P"].dropna(), p1.loc[weekend, "P"].dropna()],
                tick_labels=["laboral", "fin de semana"], showfliers=False)
axes[1].set_title("P por tipo de día"); axes[1].set_ylabel("kW")
fig.savefig(FIG / "01_distribucion.png", dpi=150, bbox_inches="tight")
plt.show()"""),
    CODE("""dia = pd.Timestamp("2026-10-08", tz="America/Bogota")
sel = p1.loc[dia:dia + pd.Timedelta(hours=23, minutes=59)]
fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
axes[0].plot(sel.index.tz_convert("America/Bogota"), sel["P"], color="#2f6db3", lw=1)
axes[0].set_ylabel("kW"); axes[0].set_title("Ejemplo de día — 2026-10-08")
axes[1].plot(sel.index.tz_convert("America/Bogota"), sel["V"], color="#d9822b", lw=0.8)
axes[1].set_ylabel("V"); axes[1].set_xlabel("hora local")
fig.savefig(FIG / "01_dia_ejemplo.png", dpi=150, bbox_inches="tight")
plt.show()"""),
    MD("""## 5. Guardar resultados

La serie procesada es la base de `02_peak_model.ipynb`. Los días de 30 s tienen `n = 2`; los de 8–10 s, `n = 6–7`."""),
    CODE("""p1.to_csv(OUT / "medidor200_1min.csv")
inv200.to_csv(TAB / "01_inventario_200.csv", index=False)
cov.to_csv(TAB / "01_cobertura_200.csv", index=False)
gap_df.to_csv(TAB / "01_huecos_200.csv")
print("Guardado:", OUT / "medidor200_1min.csv")
print(p1["low_quality"].value_counts().to_string())"""),
]

# =========================================================================
# 02 — Modelo de riesgo de pico
# =========================================================================
cells_02 = [
    MD("""# 02 · Modelo de riesgo de pico

**Pregunta:** ¿cuál es la probabilidad de que la potencia supere 12 kW en los próximos 15 minutos?

**Descriptor:**

$$
\\hat{p}_t=\\sigma\\left(\\beta_0+\\sum_{j=1}^{7}\\beta_j z_{tj}\\right),
\\qquad
Y_t=\\mathbf{1}\\left\\{\\max_{1\\le h\\le 15}P_{t+h}>12\\right\\}
$$

con $z_{tj}$ las features estandarizadas: `P_max15`, `P_mean15`, `V`, `PF`, hora (seno/coseno) y fin de semana.

**Protocolo:** rolling-origin por bloques de días, calibración temporal y test final reservado.
"""),
    CODE("""import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from pathlib import Path
from IPython.display import display

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import (average_precision_score, brier_score_loss,
                             precision_score, recall_score,
                             precision_recall_curve)
from sklearn.calibration import calibration_curve
from sklearn.isotonic import IsotonicRegression

pd.set_option("display.width", 170)
plt.rcParams.update({"figure.figsize": (10, 4.5), "axes.grid": True, "grid.alpha": 0.3})

ROOT = Path(".").resolve()
DATA = ROOT / "data" / "processed" / "medidor200_1min.csv"
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
MODELS = ROOT / "models"
for p in (FIG, TAB, MODELS):
    p.mkdir(parents=True, exist_ok=True)
assert DATA.exists(), "Corré 01_data_audit.ipynb primero."

d = pd.read_csv(DATA, parse_dates=["ts_utc"], index_col="ts_utc")
d.index = pd.to_datetime(d.index, utc=True)
print(d.shape)"""),
    MD("""## 1. Target y features"""),
    CODE("""d["P_max15"] = d["P"].rolling(15, min_periods=8).max()
d["P_mean15"] = d["P"].rolling(15, min_periods=8).mean()
loc = d.index.tz_convert("America/Bogota")
d["hour"] = loc.hour
d["is_weekend"] = (loc.dayofweek >= 5).astype(int)
d["hour_sin"] = np.sin(2 * np.pi * d["hour"] / 24)
d["hour_cos"] = np.cos(2 * np.pi * d["hour"] / 24)

H, THR = 15, 12.0
future_max = d["P"].rolling(H, min_periods=H).max().shift(-H)
d["Y"] = (future_max > THR).astype(float)
d.loc[future_max.isna(), "Y"] = np.nan

features = ["P_max15", "P_mean15", "V", "PF", "hour_sin", "hour_cos", "is_weekend"]
data = d.dropna(subset=features + ["Y"]).copy()
print(f"Filas: {len(data):,} | positivos: {int(data.Y.sum()):,} | tasa base: {data.Y.mean():.4f}")
display(data.groupby(pd.cut(data["P"], [0, 6, 7, 8, 9, 10, 11, 12, 13, 14, 20]),
                     observed=True)["Y"].agg(["mean", "count"]).round(4))"""),
    MD("""## 2. Ecuación logística

Se ajusta con el conjunto de desarrollo (todos los días menos el último bloque). Los coeficientes son sobre features estandarizadas, así que son comparables entre sí."""),
    CODE("""days = np.array(sorted(set(data.index.tz_convert("America/Bogota").date)))
blocks = np.array_split(days, 6)
dev_days = set().union(*blocks[:5])
hold_days = set(blocks[5])
dev = data[np.isin(data.index.tz_convert("America/Bogota").date, list(dev_days))]
hold = data[np.isin(data.index.tz_convert("America/Bogota").date, list(hold_days))]

def make_logit():
    return Pipeline([("sc", StandardScaler()),
                     ("lr", LogisticRegression(C=1.0, max_iter=5000))])

def make_gam():
    pre = ColumnTransformer([
        ("spl", SplineTransformer(n_knots=6, degree=3, include_bias=False),
         ["P_max15", "P_mean15", "V", "PF", "hour_sin", "hour_cos"]),
        ("bin", "passthrough", ["is_weekend"]),
    ])
    return Pipeline([("pre", pre),
                     ("lr", LogisticRegression(C=1.0, max_iter=5000))])

def make_gbm():
    return HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05,
                                          max_iter=400, l2_regularization=1.0,
                                          min_samples_leaf=50, random_state=0)

logit = make_logit().fit(dev[features], dev["Y"])
coefs = pd.Series(logit.named_steps["lr"].coef_[0], index=features).sort_values(key=abs, ascending=False)
display(coefs.round(3).to_frame("coeficiente estandarizado"))
print("intercepto:", round(logit.named_steps["lr"].intercept_[0], 3))"""),
    MD("""## 3. Validación rolling-origin

Cinco folds por bloques de días. Se comparan cuatro modelos: logística (la ecuación), GAM con splines, gradient boosting y persistencia."""),
    CODE("""rows = []
for k in range(1, 6):
    tr_days = set().union(*blocks[:k])
    te_days = set(blocks[k])
    tr = data[np.isin(data.index.tz_convert("America/Bogota").date, list(tr_days))]
    te = data[np.isin(data.index.tz_convert("America/Bogota").date, list(te_days))]

    for name, model in [("logit", make_logit()), ("gam", make_gam()), ("gbm", make_gbm())]:
        model.fit(tr[features], tr["Y"])
        p = model.predict_proba(te[features])[:, 1]
        rows.append({"fold": k, "model": name,
                     "PR": average_precision_score(te["Y"], p),
                     "Brier": brier_score_loss(te["Y"], p),
                     "base": te["Y"].mean()})

    p_pers = te["P"].values / 20.0
    rows.append({"fold": k, "model": "persistencia",
                 "PR": average_precision_score(te["Y"], p_pers),
                 "Brier": brier_score_loss(te["Y"], np.clip(p_pers, 0, 1)),
                 "base": te["Y"].mean()})

res = pd.DataFrame(rows)
display(res.pivot(index="fold", columns="model", values=["PR", "Brier"]).round(3))
display(res.groupby("model")[["PR", "Brier"]].median().round(4))"""),
    MD("""## 4. Calibración y umbral de decisión

El umbral se elige por costo. Con `C_FP = 1` y `C_FN = 10`, el umbral óptimo es $\\tau^* = 1/(1+10) = 0.091$."""),
    CODE("""# Calibración por cross-fitting: no se sacrifican datos de entrenamiento
p_oof = np.full(len(dev), np.nan)
for k in range(1, 5):
    tr_days = set().union(*blocks[:k])
    va_days = set(blocks[k])
    tr = dev[np.isin(dev.index.tz_convert("America/Bogota").date, list(tr_days))]
    va = dev[np.isin(dev.index.tz_convert("America/Bogota").date, list(va_days))]
    m = make_logit().fit(tr[features], tr["Y"])
    p_oof[dev.index.get_indexer(va.index)] = m.predict_proba(va[features])[:, 1]

mask_oof = ~np.isnan(p_oof)
iso = IsotonicRegression(out_of_bounds="clip").fit(
    p_oof[mask_oof], dev["Y"].values[mask_oof])
final = make_logit().fit(dev[features], dev["Y"])
p_hold = iso.predict(final.predict_proba(hold[features])[:, 1])

table = []
for th in [0.05, 0.091, 0.2, 0.3, 0.5]:
    pred = (p_hold >= th).astype(int)
    table.append({"umbral": th,
                  "precision": precision_score(hold["Y"], pred, zero_division=0),
                  "recall": recall_score(hold["Y"], pred, zero_division=0),
                  "tasa_alerta": pred.mean()})
display(pd.DataFrame(table).round(3))

fig, axes = plt.subplots(1, 2, figsize=(12, 4))
prec, rec, _ = precision_recall_curve(hold["Y"], p_hold)
axes[0].plot(rec, prec, color="#2f6db3")
axes[0].axhline(hold["Y"].mean(), color="#888", ls="--", lw=1, label="tasa base")
axes[0].set_xlabel("recall"); axes[0].set_ylabel("precision")
axes[0].set_title("Curva precisión-recall — holdout"); axes[0].legend()
frac_pos, mean_pred = calibration_curve(hold["Y"], p_hold, n_bins=8, strategy="quantile")
axes[1].plot(mean_pred, frac_pos, "o-", color="#2e8b57")
axes[1].plot([0, 1], [0, 1], "k--", lw=1)
axes[1].set_xlabel("probabilidad estimada"); axes[1].set_ylabel("frecuencia observada")
axes[1].set_title("Calibración — holdout")
fig.savefig(FIG / "02_pr_calibracion.png", dpi=150, bbox_inches="tight")
plt.show()"""),
    MD("""## 5. Pruebas de generalización

Tres controles: brecha train/test, etiquetas barajadas y curva de aprendizaje."""),
    CODE("""p_tr = final.predict_proba(dev[features])[:, 1]
print("PR-AUC train: %.4f | holdout: %.4f | brecha: %.4f" % (
    average_precision_score(dev["Y"], p_tr),
    average_precision_score(hold["Y"], p_hold),
    average_precision_score(dev["Y"], p_tr) - average_precision_score(hold["Y"], p_hold)))
print("Brier train: %.4f | holdout: %.4f" % (
    brier_score_loss(dev["Y"], p_tr), brier_score_loss(hold["Y"], p_hold)))

np.random.seed(0)
shuffled = []
for _ in range(5):
    y_shuf = np.random.permutation(dev["Y"].values)
    m = make_logit().fit(dev[features], y_shuf)
    shuffled.append(average_precision_score(hold["Y"], m.predict_proba(hold[features])[:, 1]))
print("Etiquetas barajadas: media %.4f | rango [%.4f, %.4f]" % (
    np.mean(shuffled), np.min(shuffled), np.max(shuffled)))

curve = []
for n_days in [11, 16, 21, 26]:
    tr_days = set(sorted(dev_days)[:n_days])
    sub = data[np.isin(data.index.tz_convert("America/Bogota").date, list(tr_days))]
    m = make_logit().fit(sub[features], sub["Y"])
    p = m.predict_proba(hold[features])[:, 1]
    curve.append({"dias_train": n_days,
                  "PR_train": average_precision_score(sub["Y"], m.predict_proba(sub[features])[:, 1]),
                  "PR_holdout": average_precision_score(hold["Y"], p),
                  "Brier_holdout": brier_score_loss(hold["Y"], p)})
display(pd.DataFrame(curve).round(4))"""),
    MD("""## 6. Ejemplo de operación y guardado"""),
    CODE("""example_day = pd.Timestamp("2026-11-17", tz="America/Bogota")
sel = hold.loc[example_day:example_day + pd.Timedelta(hours=23, minutes=59)].copy()
sel["p_hold"] = iso.predict(final.predict_proba(sel[features])[:, 1])
sel = sel.loc[sel.index.tz_convert("America/Bogota").date == example_day.date()]

fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
axes[0].plot(sel.index.tz_convert("America/Bogota"), sel["P"], color="#2f6db3", lw=1)
axes[0].axhline(THR, color="#d9822b", ls="--", lw=1, label="umbral 12 kW")
axes[0].set_ylabel("kW"); axes[0].set_title("Potencia y probabilidad de pico — día de holdout")
axes[0].legend()
axes[1].plot(sel.index.tz_convert("America/Bogota"), sel["p_hold"], color="#6a4c93", lw=1)
axes[1].axhline(0.091, color="#d9822b", ls="--", lw=1, label="umbral de alerta 0.091")
axes[1].set_ylabel("probabilidad"); axes[1].set_xlabel("hora local"); axes[1].legend()
fig.savefig(FIG / "02_ejemplo_dia.png", dpi=150, bbox_inches="tight")
plt.show()

res.to_csv(TAB / "02_resultados_folds.csv", index=False)
coefs.to_frame("coeficiente").to_csv(TAB / "02_coeficientes.csv")
pd.DataFrame(table).to_csv(TAB / "02_umbrales.csv", index=False)
joblib.dump({"model": final, "calibrator": iso, "features": features},
            MODELS / "peak_logit.joblib")
print("Guardado en", TAB, "y", MODELS)"""),
    MD("""## 7. Conclusiones

- La ecuación logística de 7 features compite con el GBM y el GAM; no necesita un modelo opaco.
- El PR-AUC en holdout es ~20× la tasa base. En la mediana de los folds la logística supera la persistencia, pero en el bloque de holdout la persistencia fue competitiva; la variabilidad entre períodos es alta.
- Las pruebas de etiquetas barajadas y la curva de aprendizaje muestran que el modelo generaliza, no memoriza.
- El umbral de alerta se elige por costo, no por F1.
- Limitaciones: 47 días, cadencia mixta, picos de 10–30 s y una sola subestación. El modelo es un MVP, no una promesa de producción.
"""),
]

if __name__ == "__main__":
    build(cells_01, "01_data_audit.ipynb")
    build(cells_02, "02_peak_model.ipynb")
    print("Listo.")
