# PeakGuard

**Sistema de alerta temprana y explicación de picos de demanda para edificios**

Proyecto final — Teoría del Aprendizaje de Máquina  
Universidad Nacional de Colombia — Sede Manizales  
Departamento de Ingeniería Eléctrica, Electrónica y Computación  
Autor: Sebastián Tovar  
Fecha: 23 de noviembre de 2026  
Versión: 1.0

---

## 1. Resumen ejecutivo

PeakGuard es un servicio de monitoreo y analítica que **predice el riesgo de picos de demanda** en un edificio, **explica qué carga los está causando** y entrega un **reporte semanal** de energía, factor de potencia y desperdicio.

El motor es un modelo de clasificación probabilística calibrado, alimentado por las mediciones de un medidor PM5300 conectado a una red Wi-Fi HaLow. El producto se ofrece como suscripción por medidor o como servicio de auditoría + monitoreo, con un piloto inicial en el bloque universitario.

El proyecto final construye el MVP: preparación de datos, modelo de riesgo de pico, modelo de estados de carga, dashboard de replay, backtest y caso de negocio. No incluye despliegue productivo ni control automático de cargas.

**One-liner:** “Te avisamos antes del pico, te decimos qué lo causó y te ayudamos a bajar la factura.”

---

## 2. Problema y oportunidad

### 2.1 El dolor

Los edificios comerciales e institucionales pagan **cargo por demanda**: la factura mensual se calcula, en parte, sobre la potencia máxima registrada. Un pico de 20 segundos puede fijar ese máximo durante todo el mes. Además, si el factor de potencia (PF) es bajo, la tarifa puede incluir un cobro por energía reactiva. Y muchos edificios no tienen un BMS ni personal dedicado a mirar la curva de carga.

El resultado: picos evitables, reactiva cobrada, equipos encendidos fuera de horario y decisiones a ciegas.

### 2.2 La evidencia en los datos

El bloque universitario monitoreado muestra exactamente esos patrones:

| Hallazgo | Dato |
|---|---|
| Carga base nocturna | 5,36 kW ≈ 128,7 kWh/día |
| Energía día laboral | 169,8 kWh/día |
| Energía fin de semana | 131,0 kWh/día |
| Carga de ocupación | ~41 kWh/día (24 % del día laboral) |
| Pico máximo observado | 18,24 kW (26-10, 15:48) |
| PF mediano (medidor 200) | 0,513 |
| Reactiva mediana | 9,61 kVAR |
| Eventos >2 kW sobre la base | 7,6/h laboral vs 1,0/h fin de semana |
| Contribución de picos a la energía | 2,15 % laboral vs 0,48 % fin de semana |
| Huecos de adquisición | 8,36 h (10-22), 4,89 h (11-04), 4,24 h (10-20) |

Los picos son reales y trifásicos: suben P, I y PF, y baja levemente la tensión. El balance de energía cierra al 0,04 % contra el contador del medidor. No son ruido.

### 2.3 La oportunidad

- **Ahorro por demanda:** cada kW de pico evitado vale el cargo por demanda del mes.
- **Ahorro por reactiva:** con PF 0,51, la compensación a 0,95 requiere ~7,9 kVAR y reduciría la corriente de ~30,6 A a ~15,5 A.
- **Ahorro por horario:** la carga base de fin de semana (131 kWh/día) es casi toda consumo no productivo.
- **Visibilidad:** el edificio no tiene un sistema que explique qué está pasando.

El mercado objetivo son edificios sin BMS: universidades, centros comerciales, hoteles, clínicas, industria pequeña. La red HaLow permite llegar donde el Wi-Fi industrial no llega.

---

## 3. Solución

### 3.1 Qué es PeakGuard

Un servicio compuesto por:

1. **Medición:** medidor PM5300 + gateway HaLow + almacenamiento de series de tiempo.
2. **Inteligencia:** modelo de riesgo de pico + modelo de estados de carga + reglas de calidad de datos.
3. **Entrega:** dashboard, alertas y reporte semanal.

### 3.2 Módulos

**Módulo A — Alerta de pico.**  
Predice la probabilidad de superar un umbral de demanda en los próximos 15/60 min. Genera una alerta con hora, probabilidad, margen y causa probable.

**Módulo B — Explicación de carga.**  
Descompone la potencia agregada en estados interpretables: base reactiva, ocupación y eventos cortos. Permite responder “¿qué está causando este pico?”.

**Módulo C — Reporte semanal.**  
Energía por día, base vs ocupación, PF, reactiva, eventos, huecos y recomendaciones. Es el entregable que el cliente ve cada semana.

**Módulo D — Auditoría de factor de potencia (opcional).**  
Cuantifica el costo de la reactiva y dimensiona la compensación. Es el “primer win” comercial: un ahorro inmediato que abre la puerta al monitoreo.

### 3.3 Historias de usuario

- Como administrador, quiero recibir una alerta antes de que la demanda supere el umbral para poder desplazar una carga.
- Como administrador, quiero saber si el pico es un evento corto o una carga sostenida para no tomar una acción innecesaria.
- Como gerente, quiero un reporte semanal que me diga cuánta energía se consumió, cuánta fue base y cuánta se pudo evitar.
- Como técnico, quiero detectar medidores mal configurados (por ejemplo, PF > 1) antes de tomar decisiones.

