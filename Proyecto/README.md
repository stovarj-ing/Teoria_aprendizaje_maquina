# PeakGuard — Modelo de riesgo de pico

Proyecto final de **Teoría del Aprendizaje de Máquina**  
Universidad Nacional de Colombia — Sede Manizales  
Autor: Sebastián Tovar  
Datos: subestación del bloque universitario, medidores 200 (red normal) y 201 (red regulada)

---

## Qué hay aquí

| Archivo | Qué es |
|---|---|
| `01_data_audit.ipynb` | Lee los ZIP, construye la serie de 1 min, audita huecos/cadencia y valida la física |
| `02_peak_model.ipynb` | Define el target, ajusta la ecuación, valida con rolling-origin, calibra y prueba generalización |
| `03_evaluation.ipynb` | Evaluación operativa retrospectiva: episodios de pico, alertas, lead time, costo y análisis de errores |
| `data/processed/medidor200_1min.csv` | Serie de 1 min del medidor 200 (salida de 01) |
| `reports/figures/` | Figuras de los tres notebooks |
| `reports/tables/` | Inventario, cobertura, huecos, resultados, coeficientes, umbrales, eventos y costos |
| `models/peak_logit.joblib` | Modelo final + calibrador + lista de features |
| `build_notebooks.py` | Genera y ejecuta los notebooks 01 y 02 |
| `build_evaluation.py` | Genera y ejecuta el notebook 03 |

**Datos crudos:** los ZIP del analizador no se publican en este repositorio. Los notebooks se entregan ejecutados y los datos procesados y resultados sí están incluidos. Para regenerar `01_data_audit.ipynb`, coloca `analizador 200.zip` y `analizador 201.zip` en la raíz de esta carpeta.

**Proyecto de pronóstico de potencia activa (24 h):** [`potencia_activa/`](potencia_activa/).

Los notebooks ya están **ejecutados con salidas**. Si quieres regenerarlas:

```powershell
python -m pip install -r requirements.txt
python build_notebooks.py
```

O abrirlas con Jupyter y correr `01` y después `02`.

---

## La pregunta

> ¿Cuál es la probabilidad de que la potencia activa del bloque supere **12 kW** en los próximos **15 minutos**?

No es una predicción determinística del instante del pico. Es una **probabilidad condicional**:

$$
\hat{p}_t=\mathbb{P}\left(\max_{1\le h\le 15}P_{t+h}>12\;\middle|\;\mathcal{F}_t\right),
$$

donde $\mathcal{F}_t$ es toda la información disponible hasta $t$.

---

## El descriptor matemático

Target:

$$
Y_t=\mathbf{1}\left\{\max_{1\le h\le 15}P_{t+h}>12\right\}.
$$

Features (7, estandarizadas con media y desvío del entrenamiento):

$$
x_t=\left[P_{\max,15},\;P_{\mean,15},\;V,\;\mathrm{PF},\;\sin\frac{2\pi h}{24},\;\cos\frac{2\pi h}{24},\;\text{weekend}\right].
$$

Ecuación ajustada:

$$
\boxed{
\begin{aligned}
\operatorname{logit}\hat{p}_t
={}&-9.015
+1.236\,z_{P\max15}
-1.021\,\text{weekend}
-0.850\,z_{\cos}\\
&+0.604\,z_{\sin}
+0.604\,z_{P\mean15}
-0.556\,z_V
+0.538\,z_{PF}.
\end{aligned}
}
$$

Es una **regresión logística de 7 variables y 8 parámetros**, no una tabla de búsqueda. Se calcula con una suma y una sigmoide.

Lectura de los signos:

- **P_max15 y P_mean15 positivos:** si la carga reciente ya es alta, el riesgo sube.
- **PF positivo:** los picos son más resistivos.
- **V negativo:** a mayor tensión, menor riesgo; los picos coinciden con una caída.
- **weekend negativo:** menos picos el fin de semana.
- **seno/coseno:** capturan el patrón diario de ocupación.

