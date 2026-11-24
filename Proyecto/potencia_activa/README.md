# Pronóstico de potencia activa a 24 horas

**Proyecto:** predicción de la potencia activa del bloque universitario en una ventana grande: las próximas **24 horas**, con resolución **horaria**.

**Datos:** serie de 1 min del medidor 200 (red normal), agregada a 1 h. La serie está en `../data/processed/medidor200_1min.csv`.

**Formulación matemática completa:** [`FORMULACION_MATEMATICA.md`](FORMULACION_MATEMATICA.md).

---

## 1. Qué se hizo

1. **Serie horaria.** Se agrega la potencia de 1 min a 1 h en hora local. Una hora con menos de 30 min de datos queda como faltante; no se imputa.
2. **Perfil y autocorrelación.** Se revisa el perfil horario por tipo de día y la ACF hasta 72 h.
3. **Dataset multipaso.** Para cada origen $t_0$ y horizonte $h=1,\dots,24$ se arma una fila con features del origen, features del objetivo y estacionalidad conocida.
4. **Modelos.** Persistencia, seasonal naive, climatología por hora/tipo de día, Ridge, Ridge con hora one-hot, GBM y un híbrido.
5. **Validación.** Rolling-origin por bloques de días: 5 folds; el modelo nunca ve el futuro del bloque de test.
6. **Modelo final.** Híbrido con residuo GBM regularizado; se guarda con la climatología para pronosticar días nuevos.
7. **Funcionalidad.** `forecast_day(historia, bundle)` devuelve las próximas 24 h, energía diaria, pico y hora del pico.
8. **Generalización.** Brecha train/test, etiquetas barajadas, curva de aprendizaje y ablación de features.

---

## 2. Datos

| Dato | Valor |
|---|---:|
| Horas totales | 1.113 |
| Horas válidas | 609 |
| Días con datos | 47 |
| Filas del dataset | 10.227 |
| Orígenes | 573 |
| Días con filas de target | 30 |
| Minutos faltantes de la serie de 1 min | 45,3 % |

La cobertura es la limitación principal: solo 609 horas válidas y 30 días con targets completos.

### Protocolo experimental

**Ventana:** 24 h hacia adelante, resolución 1 h. Para cada origen $t_0$ se predicen $P_{t_0+1},\dots,P_{t_0+24}$.

**Orígenes:** cada hora válida de la serie. Las ventanas se **solapan**: un mismo target puede aparecer en hasta 24 orígenes. Cada origen aporta hasta 24 filas (una por horizonte); por los huecos, el promedio es menor. El ejemplo del 17-11 usa el origen a medianoche solo para visualizar; el modelo se entrena y evalúa con todos los orígenes.

**Particiones:** 6 bloques cronológicos de días de origen. En el fold $k$ se entrena con los bloques $1,\dots,k$ y se evalúa con el bloque $k+1$. Sin shuffle.

| Fold | Días train | Días test | Orígenes train | Orígenes test | Filas train | Filas test | % train | % test | Test |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 5 | 5 | 75 | 82 | 1.029 | 1.338 | 43,5 | 56,5 | 10-18 a 10-23 |
| 2 | 10 | 5 | 157 | 120 | 2.367 | 2.880 | 45,1 | 54,9 | 10-24 a 10-28 |
| 3 | 15 | 5 | 277 | 99 | 5.247 | 1.758 | 74,9 | 25,1 | 10-29 a 11-04 |
| 4 | 20 | 5 | 376 | 94 | 7.005 | 1.212 | 85,3 | 14,7 | 11-05 a 11-13 |
| 5 | 25 | 5 | 470 | 103 | 8.217 | 2.010 | 80,3 | 19,7 | 11-14 a 11-18 |

**Holdout final:** los últimos 5 días de origen: 8.217 filas de train (80,3 %) y 2.010 de test (19,7 %).

**No hay un 80/20 fijo.** Cada fold tiene su propio tamaño; el primero tiene más test que train porque el bloque inicial tiene poca cobertura. Esa es la consecuencia de rolling-origin con datos parciales. Los porcentajes son sobre las filas del fold (train + test), no sobre el dataset completo.

---

## 3. Resultados

Mediana de 5 folds:

| Modelo | MAE (kW) | RMSE (kW) | Skill vs naive |
|---|---:|---:|---:|
| **Híbrido (climatología + GBM residual)** | **0,274** | **0,454** | **0,634** |
| Climatología | 0,298 | 0,477 | 0,574 |
| GBM | 0,307 | 0,474 | 0,600 |
| Ridge + hora one-hot | 0,774 | 1,016 | 0,182 |
| Ridge | 0,800 | 1,045 | 0,074 |
| Seasonal naive | 0,834 | 1,541 | 0,000 |
| Persistencia | 1,370 | 1,918 | −0,370 |