---

## 4. Alcance

### 4.1 Alcance del curso (MVP)

Incluye:

- Preparación y auditoría de los datos existentes (24 días, medidores 200 y 201).
- Construcción de la serie de 1 min como media de las muestras de 10 s.
- Modelo de riesgo de pico con calibración y validación temporal.
- Modelo de estados de carga con interpretación física.
- Dashboard de replay con cuatro vistas.
- Backtest con métricas y curvas.
- Caso de negocio y presentación.

No incluye:

- Despliegue productivo 24/7.
- Control automático de cargas.
- Hardware nuevo.
- Multi-edificio.
- Certificación legal o tarifaria.

### 4.2 Alcance del piloto

- 1 edificio, 1 medidor principal (200) y, si aporta, el 201.
- 3–6 meses de datos continuos.
- Alertas por Telegram/email.
- Reporte semanal.
- Línea base y medición de ahorro (IPMVP simplificado).
- 1 caso de estudio.

### 4.3 Fuera de alcance

- Facturación o liquidación de energía.
- Integración con el sistema de facturación del operador de red.
- Control de clima/HVAC.
- Garantía de ahorro sin medición y verificación.

### 4.4 Supuestos y restricciones

- El medidor 200 corresponde a la red normal (208 V) y el 201 a la regulada (220 V). Confirmar.
- El medidor 200 es la fuente confiable de P, Q, V, I y PF. El PF del 201 no es válido (>1 en el 99,94 % de las muestras).
- La tarifa y la factura del bloque están disponibles para el caso de negocio.
- El edificio permite un piloto y el acceso a los datos.
- El proyecto se ejecuta en Python (pandas, scikit-learn, Streamlit).

---

## 5. Datos

### 5.1 Fuentes

- `Resumen_*.csv`: 1 muestra por minuto, 46 columnas, medidores 200 y 201.
- `Analizador-200_*.csv`: 10 s o 30 s, 24 columnas.
- `Analizador-201_*.csv`: 10 s o 30 s, 24 columnas.
- `*.xlsx`: duplicados de los CSV; no se usan.

### 5.2 Variables

**Potencia:** `active_power_total`, `active_power_l1/l2/l3`, `apparent_power_total`, `reactive_power_total`.  
**Corriente:** `current_avg`, `current_l1/l2/l3`.  
**Tensión:** `voltage_vll_avg`, `voltage_vln_avg`, `voltage_vab/vbc/vca`, `voltage_van/vbn/vcn`.  
**Calidad:** `frequency`, `power_factor`.  
**Energía:** `energy_import`, `energy_export`.

### 5.3 Calidad y preparación

1. Parsear `ts_utc` y `ts_local` a UTC; verificar que `ts_local = ts_utc − 5 h`.
2. Deduplicar timestamps (5 duplicados detectados).
3. Construir la serie de 1 min como **media** de las muestras de 10 s, no con el `Resumen` (que es una muestra por minuto y aliasa los picos).
4. Marcar huecos y no interpolar para el modelo; usar máscaras.
5. Verificar consistencia física: `S = √3·V·I`, `P_total = ΣP_fases`, `PF = P/S`, `E` monótona.
6. Definir el subconjunto limpio: días de 10 s para eventos; días completos para perfiles diarios.
7. Documentar los 10 días faltantes y los huecos internos.

### 5.4 Features

- **Temporales:** hora, minuto, día de la semana, fin de semana, feriado.
- **Rezagos:** P, Q, I, V en t−1, t−5, t−15, t−60 min.
- **Ventanas:** media, mediana, máximo, mínimo, desvío y pendiente en 5/15/60 min.
- **Eléctricas:** PF, Q, tensión, corriente, desbalance de fases.
- **Eventos:** cantidad y energía de eventos en la última hora; tiempo desde el último evento.
- **Energía:** ΔE diario, energía base, energía de ocupación.

### 5.5 Targets

- **Riesgo de pico:** `y = 1` si `max(P[t+1:t+H]) > umbral`, con H = 15 o 60 min y umbral definido con el cliente (ej. 12 kW).
- **Energía diaria:** kWh del día (regresión).
- **Estado de carga:** etiqueta latente (base, ocupación, evento) para el HMM/clustering.
- **Tipo de día:** laboral, fin de semana, parcial/outlier (clasificación).

### 5.6 Partición temporal

- **Rolling-origin:** entrenar con los primeros N días, validar el siguiente, avanzar.
- Nunca split aleatorio.
- Reportar métricas por día y por tipo de día.
- Mantener un conjunto de test final no visto.

---

## 6. Modelo

### 6.1 Arquitectura

```
Datos 10 s/1 min
      │
      ├── Features de ventana ──► Clasificador de riesgo de pico (GBM calibrado)
      │                                   │
      │                                   ├── probabilidad
      │                                   └── umbral por costo
      │
      ├── P, Q, I, V ──────────► Modelo de estados (HMM / clustering)
      │                                   │
      │                                   └── explicación del pico
      │
      └── Energía / calendario ─► Reporte semanal (regresión / STL)
```

### 6.2 Modelo de riesgo de pico