El intercepto es muy negativo porque la tasa base es 2,7 %; por eso el modelo se **calibra fuera de muestra** antes de elegir el umbral.

---

## Protocolo de validación

1. **Serie de 1 min** como media de las muestras de alta resolución, no como muestra decimada.
2. **Target** con horizonte de 15 min y umbral de 12 kW.
3. **Rolling-origin** por bloques de días: 5 folds, siempre entrenando con el pasado.
4. **Test final reservado:** el último bloque no se usa para elegir features ni hiperparámetros.
5. **Calibración por cross-fitting:** predicciones out-of-fold + isotónica; el modelo final usa todos los días de desarrollo.
6. **Controles:** brecha train/test, etiquetas barajadas y curva de aprendizaje.

---

## Resultados

### Comparación de modelos (mediana de 5 folds)

| Modelo | PR-AUC | Brier |
|---|---:|---:|
| Tasa base | 0,027 | 0,026 |
| Persistencia | 0,367 | 0,102 |
| Gradient boosting | 0,428 | 0,017 |
| **Logística (ecuación)** | **0,458** | **0,014** |
| **GAM con splines** | **0,491** | **0,016** |

La ecuación logística **compite con el GBM** y el GAM la supera levemente. No hace falta un modelo opaco: la estructura está en las features.

### Holdout (último bloque, calibrado)

- PR-AUC: **0,380**
- Brier: **0,016**
- Tasa base: 0,020
- Persistencia en ese bloque: 0,511

La persistencia es un baseline fuerte y en ese bloque ganó. En la mediana de los folds, la logística la supera (0,458 vs 0,367). La variabilidad entre períodos es alta y se reporta.

### Umbrales de operación (holdout calibrado)

| Umbral | Precisión | Recall | Tasa de alerta |
|---:|---:|---:|---:|
| 0,05 | 0,117 | 1,000 | 17,0 % |
| 0,091 | 0,135 | 1,000 | 14,7 % |
| 0,20 | 0,216 | 0,966 | 8,9 % |
| **0,30** | **0,468** | **0,314** | **1,3 %** |
| 0,50 | 0 | 0 | 0 % |

El umbral 0,091 corresponde a $C_{FP}=1$, $C_{FN}=10$; es un punto de muy alto recall y baja precisión. El punto 0,30 es más equilibrado: 47 % de precisión con 31 % de recall. La elección depende del costo real de una falsa alarma vs un pico no advertido.

### Controles de generalización

| Prueba | Resultado |
|---|---|
| PR-AUC train vs holdout | 0,474 vs 0,380 (brecha 0,095) |
| Brier train vs holdout | 0,020 vs 0,016 |
| Etiquetas barajadas | PR-AUC 0,021 (rango 0,010–0,060), ≈ tasa base |
| Curva de aprendizaje | 11 días: 0,221 → 26 días: 0,400 |
| Train en la curva | 0,598 (11 días) → 0,475 (26 días) |

El train **baja** y el test **sube** al agregar datos: el modelo deja de ajustar ruido y captura estructura. Con etiquetas barajadas el rendimiento cae a la tasa base: no está memorizando.

---

## Evaluación operativa retrospectiva (03)

El notebook `03_evaluation.ipynb` reemplaza el piloto que no se puede hacer: simula el modelo desplegado sobre predicciones **out-of-fold** y evalúa el sistema a nivel de **episodio de pico**, no de minuto. El umbral se barre sobre el score crudo OOF; la calibración de probabilidades está en el notebook 02.

**Procedimientos matemáticos:**

- **Episodio de pico:** corrida maximal de $P_t>12$, cerrando huecos internos de hasta 5 min.
- **Episodio de alerta:** corrida maximal de $\hat p_t\ge\tau$, con cooldown de 15 min.
- **Detección:** el pico $j$ se detecta si hay una alerta activa en $[s_j-15,s_j)$.
- **Lead time:** $s_j-\max(a_i,s_j-15)$; se reporta el valor de la ventana.
- **Recall / precisión:** $R=TP_{\text{picos}}/N_P$; $P=TP_{\text{alertas}}/N_A$.
- **Costo:** $C(\tau)=C_{FP}FP+C_{FN}(N_P-TP)+\frac{C_{FP}}{60}A$, donde $A$ son minutos en alerta.