**Lectura honesta:**

- El **híbrido** es el mejor: MAE 0,274, RMSE 0,454, skill 0,634. Mejora ~8 % a la climatología y ~11 % al GBM.
- La **climatología** sigue siendo el mejor modelo individual; el **GBM solo** no la supera de forma clara.
- El ML aporta valor como **corrección del residuo** del perfil típico, no aprendiendo el perfil desde cero.
- Los **modelos lineales** quedan atrás: la hora como variable numérica o con one-hot no captura el perfil con la regularización usada.
- El **último fold es difícil**: test MAE 0,643, train 0,150, brecha 0,493. El mediano 0,274 no es uniforme; se reporta el rango.

### Error por horizonte

| Horizonte | Climatología | Híbrido | GBM | Seasonal naive |
|---:|---:|---:|---:|---:|
| 1 h | 0,353 | **0,330** | 0,465 | 0,795 |
| 6 h | 0,372 | **0,346** | 0,462 | 0,797 |
| 12 h | 0,384 | **0,361** | 0,503 | 0,802 |
| 18 h | 0,390 | **0,372** | 0,550 | 0,801 |
| 24 h | 0,397 | **0,379** | 0,555 | 0,810 |

El error crece con el horizonte en todos los modelos; el híbrido gana en todos los horizontes.

### Error de energía diaria

Para los días con al menos 20 h y origen a medianoche (13 días):

| Modelo | Error absoluto mediano | MAPE mediano |
|---|---:|---:|
| **Híbrido** | **3,6 kWh/día** | **2,2 %** |
| Climatología | 4,5 kWh/día | 3,0 % |

La energía diaria real media de esos días es **150,1 kWh**. El **11-16** es la excepción: 131,3 kWh reales vs 172,7 pronosticados (41,4 kWh, 31,6 %). Ese lunes fue **festivo nacional** (Independencia de Cartagena, trasladada al lunes por la Ley Emiliani): el bloque consumió como un domingo y el pronóstico lo marca como **desviación**, no como fallo del modelo. El **11-17** cierra en 155,9 kWh reales vs 150,4 pronosticados (−5,5 kWh, 3,5 %).

---

## 4. Modelo final y funcionalidad

**Modelo final:** híbrido con residuo GBM regularizado:

$$
\hat Y^{\text{hyb}}_{t_0+h}
=
\hat Y^{\text{clim}}_{h,d}
+
\hat r_\theta(x_{t_0},h),
\qquad
r=y-\hat Y^{\text{clim}}.
$$

La climatología aporta el perfil; el GBM corrige el residuo con features: rezagos 1/24/168 h, medias móviles 3/6/24 h, día anterior, semana anterior, calendario y Fourier.

**Entrenamiento:** todos los días menos los últimos 5. **Test:** últimos 5 días.

| Métrica | Valor |
|---|---:|
| MAE train | 0,150 kW |
| MAE test | 0,643 kW |
| Brecha train/test | 0,493 kW |
| RMSE test | 1,339 kW |

El último fold es difícil (11-14 a 11-18: fin de semana, 11-16 festivo, 11-18 parcial). El RMSE alto está dominado por el 11-16; el 11-17 se pronostica bien. Sin el 11-16, el MAE del híbrido baja a 0,212 kW y su R² sube a 0,961.

### Función `forecast_day`

`forecast.py` implementa:

```python
from forecast import forecast_day, summary_forecast

bundle = joblib.load("models/pronostico_24h.joblib")
hist = h["P"].loc[:"2026-11-16 23:00"]       # historia hasta el origen
fc = forecast_day(hist, bundle)               # 24 filas: target, P_hat, P_clim, resid_hat
summary_forecast(fc)
# {'energia_kwh': 172.74, 'pico_kw': 10.15, 'hora_pico': '2026-11-17 11:00'}
```

Demo del **17-11** (modelo entrenado hasta el 13-11, sin ver el 14-18):

- Pronóstico 24 h: **172,7 kWh**, pico **10,15 kW** a las **11:00**.
- Real 17-11 (21 h): **161,4 kWh**, pico **10,89 kW**.
- Pronóstico en las mismas 21 h: **156,0 kWh**, MAE **0,317 kW**.

La función devuelve la curva, la energía diaria, el pico y la hora del pico. Es la funcionalidad que se le entrega al cliente, no el notebook.

---

## 5. ¿Memoriza?

Cuatro controles sobre el modelo final:

| Prueba | Resultado |
|---|---|
| Brecha train/test | **0,493 kW** |
| Etiquetas barajadas (5 rep.) | MAE **1,274** vs baseline **1,271** |
| Curva de aprendizaje | test **0,784 → 0,631 → 0,643**; train **0,020 → 0,150** |
| Ablación | completo 0,643; sin `prev_day` 0,638; sin `prev_day/prev_week` 0,652; sin lags 0,644; sin calendario 0,635 |