- **Baseline:** regresión logística con features simples; persistencia (“¿superó el umbral en la última hora?”).
- **Modelo principal:** gradient boosting (XGBoost/LightGBM/HistGradientBoosting) con calibración isotónica.
- **Métricas:** PR-AUC, Brier score, curva de calibración, recall a precisión fija, lead time.
- **Umbral:** elegido por costo (costo de falsa alarma vs costo de pico no advertido).
- **Interpretabilidad:** SHAP o permutation importance para explicar la alerta.

### 6.3 Modelo de estados de carga

- **Enfoque:** Gaussian HMM sobre P y Q (y opcionalmente I, V) con 3–5 estados.
- **Alternativa:** K-means sobre features de ventana + perfilado.
- **Estados esperados:** base, ocupación, evento corto, carga alta.
- **Validación:** log-likelihood en días held-out, estabilidad entre días, coincidencia con el catálogo de eventos, interpretación física.
- **Uso:** la probabilidad de estado es una feature del clasificador de pico y la explicación que ve el usuario.

### 6.4 Comparación con redes (opcional)

- **MLP** sobre features o ventanas.
- **1D-CNN** sobre ventanas de 60–360 muestras (la última hora) para predecir el próximo intervalo o el riesgo.
- **2D-CNN** sobre el heatmap día×hora para clasificar el tipo de día.
- **Conclusión esperada:** con 24 días, los modelos clásicos probablemente ganan; la comparación es el aprendizaje, no el resultado.

### 6.5 Métricas y validación

| Tarea | Métricas |
|---|---|
| Clasificación de pico | PR-AUC, Brier, calibración, recall@precision, lead time |
| Regresión de energía | MAE, RMSE, MAPE, R² |
| Clustering | silueta, estabilidad por submuestreo, validación externa |
| HMM | log-likelihood held-out, estabilidad de estados |
| Pronóstico | MAE/RMSE por horizonte, pinball loss, Diebold-Mariano |

### 6.6 Mapeo a los temas del curso

| Tema | Uso en PeakGuard |
|---|---|
| Reducción de dimensión | PCA/UMAP sobre perfiles diarios y features; visualización de estados |
| Conglomerados | K-means/DBSCAN/HMM para estados de carga |
| scikit-learn | Clasificador de riesgo, regresión de energía, calibración |
| Redes neuronales | MLP de comparación (opcional) |
| Redes convolucionales | 1D-CNN sobre ventanas (opcional) |
| Series de tiempo | Features, validación rolling-origin, SARIMA baseline |

La formulación matemática completa, con la notación, las ecuaciones y el protocolo de validación, está en la **sección 16**.

---

## 7. Arquitectura del sistema

### 7.1 Flujo de datos

```
PM5300 → Modbus/RS485 → Gateway HaLow → Broker/Ingesta → Base de series de tiempo
                                                              │
                                                              ├── Feature store (1 min)
                                                              ├── Modelo (batch/online)
                                                              └── Dashboard + alertas
```

### 7.2 Stack

- **Adquisición:** PM5300, gateway HaLow, Modbus.
- **Almacenamiento:** SQLite/Parquet para el MVP; InfluxDB/TimescaleDB para el piloto.
- **Procesamiento:** Python, pandas, numpy.
- **Modelos:** scikit-learn, statsmodels, hmmlearn (opcional).
- **Dashboard:** Streamlit + Plotly.
- **Alertas:** Telegram Bot API o SMTP.
- **Reproducibilidad:** `requirements.txt`, notebooks, scripts.

### 7.3 Despliegue

- **MVP:** local, replay de datos históricos.
- **Piloto:** servidor pequeño (VPS o Raspberry Pi) con ingesta y dashboard.
- **Producción:** contenedores, base de datos gestionada, monitoreo.

---

## 8. Dashboard y experiencia

### 8.1 Pantallas

**1. Replay del día.**  
P, Q, V, PF en el tiempo; marcador de riesgo; alerta si corresponde; sombreado de eventos.

**2. Estados de carga.**  
Timeline de estados (base/ocupación/evento); contribución de cada estado a la potencia; explicación del último pico.

**3. Reporte semanal.**  
Energía por día, base vs ocupación, PF, reactiva, eventos, huecos; recomendaciones.

**4. Backtest.**  
Curva PR, calibración, matriz de confusión, errores por día; comparación con baseline.

### 8.2 Lógica de alertas

- Si `prob > 0,7` y `P_actual > 0,8 × umbral` → alerta alta.
- Si `prob > 0,5` → alerta media.
- Cooldown de 15 min para no spamear.
- Mensaje: hora, probabilidad, causa probable, acción sugerida.

### 8.3 Explicabilidad

- SHAP/permutation importance para las features que dispararon la alerta.
- Estado de carga dominante.
- Comparación con el mismo día/hora de la semana anterior.

---

## 9. Validación y criterios de aceptación

**Técnicos:**

- PR-AUC del modelo > baseline + 0,10.
- Brier score < 0,10.
- Error de calibración < 0,05.
- Lead time mediano ≥ 5 min.
- Falsas alarmas ≤ 1/día.
- Estabilidad de estados > 0,7 (ARI entre submuestras).