En los bloques OOF hay **58 episodios de pico**. A igual carga de alertas:

| Carga de alerta | Modelo recall | Modelo precisión | Modelo FA/día | Persistencia recall | Persistencia precisión | Persistencia FA/día |
|---:|---:|---:|---:|---:|---:|---:|
| 2 % | 0,397 | 0,375 | 1,15 | 0,638 | 0,210 | 4,92 |
| 5 % | 0,638 | 0,273 | 2,15 | 0,879 | 0,152 | 9,04 |
| 10 % | 0,845 | 0,281 | 2,46 | 0,948 | 0,119 | 10,54 |
| 20 % | 1,000 | 0,228 | 2,35 | 1,000 | 0,102 | 8,81 |

El punto de costo elegido con $C_{FN}/C_{FP}=10$ es un umbral de **0,0019** (score crudo), con **recall 1,0**, **precisión 0,26**, **2,08 falsas alarmas/día**, **19 % de carga de alerta** y lead mediano de **15 min** (ventana). Es un punto de muy alto recall y alta carga; a 5 % de carga, el modelo detecta 63,8 % con 27,3 % de precisión y 2,15 FA/día. La persistencia detecta más picos a igual carga, pero con muchas más falsas alarmas y menor precisión.

**Resultado honesto:** el modelo no es un oráculo. A bajo costo de falsa alarma y alto costo de pico perdido, conviene alertar mucho; a la inversa, conviene un umbral alto. La tabla de operación y la curva de costo son el entregable, no un número único.

---

## ¿Filtrar la señal ayuda?

Se probaron cuatro sets de features: **crudo**, **media móvil 15** (MA15), **EMA 15** y **Savitzky-Golay 15 causal** (centrado y desplazado 7 muestras). Dos targets: media de los próximos 15 min y pico >12 kW. Validación rolling-origin, mediana de 5 folds.

| Features | MAE media | Skill media | PR-AUC pico | Brier pico |
|---|---:|---:|---:|---:|
| Crudo | 0,197 | 0,624 | **0,446** | 0,0141 |
| EMA15 | **0,196** | **0,628** | 0,443 | **0,0139** |
| MA15 | 0,203 | 0,617 | 0,426 | 0,0142 |
| SG15 | 0,208 | 0,596 | 0,422 | 0,0141 |

**Lectura:**

- Para la **media** de la próxima ventana, el filtro ayuda apenas: EMA15 mejora el MAE un 0,9 % y el skill 0,004. MA15 y SG15 empeoran. La señal ya es suave a 15 min; el filtro no agrega mucho.
- Para el **pico**, el crudo es el mejor o está empatado. El pico es un evento de alta frecuencia; el filtro lo atenúa y borra la información que lo distingue.
- **No filtres el target.** Un target suavizado puede dar MAE artificialmente bajo (0,11 contra el target suavizado) porque el filtro causal usa muestras pasadas dentro del target; contra el target crudo el resultado ya no es comparable.
- **Cuidado con el filtro centrado:** usa $P_{t+m}$; si se aplica antes de partir train/test, hay fuga de futuro. La versión causal se obtiene desplazando la salida media ventana.

**Conclusión:** si el objetivo es la media, prueba EMA15 como feature; si el objetivo es el pico, quédate con el crudo y con `P_max15`. La confiabilidad no viene del filtro: viene de la cobertura, la validación temporal y la calibración.

El experimento está en `analysis/filter_experiment.py`; los resultados en `analysis/filter_experiment_reg.csv`, `filter_experiment_clf.csv` y `filter_experiment_trap.csv`.

---

## ¿Alcanza con predecir la media?