**Lectura:**

- **No aprende ruido:** con etiquetas barajadas el MAE cae a la media (1,274 vs 1,271). Si memorizara, el test no caería al azar.
- **Mejora con datos:** el test baja de 0,784 a 0,631 al pasar de 5 a 15 días; después se estabiliza. El train sube de 0,020 a 0,150 (menos sobreajuste al crecer el dataset).
- **La brecha es real:** 0,493 kW. El modelo ajusta mejor el train que el test. Pero el 87,5 % de esa brecha se explica por el 16-11 (festivo): sin ese día, la brecha baja a 0,062 kW y el MAE test a 0,212 kW. No es un memorizador puro, pero tampoco generaliza perfecto. Se reporta.
- **La ablación es mixta:** quitar `prev_day` o el calendario mejora levemente el último fold; quitar `prev_day/prev_week` empeora. En un fold difícil, el efecto de las features es chico. La evidencia fuerte de que aprende es el shuffle y la curva, no la ablación.

La conclusión honesta: **el modelo no memoriza el ruido, pero tiene una brecha train/test que hay que decir**. El último fold es difícil; el mediano de 0,274 es el rendimiento típico, no el peor caso.

---

## 6. Ejemplo

En `reports/figures/01_ejemplo_24h.png` se muestra el pronóstico para el **17-11**, origen 00:00:

- el **híbrido** sigue la forma del día y corrige la climatología;
- la **climatología** sigue la forma del día;
- el **GBM** solo subestima la carga alta;
- el **seasonal naive** y el **Ridge** quedan planos.

El **primer lunes completo (10-19)** no se predice bien: el entrenamiento previo no tenía un día laboral representativo. Eso no es un defecto del modelo; es cobertura.

---

## 7. Interpretación

- La estacionalidad diaria es el predictor dominante. El ML no la supera desde cero; la supera como corrección del residuo.
- El **híbrido** es el resultado principal: perfil + corrección. El GBM solo no le gana a la climatología.
- La cobertura manda: 609 horas válidas, 45 % de minutos faltantes y solo 30 días con targets completos.
- El proyecto es un **MVP metodológico**: pipeline reproducible, baselines honestos, validación temporal, funcionalidad concreta y límites.

**Para mejorar:**

1. Más días continuos (3–6 meses) para que la climatología y el GBM tengan regímenes representativos.
2. Features de clima, ocupación y calendario académico (feriados).
3. Pronóstico probabilístico con cuantiles (0,1/0,5/0,9) y pinball loss.
4. Comparación con SARIMA/ETS o STL.

---

## 8. Archivos

| Archivo | Qué es |
|---|---|
| `01_forecast_potencia.ipynb` | Notebook ejecutado con todo el pipeline, funcionalidad y generalización |
| `FORMULACION_MATEMATICA.md` | Formulación matemática completa, derivaciones y análisis |
| `build_notebook.py` | Genera y ejecuta el notebook |
| `forecast.py` | Función `forecast_day` y `summary_forecast` |
| `analysis/fold5_analysis.py` | R² por fold y descomposición del fold 5 |
| `data/processed/potencia_horaria.csv` | Serie horaria |
| `reports/tables/01_particiones.csv` | Particiones exactas |
| `reports/tables/01_metricas_folds.csv` | Métricas por fold |
| `reports/tables/01_resumen_modelos.csv` | Resumen de modelos |
| `reports/tables/01_mae_horizonte.csv` | MAE por horizonte |
| `reports/tables/01_generalizacion.csv` | Brecha y shuffle |
| `reports/tables/01_ablacion.csv` | Ablación de features |
| `reports/tables/01_learning_curve.csv` | Curva de aprendizaje |
| `reports/tables/01_importancia.csv` | Importancia del residuo |
| `reports/tables/01_r2_folds.csv` | R² por fold |
| `reports/tables/01_fold5_por_dia.csv` | MAE por día objetivo en el fold 5 |
| `reports/tables/01_fold5_sin_feriado.csv` | Fold 5 con y sin el 16-11 |
| `reports/figures/01_*.png` | Serie, perfil, ACF, error, ejemplo, curva e importancia |
| `models/pronostico_24h.joblib` | Bundle: features, climatología, fallback y GBM del residuo |

## 9. Cómo correr

```powershell
cd repo\Proyecto\potencia_activa
python build_notebook.py
python forecast.py
python analysis\generalization_checks.py
python analysis\fold5_analysis.py
python analysis\daily_energy_error.py
```

O abrir `01_forecast_potencia.ipynb` en Jupyter. El notebook ya está ejecutado con salidas.