**De producto:**

- El dashboard carga un día en < 5 s.
- La alerta se entiende sin leer el notebook.
- El reporte semanal se genera automáticamente.

**De negocio:**

- 1 piloto acordado.
- 3 clientes potenciales identificados.
- 1 caso de estudio con ahorro estimado.

---

## 10. Caso de negocio

### 10.1 Cliente

Administradores de edificios con cargo por demanda y sin BMS: universidades, centros comerciales, hoteles, clínicas, industria pequeña. El decisor es el gerente administrativo/financiero; el usuario es el técnico de mantenimiento.

### 10.2 Propuesta de valor

- **Evitar picos:** alerta antes de que ocurran.
- **Entender la factura:** PF, reactiva, base, ocupación.
- **Reducir desperdicio:** equipos encendidos fuera de horario.
- **Priorizar inversiones:** compensación reactiva, automatización, mantenimiento.

### 10.3 Modelo de ingresos

- **Suscripción por medidor:** fee mensual por edificio/medidor.
- **Servicio de auditoría + monitoreo:** pago inicial + fee.
- **Ahorro compartido:** 20–30 % del ahorro verificado (requiere M&V).

La fórmula de valor es:

```
ahorro_demanda  = Δpico_kW × cargo_por_demanda
ahorro_reactivo = ΔkVAR × cargo_por_reactivo
ahorro_energía  = ΔkWh × tarifa
```

No se inventan tarifas: se usan las de la factura del edificio.

### 10.4 Competencia y diferenciación

Competidores: Schneider EcoStruxure, Siemens Building X, Bidgely, Enertika, integradores locales. La diferencia:

- Retrofit de bajo costo.
- Conectividad HaLow en edificios sin Wi-Fi industrial.
- Explicación en lenguaje del cliente, no solo gráficas.
- Servicio local y acompañamiento.
- Enfoque en edificios pequeños/medianos, no en grandes cuentas.

### 10.5 Piloto

- 1 edificio (el bloque universitario).
- 3–6 meses.
- Línea base + monitoreo + reporte semanal.
- Medición de ahorro con IPMVP simplificado.
- Caso de estudio y carta de recomendación.

### 10.6 Riesgos

| Riesgo | Mitigación |
|---|---|
| Pocos datos (24 días) | Piloto de 3–6 meses; validación multi-sitio |
| Modelo no generaliza | Calibración por edificio; features simples; monitoreo de deriva |
| Medidor mal configurado | Checklist de puesta en marcha; validación PF > 1 |
| Huecos de red | Buffer local; reintentos; imputación robusta |
| Bajo interés del cliente | Primer win con PF; reporte con ahorro en COP |
| Competencia | Foco en nicho y servicio, no en precio |

---

## 11. Roadmap

| Semana | Hito | Entregable |
|---|---|---|
| 1–2 | Datos y EDA | Serie 1 min, auditoría, features |
| 3–4 | Modelo de pico | Clasificador calibrado, backtest |
| 5–6 | Estados de carga | HMM/clustering, interpretación |
| 7–8 | Dashboard | 4 pantallas, replay |
| 9–10 | Validación | Métricas, comparación, conclusiones |
| 11–12 | Negocio | Caso, presentación, pitch |
| Post-curso | Piloto | 3–6 meses, caso de estudio |

---

## 12. Entregables

- `peakguard_model.ipynb`: preparación, modelos, validación.
- `app.py`: dashboard Streamlit.
- `PEAKGUARD.md`: este documento.
- `presentacion.pdf`: 10–15 diapositivas.
- `data_dictionary.md`: variables y unidades.
- `requirements.txt`: dependencias.
- `README.md`: cómo correr el proyecto.

---

## 13. Métricas de éxito

**Técnicas:** PR-AUC, Brier, calibración, lead time, falsas alarmas, estabilidad de estados.

**De producto:** tiempo de carga del dashboard, claridad de la alerta, generación automática del reporte.

**De negocio:** piloto, clientes potenciales, ahorro estimado, caso de estudio.

---

## 14. Decisiones abiertas

1. Confirmar qué medidor es normal y cuál regulado.
2. Obtener tarifa y factura del bloque.
3. Definir el umbral de pico con el cliente.
4. Conseguir 3–6 meses de datos.
5. Etiquetar eventos con experimentos controlados.
6. Elegir el edificio del piloto.

---

## 15. Anexos

### A. Diccionario de datos

| Variable | Unidad | Descripción |
|---|---|---|
| `active_power_total` | kW | Potencia activa total |
| `apparent_power_total` | kVA | Potencia aparente |
| `reactive_power_total` | kVAR | Potencia reactiva |
| `current_avg` | A | Corriente promedio |
| `voltage_vll_avg` | V | Tensión línea-línea promedio |
| `power_factor` | — | Factor de potencia |
| `frequency` | Hz | Frecuencia |
| `energy_import` | kWh | Energía importada acumulada |

### B. Glosario