Se ajustó Ridge para la **media de los próximos 15 min** y se evaluó en el holdout:

| Métrica | Valor |
|---|---:|
| MAE | 0,171 kW |
| RMSE | 0,245 kW |
| Skill vs persistencia | 0,568 |

El pronóstico es bueno para el perfil. Pero en las **118 filas con pico real** ($\max P_{t+1..t+15}>12$):

- predicción media: **10,48 kW**;
- máximo real medio: **12,52 kW**;
- ninguna predicción supera 12 kW.

Si se alerta con “media pronosticada ≥ 12”, se detectan **0 picos**. Con “≥ 10” se detecta el 78 % con 44 % de precisión y 3,5 % de alerta. El pronóstico de la media **no es un detector de picos**: predice el valor esperado, no la cola.

**Consecuencia:** para un proyecto de series de tiempo, predecir la potencia activa es válido y suficiente. Para predecir picos hay que cambiar el target o el loss: máximo de la ventana, regresión cuantílica, o clasificación directa de $P(\max>\tau)$.

El análisis está en `analysis/mean_vs_peak.py`; la salida en `analysis/mean_vs_peak_out.txt`.

---

## Qué muestran los datos

- **200** (red normal): 154.626 filas, 10-06 a 11-21, cadencia 10 s / 30 s / 8–9 s. PF válido (solo 2 muestras > 1).
- **201** (red regulada): 167.044 filas, 10-06 a 11-22. **PF roto**: > 1 en 70,8 % de las muestras. P, Q, S e I son usables; el PF no.
- **Serie de 1 min del 200:** 66.767 minutos, **45,3 % faltantes**, 47 días con datos y **26 días con cobertura < 80 %**.
- **Muestra de modelado:** 35.375 minutos con features y target completos; 948 positivos (2,68 %).
- **NILM 200:** vacío (solo encabezado). **NILM 201:** 4,76 h a 0,5 s + 6,6 min; caso de estudio, no alcanza para entrenar.
- **Armónicos:** no hay THD ni armónicos individuales; solo $D=\sqrt{S^2-P^2-Q^2}$ como proxy.

La cobertura es la limitación principal. El modelo no vio 47 días completos: vio 35.375 minutos útiles. Por eso el proyecto es un **MVP**, no una promesa de producción.

---

## Estructura del proyecto

```text
Proyecto/
  01_data_audit.ipynb
  02_peak_model.ipynb
  03_evaluation.ipynb
  build_notebooks.py
  build_evaluation.py
  requirements.txt
  data/
    processed/medidor200_1min.csv
  models/
    peak_logit.joblib
  reports/
    figures/01_*.png, 02_*.png
    tables/01_*.csv, 02_*.csv
  analysis/               # experimentos exploratorios
  docs/                   # diagramas y documento del proyecto
  PEAKGUARD.md            # descripción completa del producto/proyecto
```

---

## Limitaciones y siguientes pasos

1. **Cobertura:** 45,3 % de minutos faltantes; 26 días con menos de 80 %. El piloto debe garantizar 3–6 meses continuos.
2. **Cadencia mixta:** 10 s, 30 s y 8–9 s. Los días de 30 s tienen medias de 1 min con 2 muestras; los de 8–10 s, con 6–7.
3. **Un solo medidor confiable:** el 201 no se usa por el PF roto. Para comparar redes hay que corregir su configuración.
4. **Sin armónicos:** el análisis de cargas capacitivas/reactivas queda limitado a P, Q, S y $D$.
5. **Picos de 10–30 s:** el target de 15 min es una ventana de riesgo, no un evento puntual. Para predecir el instante hace falta 0,5–1 s y otra formulación.
6. **Generalización:** con 35 mil minutos y 948 positivos, el modelo es un MVP. La transferencia a otro edificio requiere recalibración y validación.

Siguiente paso natural: **piloto de 3–6 meses** con datos continuos, tarifa real y etiquetas de eventos; después, comparar con la red regulada y evaluar un planificador de cargas.