- **Pico de demanda:** máximo de potencia en un intervalo.
- **Cargo por demanda:** componente tarifaria basada en el pico.
- **PF:** factor de potencia, P/S.
- **kVAR:** potencia reactiva.
- **NILM:** desagregación no intrusiva de cargas.
- **HMM:** modelo oculto de Markov.
- **Rolling-origin:** validación temporal que avanza en el tiempo.
- **PR-AUC:** área bajo la curva precisión-recall.
- **Brier:** error cuadrático de probabilidades.
- **IPMVP:** protocolo de medición y verificación de ahorros.

### C. Referencias

- scikit-learn: <https://scikit-learn.org>
- statsmodels: <https://www.statsmodels.org>
- Streamlit: <https://streamlit.io>
- IPMVP: <https://www.efficiencyvaluation.org>
- CREG (tarifas y regulación de energía en Colombia).

---

## 16. Método: formulación matemática detallada

Esta sección formaliza el modelo. La idea central es estimar una **probabilidad condicional** de un evento futuro, no ajustar una curva a los datos. La formulación completa es una composición de etapas: un modelo latente (HMM), un mapa de features, un ensamble de árboles, una calibración y una regla de decisión. Ninguna etapa es una sola multiplicación o división; cada una resuelve un problema distinto y todas están sujetas a control de capacidad y validación temporal.

### 16.1 Notación

| Símbolo | Definición |
|---|---|
| $P_t$ | potencia activa total (kW) en el instante $t$ |
| $Q_t$ | potencia reactiva total (kVAR) |
| $I_t$ | corriente promedio (A) |
| $V_t$ | tensión línea-línea promedio (V) |
| $\mathrm{PF}_t$ | factor de potencia |
| $\bar{P}_m$ | media de $P$ en el minuto $m$ |
| $H$ | horizonte de predicción (min) |
| $\tau_P$ | umbral de pico (kW) |
| $Y_t$ | target binario de pico |
| $\mathcal{F}_t$ | historia disponible hasta $t$ |
| $x_t$ | vector de features |
| $\hat{p}_t$ | probabilidad estimada de pico |
| $S_t$ | estado latente de carga |
| $\gamma_{t,k}$ | probabilidad posterior del estado $k$ |
| $C$ | clase de causa del evento |
| $a_t$ | alerta binaria |
| $\tau^*$ | umbral de decisión |

### 16.2 Riesgo esperado, riesgo empírico y generalización

El objetivo no es minimizar el error en los datos observados, sino el error esperado en datos futuros:

$$
R(f)=\mathbb{E}_{(x,y)\sim\mathcal{D}}\big[L(y,f(x))\big]
\qquad\text{(riesgo esperado)}
$$

$$
\hat{R}_n(f)=\frac{1}{n}\sum_{i=1}^{n}L(y_i,f(x_i))
\qquad\text{(riesgo empírico)}
$$

La diferencia $R(f)-\hat{R}_n(f)$ es la **brecha de generalización**. Memorizar es hacer $\hat{R}_n\to 0$ mientras $R$ aumenta. El diseño del modelo se orienta a controlar esa brecha mediante **minimización del riesgo estructural**:

$$
\min_{\theta}\ \hat{R}_n(\theta)+\lambda\,\Omega(\theta),
$$

donde $\Omega(\theta)$ penaliza la complejidad y $\lambda$ se elige por validación. Una cota clásica (VC) formaliza el compromiso:

$$
R(f)\le\hat{R}_n(f)+
\sqrt{\frac{d_{VC}\big(\log(2n/d_{VC})+1\big)+\log(4/\delta)}{n}},
$$

con probabilidad $1-\delta$. Con $n$ fijo (24 días), aumentar la capacidad $d_{VC}$ agranda la brecha. Por eso el modelo debe ser lo más simple que capture la estructura, no lo más complejo posible.

### 16.3 Agregación multi-resolución y definición del target

La serie de 1 min se construye como **media** de las muestras de alta resolución, no como una muestra decimada:

$$
\bar{P}_m=
\begin{cases}
\dfrac{1}{|\mathcal{T}_m|}\displaystyle\sum_{t\in\mathcal{T}_m}P_t, & |\mathcal{T}_m|\ge n_{\min},\\[6pt]
\mathrm{NaN}, & \text{en otro caso},
\end{cases}
\qquad
\mathcal{T}_m=\{t:\ m\le t<m+1\text{ min}\}.
$$

Si el minuto no tiene suficientes muestras (hueco o cadencia insuficiente), se marca como faltante y no se usa para entrenar. El target se define con horizonte $H$ y umbral $\tau_P$:

$$
Y_t=
\begin{cases}
\mathbf{1}\!\left\{\displaystyle\max_{1\le h\le H}\bar{P}_{t+h}>\tau_P\right\}, & \text{si todos los }\bar{P}_{t+h}\text{ existen},\\[6pt]
\mathrm{NaN}, & \text{si falta alguno}.
\end{cases}
$$

La salida del modelo es:

$$
\boxed{\ \hat{p}_t=\mathbb{P}\big(Y_t=1\mid\mathcal{F}_t\big)\ }
$$

Es decir, la probabilidad de un evento futuro condicionada a toda la historia pasada. No es una función determinística de $P_t$; depende de la tendencia, la hora, el estado de carga y los eventos recientes.

### 16.4 Mapa de features

Toda la información entra por un vector determinístico:

$$
x_t=\phi(\mathcal{F}_t,\gamma_t)\in\mathbb{R}^{d},
$$

con las siguientes componentes:

- **Rezagos:** $P_{t-k},Q_{t-k},I_{t-k},V_{t-k}$ para $k\in\{1,5,15,60\}$ min.
- **Ventanas móviles:** media, desvío y máximo de $P$ en ventanas $W\in\{5,15,60\}$ min.
- **Calendario:** hora, día de la semana, fin de semana, feriado (one-hot).
- **Eléctricas:** $\mathrm{PF}_t$, $Q_t$, $V_t$, desbalance de fases.
- **Eventos:** cantidad y energía de eventos en la última hora, tiempo desde el último evento.
- **Estados:** $\gamma_{t,1},\dots,\gamma_{t,K}$ del HMM.

El mapa $\phi$ es fijo y de dimensión controlada. No es una tabla que guarda cada muestra; es una representación comprimida de la historia. Para el baseline logístico se estandarizan las features; los árboles son invariantes a transformaciones monótonas.

### 16.5 Modelo de estados (HMM)

El estado de carga $S_t\in\{1,\dots,K\}$ no se observa; se infiere. Se modela con un HMM gaussiano sobre $o_t=(\bar{P}_t,\bar{Q}_t)$:

$$
A_{ij}=\mathbb{P}(S_t=j\mid S_{t-1}=i),
\qquad
p(o_t\mid S_t=k)=\mathcal{N}(o_t;\mu_k,\Sigma_k),
$$

con parámetros $\lambda=(\pi,A,\{\mu_k,\Sigma_k\})$. La verosimilitud de la secuencia es:

$$
p(o_{1:T};\lambda)
=
\sum_{s_{1:T}}
\pi_{s_1}\,p(o_1\mid s_1)
\prod_{t=2}^{T}
A_{s_{t-1},s_t}\,p(o_t\mid s_t),
$$

y se maximiza con **EM (Baum-Welch)**. En el paso E se calculan las posteriores $\gamma_{t,k}=\mathbb{P}(S_t=k\mid o_{1:T})$ y las transiciones $\xi_{t,ij}=\mathbb{P}(S_t=i,S_{t+1}=j\mid o_{1:T})$; en el paso M se actualizan:

$$
\mu_k=\frac{\sum_t\gamma_{t,k}o_t}{\sum_t\gamma_{t,k}},
\qquad
\Sigma_k=\frac{\sum_t\gamma_{t,k}(o_t-\mu_k)(o_t-\mu_k)^\top}{\sum_t\gamma_{t,k}},
$$

$$
A_{ij}=\frac{\sum_t\xi_{t,ij}}{\sum_t\sum_j\xi_{t,ij}},
\qquad
\pi_k=\gamma_{1,k}.
$$

Para las features del clasificador se usa la **posterior causal**, calculada con el filtro hacia adelante y no con suavizado:

$$
\alpha_{t,k}=p(o_t\mid S_t=k)\sum_{j=1}^{K}A_{jk}\,\alpha_{t-1,j},
\qquad
\gamma_{t,k}=\frac{\alpha_{t,k}}{\sum_{j=1}^{K}\alpha_{t,j}}.
$$

Así, en el instante $t$ solo se usa $o_{1:t}$; no se filtra información del futuro. En EM se usa la posterior suavizada (que mira toda la secuencia), pero en las features se usa la filtrada; el contexto indica cuál. El número de estados se fija en $K\in\{3,4,5\}$ y se elige por log-likelihood en validación e interpretabilidad. Los estados son identificables solo hasta permutación; se ordenan por potencia media para asignarles nombre (base, ocupación, evento, carga alta).

### 16.6 Modelo discriminativo

**Baseline logístico:**

$$
\eta_t=\beta_0+\beta^\top x_t,
\qquad
\hat{p}_t=\sigma(\eta_t)=\frac{1}{1+e^{-\eta_t}}.
$$

**Modelo principal (gradient boosting):** una expansión aditiva de árboles,

$$
f_\theta(x)=\sum_{m=1}^{M}\nu\,T_m(x;\Theta_m),
\qquad
T_m(x)=\sum_{j=1}^{J_m}c_{mj}\,\mathbf{1}\{x\in R_{mj}\},
$$

donde $T_m$ parte el espacio en regiones $R_{mj}$ y asigna una constante $c_{mj}$, $\nu$ es la tasa de aprendizaje y $M$ el número de árboles. La probabilidad es:

$$
\hat{p}_t=\sigma\big(f_\theta(x_t)\big).
$$

El entrenamiento minimiza la entropía cruzada regularizada:

$$
\mathcal{L}(\theta)
=
-\frac{1}{N}\sum_{t=1}^{N}
\Big[y_t\log\hat{p}_t+(1-y_t)\log(1-\hat{p}_t)\Big]
+\lambda_1\|\theta\|_1+\lambda_2\|\theta\|_2.
$$

La capacidad se controla con $M$, la profundidad, $J_m$, `min_samples_leaf`, $\nu$ y el submuestreo. Esos son los mecanismos que impiden que el modelo memorice.

### 16.7 Calibración

El clasificador devuelve un puntaje, no una probabilidad confiable. Se calibra con una función monótona ajustada **fuera de muestra**:

$$
\hat{p}_t^{\text{cal}}=g^{-1}\big(\hat{p}_t\big),
$$

con calibración isotónica o Platt:

$$
\hat{p}^{\text{cal}}=\sigma\big(a\,\mathrm{logit}(\hat{p})+b\big).
$$

La calidad de la calibración se mide con el error de calibración esperado:

$$
\mathrm{ECE}=\sum_{b=1}^{B}\frac{|B_b|}{N}\,
\big|\mathrm{acc}(B_b)-\mathrm{conf}(B_b)\big|,
$$

donde $B_b$ es el conjunto de muestras del bin $b$, $\mathrm{acc}(B_b)$ la frecuencia observada de positivos en ese bin y $\mathrm{conf}(B_b)$ la probabilidad media estimada. Sin calibración, el umbral de decisión no tiene interpretación económica.

### 16.8 Decisión

La alerta se dispara con un umbral $\tau$:

$$
a_t=\mathbf{1}\{\hat{p}_t^{\text{cal}}\ge\tau\}.
$$

Si las probabilidades están calibradas, el umbral óptimo bajo costos asimétricos es:

$$
\boxed{\ \tau^*=\frac{C_{FP}}{C_{FP}+C_{FN}}\ }
$$

donde $C_{FP}$ es el costo de una falsa alarma y $C_{FN}$ el costo de un pico no advertido. La derivación es directa: alertar cuesta $C_{FP}(1-p)$; no alertar cuesta $C_{FN}\,p$. Se alerta si $C_{FP}(1-p)<C_{FN}\,p$, es decir, si $p>C_{FP}/(C_{FP}+C_{FN})$.

### 16.9 Atribución de causa

La causa no se adivina por la hora: se infiere de la **firma** del evento. Se define el vector de cambio:

$$
\Delta_t=
\big[\Delta P_t,\Delta Q_t,\Delta I_t,\Delta V_t,\Delta\mathrm{PF}_t,\mathrm{bal}_t,d_t\big],
$$

donde $\mathrm{bal}_t$ mide el balance entre fases y $d_t$ la duración. La causa se estima como:

$$
\hat{c}_t=\arg\max_{c\in\mathcal{C}}\ \mathbb{P}\big(C=c\mid\Delta_t,\gamma_t\big),
$$

con $\mathcal{C}=\{$resistiva, motor, condensador, pérdida de carga, error de medición$\}$. Puede implementarse como un clasificador supervisado (si hay etiquetas de experimentos) o como un conjunto de reglas físicas. Antes de atribuir la causa se verifica la consistencia:

$$
S_t=\sqrt{3}\,V_t I_t,
\qquad
P_t=\sum_{\ell=1}^{3}P_{t,\ell},
\qquad
\mathrm{PF}_t=\frac{P_t}{S_t}.
$$

Si alguna identidad no se cumple, el evento se clasifica como error de medición, no como carga.

### 16.10 Magnitud del pico (opcional)

Si además de la probabilidad se quiere la magnitud:

$$
M_t=\max_{1\le h\le H}\bar{P}_{t+h},
$$

se estima un cuantil con regresión cuantílica:

$$
\hat{q}_\alpha(x_t)=\arg\min_{q}\ \mathbb{E}\big[\rho_\alpha(M_t-q)\big],
\qquad
\rho_\alpha(u)=\max\{\alpha u,(\alpha-1)u\}.
$$

Así se puede reportar “70 % de probabilidad de superar 12 kW y pico esperado entre 14 y 17 kW”.

### 16.11 Control de capacidad y anti-memorización

La formulación anterior es deliberadamente no lineal y multicapa, pero la complejidad se controla en cada etapa:

- **HMM:** $K=3$ a $5$ estados, no uno por muestra.
- **Árboles:** profundidad 2–3, `min_samples_leaf` alto, $M=100$–$300$, $\nu=0{,}03$–$0{,}1$.
- **Regularización:** L1/L2 y `l2_regularization` en el boosting.
- **Early stopping:** se detiene cuando la pérdida de validación deja de bajar.
- **Calibración out-of-fold:** nunca se ajusta con las predicciones de entrenamiento.
- **Ensamble:** promedio de $E$ modelos,
  $$
  \hat{p}(x)=\frac{1}{E}\sum_{e=1}^{E}\hat{p}_e(x),
  $$
  para reducir varianza.
- **Validación temporal:** rolling-origin, nunca split aleatorio.
- **Curvas de aprendizaje:** se compara pérdida de entrenamiento contra validación; si la brecha crece, se reduce capacidad.
- **Test final reservado:** no se toca hasta el cierre.

### 16.12 Protocolo de validación y métricas

La validación avanza en el tiempo:

$$
\mathcal{D}_{\text{train}}^{(k)}=\{t\le T_k\},
\qquad
\mathcal{D}_{\text{test}}^{(k)}=\{T_k<t\le T_{k+1}\},
\qquad
k=1,\dots,K.
$$

Los hiperparámetros se eligen con validación anidada dentro de cada fold; el test final se reserva. Métricas:

| Tarea | Métrica | Definición |
|---|---|---|
| Clasificación | PR-AUC | área bajo la curva precisión-recall |
| Clasificación | Brier | $\frac{1}{N}\sum_t(\hat{p}_t-y_t)^2$ |
| Clasificación | ECE | error de calibración esperado |
| Clasificación | Recall@precision | recall a una precisión fija |
| Operación | Lead time | minutos entre alerta y cruce del umbral |
| Operación | Falsas alarmas/día | alertas sin evento en la ventana |
| Estados | Log-likelihood | verosimilitud en días held-out |
| Estados | ARI | estabilidad entre submuestras |
| Magnitud | MAE/RMSE | error del pico estimado |
| Magnitud | Pinball | pérdida cuantílica |

El baseline obligatorio es la persistencia (“¿superó el umbral en la última hora?”) y la climatología (“mismo día y hora de la semana anterior”). Si el modelo no le gana al baseline en PR-AUC y Brier, no aporta.

### 16.13 Algoritmo completo

```text
Entrada: serie cruda P, Q, I, V (10 s), calendario, umbral τ_P, horizonte H
1. Agregar a 1 min como media; marcar huecos; construir Y_t.
2. Dividir en folds temporales (rolling-origin).
3. Para cada fold:
   a. Ajustar HMM con los datos de entrenamiento (EM).
   b. Calcular γ_t con filtro hacia adelante (sin futuro).
   c. Construir x_t = φ(historia, γ_t).
   d. Ajustar GBM con early stopping en validación.
   e. Calibrar con predicciones out-of-fold.
   f. Elegir τ* = C_FP / (C_FP + C_FN).
   g. Evaluar en test: PR-AUC, Brier, ECE, lead time, falsas alarmas.
4. Entrenar el modelo final con todos los datos de desarrollo.
5. Reservar el test final y reportar.
6. Explicar cada alerta con SHAP y el estado dominante.
Salida: p_t calibrada, causa estimada, alerta a_t, reporte.
```

### 16.14 Supuestos y limitaciones

- El modelo es **predictivo, no causal**: estima el riesgo dado el pasado, no el efecto de una intervención.
- Se asume **estacionariedad condicional** dentro del mismo tipo de día; si cambia el edificio o el horario, se recalibra.
- El HMM tiene **identificabilidad solo hasta permutación**; los estados se ordenan por potencia media.
- Los huecos son **MNAR** (no faltan al azar): se enmascaran y no se imputan para el modelo.
- El medidor 201 no se usa para PF ni para atribución por fase hasta corregir su configuración.
- Con 24 días, el modelo es un **MVP**; la generalización a otros edificios requiere piloto y recalibración.

### 16.15 Implementación

| Etapa | Herramienta |
|---|---|
| HMM | `hmmlearn.GaussianHMM` (EM) |
| Filtro causal | implementar forward o usar una librería que exponga filtering |
| Features | `pandas`, `numpy` |
| Clasificador | `HistGradientBoostingClassifier` o `LGBMClassifier` |
| Calibración | `CalibratedClassifierCV` / `IsotonicRegression` |
| Validación | `TimeSeriesSplit` + rolling-origin |
| Métricas | `average_precision_score`, `brier_score_loss`, `calibration_curve` |
| Explicabilidad | `shap`, `permutation_importance` |
| Cuantiles | `statsmodels` (`QuantReg`) |

**Advertencia de implementación:** `hmmlearn.predict_proba` calcula la posterior suavizada sobre toda la secuencia. Para las features causales hay que usar el **filtro hacia adelante**; de lo contrario se filtra información del futuro y el modelo “parece” mejor de lo que es.

---

## 17. Diagramas

- Arquitectura y flujo de datos: [`docs/diagrama_arquitectura.png`](docs/diagrama_arquitectura.png)
- Flujo de trabajo: [`docs/diagrama_flujo_trabajo.png`](docs/diagrama_flujo_trabajo.png)
- Versión editable (Mermaid) y explicación: [`docs/DIAGRAMA_PROYECTO.md`](docs/DIAGRAMA_PROYECTO.md)

---

## 18. Notebooks y resultados

- [`01_data_audit.ipynb`](01_data_audit.ipynb): pipeline de 1 min, auditoría de cobertura/cadencia y validación física.
- [`02_peak_model.ipynb`](02_peak_model.ipynb): target, ecuación logística, validación rolling-origin, calibración y pruebas de generalización.
- [`03_evaluation.ipynb`](03_evaluation.ipynb): evaluación operativa retrospectiva con episodios de pico, alertas, lead time, costo y análisis de errores.
- [`README.md`](README.md): instrucciones, ecuación ajustada y resultados.
- [`data/processed/medidor200_1min.csv`](data/processed/medidor200_1min.csv): serie de 1 min del medidor 200.
- [`reports/`](reports/): figuras y tablas.
- [`models/peak_logit.joblib`](models/peak_logit.joblib): modelo final y calibrador.

**Resultado principal:** la ecuación logística de 7 features alcanza un PR-AUC mediano de 0,458 en validación rolling-origin (tasa base 0,027) y un Brier de 0,014. En el holdout calibrado, PR-AUC 0,380, Brier 0,016. Las etiquetas barajadas caen a 0,021 (≈ azar) y la curva de aprendizaje mejora con más datos: el modelo generaliza, no memoriza.
