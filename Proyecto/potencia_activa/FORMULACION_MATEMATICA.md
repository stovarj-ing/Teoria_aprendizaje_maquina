# Pronóstico de potencia activa a 24 horas — formulación matemática

| Campo | Valor |
|---|---|
| **Curso** | Teoría del Aprendizaje de Máquina — VIII semestre |
| **Datos** | PM5300, medidor 200 (red normal), agregados de 1 min a 1 h |
| **Periodo** | 6 de octubre a 21 de noviembre de 2026 |
| **Documento** | Planteamiento formal, derivación de los modelos, protocolo de validación y lectura de resultados |

---

## 0. Qué contiene este documento y cómo leerlo

Este documento formaliza el proyecto de pronóstico de potencia activa del bloque universitario. No es un resumen del notebook: es el **desarrollo matemático** de lo que el notebook implementa. Cada definición está conectada con la sección, la tabla o el archivo de código que la produce.

El orden es deliberado:

1. Primero se define el objeto de estudio y la información disponible.
2. Después se construye el problema de aprendizaje supervisado.
3. Luego se derivan los modelos, empezando por los baselines más simples.
4. Se define el protocolo de validación y se demuestra qué garantiza y qué no.
5. Se presentan los resultados y se descomponen los errores.
6. Se cierra con la función de pronóstico, las limitaciones y las extensiones.

**Convención de lectura:** las fórmulas con subíndice $t$ se refieren a la serie horaria; $t_0$ es el origen del pronóstico; $h$ es el horizonte; $y$ es el valor observado; $\hat y$ es el valor pronosticado. Todos los tiempos están en hora local de Colombia (`America/Bogota`, UTC−5, sin horario de verano). Los números siguen la convención colombiana: punto para miles ($10.227$) y coma para decimales ($0{,}274$). Las fórmulas usan `$...$` para matemática en línea y `$$...$$` para bloques; se renderizan en GitHub, Obsidian, VS Code con extensión de matemáticas y Jupyter.

**Resultado principal:** el modelo final es un híbrido entre una climatología por hora y tipo de día y un GBM sobre el residuo. En la mediana de 5 folds obtiene MAE $0{,}274$ kW, RMSE $0{,}454$ kW y skill $0{,}634$ frente al seasonal naive. En el último fold, el MAE sube a $0{,}643$ kW; la causa principal es un lunes festivo no modelado (16-11-2026), no una falla de generalización en el régimen normal.

---

## 1. Notación

| Símbolo | Significado |
|---|---|
| $t$ | Índice horario local |
| $P_t$ | Potencia activa media de la hora $t$, en kW |
| $t_0$ | Origen del pronóstico |
| $h$ | Horizonte, $h \in \{1,\dots,24\}$ |
| $H$ | Ventana de pronóstico, $H=24$ |
| $y$ | Valor objetivo, $y=P_{t_0+h}$ |
| $\hat y$ | Pronóstico de $y$ |
| $x$ | Vector de features de la fila $(t_0,h)$ |
| $f$ | Función de pronóstico |
| $\theta$ | Parámetros del modelo |
| $\mathcal{D}_{\text{tr}}$ | Conjunto de entrenamiento |
| $\mathcal{D}_{\text{te}}$ | Conjunto de prueba |
| $w(t)$ | Indicador de fin de semana: $w(t)=\mathbf{1}\{\text{dow}(t)\ge 5\}$ |
| $\text{dow}(t)$ | Día de la semana, $0=$ lunes, $6=$ domingo |
| $M_t$ | Minutos con dato dentro de la hora $t$ |
| $n_t$ | $\lvert M_t\rvert$, número de minutos válidos en la hora $t$ |
| $p_m$ | Potencia de 1 min en el minuto $m$ |
| $\bar P_t$ | Media horaria de potencia |
| $c_{h,w}$ | Climatología: media de $y$ para hora $h$ y tipo de día $w$ |
| $r$ | Residuo, $r=y-c_{h,w}$ |
| $\varepsilon$ | Error de pronóstico, $\varepsilon=y-\hat y$ |
| $\Delta$ | Error diario con signo, $\Delta=\hat E-E$ |
| $\mathrm{MAE}$ | Error absoluto medio |
| $\mathrm{RMSE}$ | Raíz del error cuadrático medio |
| $\mathrm{MAPE}$ | Error porcentual absoluto medio |
| R² | Coeficiente de determinación |

**Convención de signos.** En el análisis de error se usa $\varepsilon=y-\hat y$: positivo significa que el modelo **subestimó**. En el análisis de energía diaria se usa $\Delta=\hat E-E$: positivo significa que el modelo **sobrestimó**. La diferencia es intencional y se indica en cada tabla.

---

## 2. Datos

### 2.1 Serie original de 1 minuto

El punto de partida es la serie de potencia activa del medidor 200:

$$
\{p_m\}_{m=1}^{N}, \qquad p_m \in \mathbb{R}^{+}\ \text{(kW)}.
$$

La serie tiene $N=66.767$ minutos, desde el 6 de octubre de 2026 a las 15:13 hasta el 21 de noviembre de 2026 a las 23:59 (hora local). El $45{,}3\,\%$ de los minutos no tiene dato de potencia ($30.268$ valores faltantes). Los faltantes no son aleatorios: corresponden a caídas del medidor, ventanas de mantenimiento y periodos sin comunicación.

**Por qué no se imputa.** Imputar la potencia con interpolación crearía una serie artificialmente suave, reduciría la varianza del target y contaminaría la evaluación: el modelo aprendería una señal que no existe. Además, una interpolación que use el futuro introduciría fuga temporal. Por eso los faltantes se conservan como `NaN` y las filas que los necesitan se descartan.

### 2.2 Agregación horaria

Para cada hora $t$ se define el conjunto de minutos válidos:

$$
M_t=\{m:\ m\in[t,t+1\text{ h}),\ p_m\ \text{observado}\}, \qquad n_t=|M_t|.
$$

La potencia horaria es la media de los minutos válidos:

$$
\bar P_t=
\begin{cases}
\dfrac{1}{n_t}\displaystyle\sum_{m\in M_t} p_m, & n_t\ge 30,\\[1.2em]
\text{NaN}, & n_t<30.
\end{cases}
\qquad (2.1)
$$

**Interpretación física.** Si la potencia fuera constante durante la hora, la energía sería $E_t=\bar P_t\times 1\text{ h}$, es decir, el número de kW medios es numéricamente igual al número de kWh de esa hora. Por eso la media horaria es la agregación correcta para un pronóstico de energía: sumar 24 potencias medias equivale a estimar la energía del día.

**Supuesto estadístico.** Cuando $n_t<60$, la media de los minutos observados estima la media de la hora completa bajo el supuesto de que los minutos faltantes tienen la misma media que los observados (missing at random dentro de la hora). Es un supuesto fuerte; se mitiga exigiendo $n_t\ge 30$. Si la hora tiene menos de 30 minutos, la estimación es demasiado ruidosa y se descarta.

**Resultado.** La serie horaria tiene $1.113$ slots y $609$ horas válidas, es decir, el $54{,}7\,\%$. La cobertura horaria es la limitación dominante del proyecto.

### 2.3 Estadísticos de la serie horaria

| Estadístico | Valor |
|---|---:|
| Horas válidas | 609 |
| Media | $6{,}403$ kW |
| Desviación estándar | $1{,}542$ kW |
| Mediana | $5{,}520$ kW |
| Mínimo | $5{,}242$ kW |
| Máximo | $11{,}310$ kW |
| Coeficiente de variación | $0{,}241$ |
| Asimetría | $1{,}315$ |
| Exceso de curtosis | $0{,}273$ |
| Horas con $P<6$ kW | $66{,}7\,\%$ |
| Horas con $P<8$ kW | $79{,}1\,\%$ |

La distribución es **bimodal en la práctica**: una base estable alrededor de $5{,}4$ kW y un régimen diurno de $8$–$10$ kW cuando el bloque está ocupado. Dos tercios de las horas están por debajo de $6$ kW; el consumo alto es la excepción, no la regla. Esto tiene una consecuencia directa: un modelo que acierte la base y falle la ocupación diurna puede tener un MAE bajo y, aun así, un error grande en la energía del día.

### 2.4 Perfil horario

Perfil medio (media de $P_t$ por hora y tipo de día):

| Hora | Laboral (kW) | Fin de semana (kW) |
|---:|---:|---:|
| 00 | 5,43 | 5,38 |
| 06 | 5,61 | 5,42 |
| 07 | 6,85 | 5,37 |
| 08 | 8,22 | 5,48 |
| 10 | 9,53 | 5,96 |
| 12 | 8,36 | 5,46 |
| 15 | 8,87 | 5,54 |
| 18 | 6,67 | 5,46 |
| 21 | 5,55 | 5,39 |
| 23 | 5,43 | 5,38 |

El perfil laboral tiene cuatro fases: base nocturna ($5{,}4$ kW), rampa de entrada ($7$–$9$ kW entre 07:00 y 09:00), meseta diurna ($8$–$9{,}5$ kW) y descenso desde las 17:00. El fin de semana es casi plano: la ocupación no existe y solo queda la base. La diferencia entre ambos perfiles es la **carga de ocupación**, que es exactamente la variable que un calendario de festivos y de actividad académica podría explicar.

> **Conexión con el código.** El perfil exploratorio del notebook usa la **mediana** por hora y tipo de día. El modelo de climatología usa la **media** por celda. No son lo mismo: la media es el estimador adecuado para pérdida cuadrática y para energía; la mediana es más robusta para visualizar. La diferencia típica es de $\pm0{,}2$ kW.

### 2.5 Autocorrelación

Sobre la grilla horaria completa (con `NaN` en los huecos), calculando cada par $(P_t,P_{t-\ell})$ solo cuando ambos valores existen:

| Rezago $\ell$ | ACF | Pares |
|---:|---:|---:|
| 1 h | 0,932 | 594 |
| 2 h | 0,802 | 586 |
| 3 h | 0,662 | 577 |
| 24 h | 0,581 | 443 |
| 48 h | 0,273 | 331 |

La persistencia de corto plazo es muy alta: la correlación con la hora anterior es $0{,}932$. La estacionalidad diaria también es fuerte ($0{,}581$ a 24 h). Los rezagos semanales tienen muy pocos pares completos ($292$ a 168 h) y no se usan para inferencia; el modelo los usa como feature, no como evidencia descriptiva.

**Consecuencia.** Un baseline de persistencia ($P_t$) es razonable a 1 h pero malo a 24 h. Un baseline seasonal naive ($P_{t-24}$) es mucho mejor a 24 h. El modelo tiene que superar a este último, no al primero.

---

## 3. Formulación del problema

### 3.1 Proceso estocástico e información

Se modela la potencia como un proceso estocástico $\{P_t\}_{t\in\mathbb{Z}}$ en tiempo discreto horario. Sea $\mathcal{F}_{t_0}$ la información disponible en el origen:

$$
\mathcal{F}_{t_0} =
\sigma\left(
\{P_s:\ s\le t_0\}
\ \cup\
\{\text{calendario}(s):\ s\le t_0+24\}
\right).
\qquad (3.1)
$$

El calendario futuro es determinista (hora, día de la semana, fin de semana), así que se conoce en $t_0$. El objetivo es, para cada $h=1,\dots,24$,

$$
\hat y_{t_0+h} =
\mathbb{E}\left[P_{t_0+h}\mid \mathcal{F}_{t_0}\right].
\qquad (3.2)
$$

Esta es la **esperanza condicional**. Es el pronóstico que minimiza el error cuadrático medio. Si se quisiera minimizar el error absoluto, el óptimo sería la **mediana condicional**, que no coincide con la media en una distribución asimétrica. El proyecto usa pérdida cuadrática para entrenar y reporta MAE y RMSE; la distinción se retoma en la sección 6.

### 3.2 Pronóstico directo multi-horizonte

Hay tres formas de pronosticar 24 horas:

1. **Recursiva:** entrenar un modelo a 1 h y alimentarlo con sus propias predicciones:
   $\hat y_{t_0+h}=f\left(\hat y_{t_0+h-1},x_{t_0}\right)$.
   Es simple, pero los errores se acumulan: un error a 1 h se convierte en input del paso 2, y así sucesivamente.

2. **Directa con 24 modelos:** entrenar un modelo $f_h$ por horizonte:
   $\hat y_{t_0+h}=f_h\left(x_{t_0}\right)$, con $h=1,\dots,24$.
   Evita la acumulación, pero cada modelo ve solo $1/24$ de los datos y no comparte información entre horizontes.

3. **Directa con un solo modelo y el horizonte como feature:**
   $\hat y_{t_0+h}=f\left(x_{t_0},h\right)$.
   Es la que se usa. Cada fila es un pronóstico genuino a $h$ pasos; no se usan predicciones intermedias; el modelo comparte fuerza estadística entre horizontes y aprende correcciones específicas de $h$ a través de la feature `horizon`.

**Supuesto de la forma directa.** Se asume que la función $f(x,h)$ es suave en $h$: lo que se aprende para $h=10$ ayuda a $h=11$. Con 25 días de entrenamiento, este supuesto es necesario; sin él, cada horizonte tendría muy pocos ejemplos.

### 3.3 Pérdida y riesgo

El entrenamiento minimiza el riesgo empírico con pérdida cuadrática:

$$
L_2(y,\hat y)=\frac12\left(y-\hat y\right)^2,
\qquad
\hat R_{\text{emp}}(f) =
\frac{1}{|\mathcal{D}_{\text{tr}}|}
\sum_{(x,y)\in\mathcal{D}_{\text{tr}}}
L_2\left(y,f(x)\right).
\qquad (3.4)
$$

La evaluación usa pérdida absoluta:

$$
L_1(y,\hat y)=\left|y-\hat y\right|.
\qquad (3.5)
$$

**Por qué dos pérdidas distintas.** La pérdida cuadrática es diferenciable y castiga fuerte los errores grandes; el GBM la usa para aprovechar los gradientes. La pérdida absoluta es robusta y se interpreta directamente en kW; es la métrica que le importa a un operador. Un modelo entrenado con $L_2$ estima la media condicional; evaluarlo con $L_1$ mide qué tan cerca está de la mediana condicional. En una distribución asimétrica, ambas pueden diferir. El proyecto reporta las dos para no esconder esa diferencia.

### 3.4 Clase de hipótesis

El modelo final no es una función arbitraria: es la suma de dos componentes,

$$
f(x)=c_{h(x),w(x)}+g(x),
\qquad (3.6)
$$

donde $c$ es una tabla de medias por hora y tipo de día (climatología) y $g$ es un GBM sobre el residuo. Los baselines lineales (Ridge) y el GBM directo son casos particulares o alternativas de esta clase. La sección 8 deriva cada uno.

---

## 4. Construcción del dataset supervisado

### 4.1 Orígenes válidos

Sea $t_{\max}$ el último timestamp de la serie horaria. Un origen $t_0$ es válido si:

$$
P_{t_0}\ \text{observado}
\quad\text{y}\quad
t_0+24\le t_{\max}.
\qquad (4.1)
$$

El conjunto de orígenes es

$$
\mathcal{T}_0=\{t_0:\ \text{(4.1) se cumple}\}.
\qquad (4.2)
$$

No se usan orígenes con $P_{t_0}$ faltante: sin la potencia actual no se pueden construir los rezagos ni la media móvil. Tampoco se usan orígenes a menos de 24 h del final: no tendrían ventana completa.

### 4.2 Filas del dataset

Para cada $t_0\in\mathcal{T}_0$ y cada $h=1,\dots,24$, se construye una fila si:

$$
P_{t_0+h}\ \text{observado}
\quad\text{y}\quad
P_{t_0+h-24}\ \text{observado}.
\qquad (4.3)
$$

La segunda condición es necesaria porque `prev_day` es una feature obligatoria: sin el valor de la misma hora del día anterior, la fila no se puede construir. No se imputa.

La fila contiene:

$$
\left(x_{t_0,h},\ y_{t_0,h}\right),
\qquad
y_{t_0,h}=P_{t_0+h}.
\qquad (4.4)
$$

### 4.3 Mapa de features

| Grupo | Feature | Definición | ¿Conocida en $t_0$? |
|---|---|---|---|
| Origen | `P_origin` | $P_{t_0}$ | Sí |
| Origen | `lag1` | $P_{t_0-1}$ | Sí |
| Origen | `lag24` | $P_{t_0-24}$ | Sí |
| Origen | `lag168` | $P_{t_0-168}$ | Sí |
| Origen | `roll3` | $\frac13\sum_{j=0}^{2}P_{t_0-j}$ | Sí |
| Origen | `roll6` | $\frac16\sum_{j=0}^{5}P_{t_0-j}$ | Sí |
| Origen | `roll24` | $\frac1{24}\sum_{j=0}^{23}P_{t_0-j}$ | Sí |
| Origen | `std24` | desviación estándar de $P_{t_0-23},\dots,P_{t_0}$ (`ddof=1`) | Sí |
| Objetivo | `prev_day` | $P_{t_0+h-24}$ | Sí, porque $h\le24$ |
| Objetivo | `prev_week` | $P_{t_0+h-168}$ | Sí, porque $h\le24<168$ |
| Calendario | `target_hour` | hora local de $t_0+h$ | Sí (determinista) |
| Calendario | `target_dow` | día de la semana de $t_0+h$ | Sí (determinista) |
| Calendario | `target_weekend` | $\mathbf{1}\{\text{dow}\ge5\}$ | Sí (determinista) |
| Origen | `origin_hour` | hora local de $t_0$ | Sí |
| Origen | `origin_dow` | día de la semana de $t_0$ | Sí |
| Horizonte | `horizon` | $h$ | Sí |
| Fourier | `hour_sin1`, `hour_cos1` | $\sin(2\pi\,\text{hora}/24)$, $\cos(\cdot)$ | Sí |
| Fourier | `hour_sin2`, `hour_cos2` | $\sin(4\pi\,\text{hora}/24)$, $\cos(\cdot)$ | Sí |
| Fourier | `hour_sin3`, `hour_cos3` | $\sin(6\pi\,\text{hora}/24)$, $\cos(\cdot)$ | Sí |
| Fourier | `dow_sin`, `dow_cos` | $\sin(2\pi\,\text{dow}/7)$, $\cos(\cdot)$ | Sí |

**Reglas de relleno.** Para que el dataset no pierda filas por features auxiliares:

- `lag1`, `lag24`, `roll3`, `roll6`, `roll24`: si el valor es `NaN`, se usa $P_{t_0}$.
- `lag168`: si es `NaN`, se usa `lag24`.
- `std24`: si es `NaN`, se usa $0$.
- `prev_week`: si es `NaN`, se usa `prev_day`.
- `prev_day`: **no** tiene relleno; si falta, la fila se descarta.

Estos rellenos son conservadores: reemplazan un dato faltante por el valor actual del origen, que es la mejor estimación disponible sin usar el futuro. Introducen un sesgo hacia la persistencia en los bordes de la serie; por eso las primeras filas tienen menos cobertura.

### 4.4 Prueba de no fuga temporal

Para $h\in\{1,\dots,24\}$:

$$
t_0+h-24\le t_0
\qquad\text{y}\qquad
t_0+h-168<t_0.
\qquad (4.5)
$$

Además, todos los rezagos y medias móviles están evaluados en $t_0$ o antes, y las features de calendario son deterministas. Por lo tanto, **todo el vector $x_{t_0,h}$ es $\mathcal{F}_{t_0}$-medible**. El target $P_{t_0+h}$ está en $t_0+h>t_0$, estrictamente en el futuro. No hay fuga de información del target hacia las features.

Esta prueba es sobre las **features**, no sobre la partición. La partición tiene una sutileza adicional que se discute en la sección 7.4.

### 4.5 Conteo y solapamiento

| Concepto | Valor |
|---|---:|
| Filas totales | 10.227 |
| Orígenes | 573 |
| Días de origen | 30 |
| Filas por origen | 17,85 |
| Máximo teórico ($573\times24$) | 13.752 |
| Retención | 74,4 % |

El máximo teórico no se alcanza porque faltan targets, falta `prev_day` o el origen está cerca del final. La retención del $74{,}4\,\%$ es razonable para una serie con $45{,}3\,\%$ de faltantes.

**El solapamiento es la propiedad estadística más importante del dataset.** Un mismo target $P_\tau$ puede aparecer en hasta 24 filas: todas las combinaciones $(t_0,h)$ con $t_0+h=\tau$ y $1\le h\le24$. Por lo tanto:

1. El target $y$ se repite en varias filas.
2. Las filas no son independientes: comparten el mismo $y$ y features muy correlacionadas.
3. El tamaño de muestra efectivo no es $10.227$ ni $8.217$: es mucho menor. En el fold final hay $25$ días de entrenamiento y, como máximo, $25\times24=600$ targets distintos. La correlación serial reduce aún más la información efectiva; el orden de magnitud es **decenas de días, no miles de filas**.

**Consecuencia matemática.** El error de entrenamiento es optimista: el modelo ve el mismo target desde varios orígenes y puede ajustar esos valores repetidos. La brecha train/test no es un defecto raro; es una consecuencia esperada del diseño de ventanas deslizantes. La sección 10 la cuantifica y la descompone.

### 4.6 Por qué 30 días de origen y no 47

La serie cubre 47 días calendario, pero solo 30 tienen orígenes válidos. Las razones:

- El primer día es parcial (la serie empieza a las 15:13) y no tiene `prev_day` para muchas horas.
- Los días sin comunicación no tienen $P_{t_0}$ y se descartan.
- Los últimos días no tienen 24 h de futuro.
- Algunos días tienen datos parciales y no alcanzan el umbral de 30 minutos por hora.

Esto no es un error de conteo: es la cobertura real del medidor.

---

## 5. Baselines

Los baselines no son decorativos: son el **piso** que el modelo debe superar. Si un modelo complejo no le gana a una regla simple, el modelo complejo no aporta valor.

### 5.1 Persistencia

$$
\hat y_{t_0+h}=P_{t_0}.
\qquad (5.1)
$$

Repite la última potencia observada. Es un baseline razonable a 1 h y malo a 24 h: la potencia de la medianoche no es la potencia de la tarde siguiente.

### 5.2 Seasonal naive

$$
\hat y_{t_0+h}=P_{t_0+h-24}.
\qquad (5.2)
$$

Repite la misma hora del día anterior. Captura el perfil diario y es el baseline estándar para series con estacionalidad diaria. El skill se define contra este modelo, no contra la persistencia.

### 5.3 Media global

$$
\hat y_{t_0+h}=\bar y_{\text{tr}} =
\frac{1}{|\mathcal{D}_{\text{tr}}|}
\sum_{(x,y)\in\mathcal{D}_{\text{tr}}}y.
\qquad (5.3)
$$

Es el baseline que se usa en la prueba de etiquetas barajadas: si el modelo no aprende nada, debe quedar cerca de este.

### 5.4 Climatología por hora y tipo de día

Se discretiza el calendario en $24\times2=48$ celdas:

$$
(h,w)\in\{0,\dots,23\}\times\{0,1\},
\qquad
w=\mathbf{1}\{\text{dow}\ge5\}.
\qquad (5.4)
$$

Para cada celda se estima la media condicional:

$$
\hat c_{h,w} =
\frac{
\displaystyle\sum_{i=1}^{N}
y_i\,\mathbf{1}\{h_i=h,\ w_i=w\}
}{
\displaystyle\sum_{i=1}^{N}
\mathbf{1}\{h_i=h,\ w_i=w\}
}.
\qquad (5.5)
$$

Si una celda no tiene datos, se usa $\bar y_{\text{tr}}$.

**Derivación como modelo.** Supóngase el modelo saturado

$$
y_i=c_{h_i,w_i}+\epsilon_i,
\qquad
\epsilon_i\sim\mathcal{N}(0,\sigma^2).
\qquad (5.6)
$$

La log-verosimilitud es

$$
\ell(c)=-\frac{N}{2}\log(2\pi\sigma^2)
-\frac{1}{2\sigma^2}
\sum_{i=1}^{N}\left(y_i-c_{h_i,w_i}\right)^2.
\qquad (5.7)
$$

Derivando respecto de $c_{h,w}$ e igualando a cero:

$$
\frac{\partial\ell}{\partial c_{h,w}} =
\frac{1}{\sigma^2}
\sum_{i:\ h_i=h,\ w_i=w}
\left(y_i-c_{h,w}\right)=0
\;\Longrightarrow\;
\hat c_{h,w}=\frac{1}{n_{h,w}}
\sum_{i:\ h_i=h,\ w_i=w}y_i.
\qquad (5.8)
$$

Es el estimador de máxima verosimilitud bajo el modelo de celda constante: una media por celda, $48$ parámetros.

**Naturaleza del modelo.** La climatología es **no paramétrica** en el sentido de que no impone una forma funcional sobre la hora: aprende una tabla. Es un modelo, pero es un **lookup**: no puede generalizar a combinaciones no vistas ni usar features continuas. Su fortaleza es que el perfil es estable; su debilidad es que no reacciona al nivel reciente ni a los festivos.

**Un matiz del estimador.** La suma de (5.5) recorre **filas**, no targets distintos. Como cada target aparece hasta 24 veces, la media está ponderada por el número de orígenes que alcanzan cada hora. En un dataset regular, esa ponderación es uniforme; con huecos, no. La diferencia es pequeña, pero conviene decirla: la climatología estimada es una media ponderada por cobertura, no la media simple de las horas distintas.

### 5.5 Resumen de baselines

| Baseline | Fórmula | Qué captura | Qué no captura |
|---|---|---|---|
| Persistencia | $P_{t_0}$ | Nivel actual | Perfil diario |
| Seasonal naive | $P_{t_0+h-24}$ | Perfil diario | Suavizado, nivel reciente |
| Media global | $\bar y$ | Nivel medio | Todo lo demás |
| Climatología | $\hat c_{h,w}$ | Perfil por hora y tipo de día | Nivel reciente, festivos, día específico |

---

## 6. Métricas

### 6.1 MAE

$$
\mathrm{MAE} =
\frac{1}{n}
\sum_{i=1}^{n}
\left|y_i-\hat y_i\right|.
\qquad (6.1)
$$

Está en kW, se interpreta directamente y es robusta a outliers. Su óptimo poblacional es la **mediana condicional**.

### 6.2 RMSE

$$
\mathrm{RMSE} =
\sqrt{
\frac{1}{n}
\sum_{i=1}^{n}
\left(y_i-\hat y_i\right)^2
}.
\qquad (6.2)
$$

También está en kW, pero penaliza los errores grandes al cuadrado. Su óptimo poblacional es la **media condicional**. Un solo día mal pronosticado puede dominar el RMSE; el MAE lo reparte.

### 6.3 Skill contra seasonal naive

$$
\mathrm{Skill} =
1-\frac{\mathrm{MAE}_{\text{modelo}}}{\mathrm{MAE}_{\text{naive}}}.
\qquad (6.3)
$$

- $\mathrm{Skill}=0$: el modelo empata con el naive.
- $\mathrm{Skill}>0$: el modelo es mejor.
- $\mathrm{Skill}<0$: el modelo es peor que repetir el día anterior.

En la tabla resumen, el skill reportado es la **mediana del skill por fold**, no el skill calculado con la mediana de los MAE:

$$
\widetilde{\mathrm{Skill}} =
\operatorname{median}_{k=1,\dots,5}
\left(
1-\frac{\mathrm{MAE}_{m,k}}{\mathrm{MAE}_{\text{naive},k}}
\right).
\qquad (6.4)
$$

Es una distinción sutil: la mediana de los cocientes no es el cociente de las medianas.

### 6.4 MAPE

$$
\mathrm{MAPE} =
\frac{100}{n}
\sum_{i=1}^{n}
\frac{\left|y_i-\hat y_i\right|}{\left|y_i\right|}.
\qquad (6.5)
$$

Es adimensional y fácil de comunicar, pero inestable cuando $y\approx0$. En este proyecto la carga mínima es $5{,}2$ kW, así que el denominador nunca es cero; aun así, el MAPE pondera más las horas de carga baja. Se reporta solo para la energía diaria, no para las horas.

### 6.5 R²

$$
R^2 =
1-\frac{\sum_i\left(y_i-\hat y_i\right)^2}
{\sum_i\left(y_i-\bar y_{\text{te}}\right)^2}.
\qquad (6.6)
$$

Mide la fracción de varianza de test explicada. Puede ser negativo si el modelo es peor que la media del test. Es útil para comparar modelos en la misma escala, pero no reemplaza al MAE: un modelo puede tener mejor MAE y peor $R^2$ si sus errores se concentran en los valores extremos.

### 6.6 Agregación entre folds

Para cada modelo se reportan:

$$
\text{mediana}_{k}\ \mathrm{MAE}_k,
\qquad
\text{media}_{k}\ \mathrm{MAE}_k,
\qquad
\min_k\ \mathrm{MAE}_k,
\qquad
\max_k\ \mathrm{MAE}_k.
\qquad (6.7)
$$

**Por qué la mediana.** Con 5 folds y un fold difícil, la media puede estar dominada por un solo valor. La mediana es más representativa del rendimiento típico. Pero la mediana **esconde el peor caso**; por eso se reportan también la media, el mínimo, el máximo y la tabla por fold.

**MAE pooled.** Como las filas de test de cada fold son disjuntas, el MAE sobre todas las filas de test es

$$
\mathrm{MAE}_{\text{pooled}} =
\frac{\sum_{k=1}^{5} n_k\,\mathrm{MAE}_k}
{\sum_{k=1}^{5} n_k}.
\qquad (6.8)
$$

Es la media ponderada por tamaño. En este proyecto el fold 5 tiene $2.010$ filas, el $21{,}9\,\%$ del total de test; la mediana le da el mismo peso que al fold 1, que tiene $1.338$. Ambas lecturas son válidas; la diferencia se muestra en la sección 9.

### 6.7 Métrica y funcional

| Pérdida de entrenamiento | Funcional que estima | Métrica natural |
|---|---|---|
| Cuadrática $L_2$ | Media condicional | RMSE |
| Absoluta $L_1$ | Mediana condicional | MAE |

El GBM se entrena con $L_2$, así que estima la media. La evaluación con MAE mide la cercanía a la mediana. En una distribución asimétrica como la de este bloque, no son lo mismo. Esta es la razón matemática por la que el MAE y el RMSE pueden ordenar distinto a dos modelos.

---

## 7. Protocolo de validación

### 7.1 Rolling origin con ventana expansiva

Los 30 días de origen se ordenan cronológicamente y se dividen en 6 bloques de 5 días:

$$
\mathcal{B}_1,\dots,\mathcal{B}_6,
\qquad
|\mathcal{B}_j|=5.
\qquad (7.1)
$$

Para el fold $k=1,\dots,5$:

$$
\mathcal{D}_{\text{tr}}^{(k)} =
\bigcup_{j=1}^{k}\mathcal{B}_j,
\qquad
\mathcal{D}_{\text{te}}^{(k)} =
\mathcal{B}_{k+1}.
\qquad (7.2)
$$

Es una **ventana expansiva**: el entrenamiento crece con cada fold y el test es siempre el bloque siguiente. No hay shuffle. El fold 5 entrena con 25 días y evalúa con los últimos 5; es el **holdout final**.

### 7.2 Particiones exactas

| Fold | Días train | Días test | Orígenes train | Orígenes test | Filas train | Filas test | % train | % test | Test |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 1 | 5 | 5 | 75 | 82 | 1.029 | 1.338 | 43,5 | 56,5 | 10-18 a 10-23 |
| 2 | 10 | 5 | 157 | 120 | 2.367 | 2.880 | 45,1 | 54,9 | 10-24 a 10-28 |
| 3 | 15 | 5 | 277 | 99 | 5.247 | 1.758 | 74,9 | 25,1 | 10-29 a 11-04 |
| 4 | 20 | 5 | 376 | 94 | 7.005 | 1.212 | 85,3 | 14,7 | 11-05 a 11-13 |
| 5 | 25 | 5 | 470 | 103 | 8.217 | 2.010 | 80,3 | 19,7 | 11-14 a 11-18 |

**Lectura.** El primer fold tiene más filas de test que de train. No es un error: el primer bloque de la serie tiene poca cobertura (empieza a las 15:13 y no tiene historia para `prev_day`), así que aporta pocas filas; el segundo bloque ya tiene un día completo de historia y aporta más. Los porcentajes son sobre las filas del fold (train + test), no sobre el dataset completo. No hay un 80/20 fijo: cada fold tiene su propio tamaño.

### 7.3 Qué garantiza el protocolo

1. **Ningún origen de test es anterior a un origen de train.** El entrenamiento siempre usa el pasado del bloque de test.
2. **Las features de un origen de test no se usan para entrenar.** La separación es por día de origen, no por fila.
3. **El orden temporal se respeta.** No hay shuffle, así que no se mezclan regímenes.

### 7.4 Qué **no** garantiza: solapamiento y purga

El protocolo separa por **origen**, no por **target**. Como las ventanas se solapan, un target del bloque de test puede haber aparecido como target de un origen de train del último día de entrenamiento. Ejemplo: si el último día de train es $E$ y el primero de test es $E+1$, un origen en $E$ a las 00:00 con $h=24$ tiene como target $E+1$ a las 00:00. Un origen en $E$ a las 23:00 con $h=24$ tiene como target $E+1$ a las 23:00. Es decir, **todo el primer día de test** puede aparecer como target en el train.

Esto no es fuga de features: las features siguen siendo pasadas. Es una **fuga de etiquetas** limitada al primer día del bloque de test. El efecto es un sesgo optimista leve en ese día. Un protocolo estricto aplicaría un **embargo** (purging): eliminar del train los orígenes de las últimas 24 h, o el último día completo, para que ninguna ventana de train cruce el inicio del test. En este proyecto no se aplicó. Se declara como limitación.

**La afirmación correcta es:** el modelo es out-of-sample **por origen**, no out-of-sample **por target**. No es lo mismo, y decirlo con precisión evita una crítica fácil.

### 7.5 Selección de hiperparámetros

Los hiperparámetros del modelo final se eligieron después de ver los resultados de los folds: se comparó el GBM original con el regularizado y se eligió el regularizado porque reducía la brecha train/test. Por lo tanto, el fold 5 **no es un holdout prístino**: se usó, junto con los demás, para seleccionar el modelo. La estimación de desempeño tiene un sesgo de selección.

Con 30 días no hay datos para un tercer split limpio. La alternativa correcta sería separar un periodo final antes de mirar nada y no usarlo para elegir hiperparámetros. No se hizo. Se declara.

---

## 8. Modelos

### 8.1 Ridge

Se estandarizan las features:

$$
z_j=\frac{x_j-\mu_j}{\sigma_j},
\qquad
\mu_j=\frac1n\sum_i x_{ij},
\quad
\sigma_j^2=\frac1n\sum_i\left(x_{ij}-\mu_j\right)^2.
\qquad (8.1)
$$

El objetivo es

$$
\hat\beta =
\arg\min_{\beta}
\left\{
\|y-X\beta\|_2^2 +
\alpha\|\beta\|_2^2
\right\},
\qquad
\alpha=1.
\qquad (8.2)
$$

Derivando respecto de $\beta$:

$$
\nabla_\beta =
-2X^T(y-X\beta)+2\alpha\beta=0
\;\Longrightarrow\;
\left(X^TX+\alpha I\right)\hat\beta=X^Ty,
\qquad (8.3)
$$

$$
\boxed{
\hat\beta =
\left(X^TX+\alpha I\right)^{-1}X^Ty
}.
\qquad (8.4)
$$

El intercepto no se penaliza (sklearn lo centra). La regularización encoge los coeficientes hacia cero; con features correlacionadas, reparte el peso entre ellas.

**Por qué falla en este problema.** La relación entre la hora y la carga no es lineal: es una rampa, una meseta y un descenso. Un modelo lineal con `target_hour` como número impone una recta; los términos de Fourier de 3 armónicos pueden aproximar la forma, pero no la meseta. Además, las features están muy correlacionadas (`P_origin`, `lag1`, `roll3`, `roll24`), y Ridge reparte el peso entre todas, lo que diluye la señal. El resultado es un MAE de $0{,}800$ kW, muy por encima de la climatología ($0{,}298$).

### 8.2 Ridge con hora one-hot

Se reemplazan las features categóricas por dummies:

$$
X=
\left[
X_{\text{num}},
\ \mathbf{1}\{\text{hora}=0\},\dots,\mathbf{1}\{\text{hora}=23\},
\ \mathbf{1}\{\text{dow}=0\},\dots,\mathbf{1}\{\text{dow}=6\}
\right].
\qquad (8.5)
$$

Hay $22$ features numéricas, $24$ dummies de hora y $7$ de día: $53$ columnas más intercepto. El modelo sigue siendo lineal en los parámetros, pero ahora puede ajustar un nivel distinto por hora. Mejora a $0{,}774$ kW, pero sigue lejos: no hay interacciones entre la hora y el nivel reciente, y la regularización encoge las dummies.

**Lección.** Pasar de una hora numérica a one-hot es una mejora de especificación, pero no convierte un modelo lineal en un modelo de perfil. La climatología, que es una tabla, le gana porque su forma funcional es la correcta para un perfil horario.

### 8.3 GBM directo

El GBM construye un modelo aditivo de árboles:

$$
F_M(x)=F_0+\nu\sum_{m=1}^{M}h_m(x),
\qquad (8.6)
$$

donde $F_0$ es la predicción inicial (la media del target), $h_m$ son árboles de regresión y $\nu$ es la tasa de aprendizaje.

Con pérdida cuadrática,

$$
L(y,F)=\frac12(y-F)^2,
\qquad
-\frac{\partial L}{\partial F}=y-F,
\qquad (8.7)
$$

el pseudo-residuo en la iteración $m$ es

$$
r_i^{(m)}=y_i-F_{m-1}(x_i).
\qquad (8.8)
$$

Se ajusta un árbol a $r^{(m)}$. Para una hoja $R_{jm}$, el valor óptimo con penalización $L_2$ es

$$
\gamma_{jm} =
\arg\min_{\gamma}
\left\{
\sum_{i\in R_{jm}}\left(r_i^{(m)}-\gamma\right)^2 +
\lambda\gamma^2
\right\} =
\frac{\sum_{i\in R_{jm}}r_i^{(m)}}{n_{jm}+\lambda}.
\qquad (8.9)
$$

La actualización es

$$
F_m(x)=F_{m-1}(x)+\nu\,\gamma_{jm},
\qquad
x\in R_{jm}.
\qquad (8.10)
$$

**Hiperparámetros del GBM directo.** `max_depth=4` (hasta $2^4=16$ hojas por árbol), `max_iter=500`, `learning_rate=0.05`, `l2_regularization=1`, `min_samples_leaf=15`. Capacidad máxima: $500\times16=8.000$ hojas. Con $1.029$ filas en el fold 1, eso es más hojas que filas: sobreajuste garantizado. En el fold 1 el $R^2$ es $-0{,}4255$, peor que predecir la media.

**Por qué el GBM directo no le gana a la climatología.** Tiene que aprender el perfil desde cero con muy pocos días. La climatología le da el perfil gratis; el GBM, sin ese prior, gasta capacidad en reconstruir la forma diaria y le queda poca para la desviación. En la mediana, el GBM directo queda en $0{,}307$ kW, ligeramente peor que la climatología ($0{,}298$).

### 8.4 Híbrido: climatología + GBM del residuo

#### 8.4.1 Definición

$$
\hat y_{t_0+h} =
\hat c_{h,w} +
\hat g\left(x_{t_0,h}\right),
\qquad (8.11)
$$

donde

$$
r=y-\hat c_{h,w}
\qquad (8.12)
$$

es el residuo. El GBM se entrena sobre $r$, no sobre $y$:

$$
\hat g =
\arg\min_{g\in\mathcal{G}}
\sum_{(x,y)\in\mathcal{D}_{\text{tr}}}
\left(
y-\hat c_{h,w}-g(x)
\right)^2 +
\lambda\,\Omega(g).
\qquad (8.13)
$$

#### 8.4.2 Equivalencia con un GBM con offset

Un GBM con predicción inicial $F_0(x)=\hat c_{h,w}$ y $M$ iteraciones ajusta

$$
F_M(x) =
\hat c_{h,w} +
\nu\sum_{m=1}^{M}h_m(x),
\qquad (8.14)
$$

donde los árboles se ajustan a los residuos $y-F_{m-1}$. El híbrido es exactamente eso: un GBM con un **offset no constante** igual a la climatología. La diferencia con el GBM directo es que el offset no se aprende: se impone como prior.

#### 8.4.3 Identidad del error

$$
y-\hat y =
\left(y-\hat c\right)-\hat g =
r-\hat g.
\qquad (8.15)
$$

El error del híbrido es el error del GBM sobre el residuo. Si $\hat g=0$, el error es el residuo de la climatología; si $\hat c=0$, el error es el del GBM directo. El híbrido **anida** a los dos.

#### 8.4.4 Descomposición sesgo-varianza

Para un punto de test $x$,

$$
\mathbb{E}\left[\left(y-\hat f(x)\right)^2\right] =
\sigma^2 +
\left(\mathbb{E}[\hat f(x)]-f^*(x)\right)^2 +
\operatorname{Var}\left(\hat f(x)\right),
\qquad (8.16)
$$

donde $\sigma^2$ es el ruido irreducible, $f^*$ es la media condicional verdadera, y los otros dos términos son el sesgo y la varianza del estimador.

- La **climatología** tiene alta bias (no usa el nivel reciente ni el día específico) y baja varianza (48 medias sobre muchos datos).
- El **GBM** tiene baja bias (puede ajustar interacciones) y alta varianza (muchos parámetros, pocos días).
- El **híbrido** suma un estimador de baja varianza con una corrección de alta flexibilidad. Si la corrección reduce la bias más de lo que agrega varianza, el MSE baja.

La identidad (8.15) permite verlo de otra forma:

$$
\operatorname{Var}(y) =
\operatorname{Var}(\hat c) +
\operatorname{Var}(r) +
2\operatorname{Cov}(\hat c,r).
\qquad (8.17)
$$

La climatología absorbe la parte de la varianza explicada por el calendario; el residuo $r$ tiene una varianza mucho menor que $y$. El GBM no tiene que aprender el perfil: solo la desviación. Ese es el argumento matemático de por qué el híbrido funciona.

#### 8.4.5 Caso límite y modo de falla

- Si $\hat g=0$, el híbrido es la climatología.
- Si $\hat c=0$, el híbrido es el GBM directo.
- Si el régimen cambia (por ejemplo, un festivo no modelado), la climatología predice el perfil laboral y el GBM agrega una corrección aprendida de días laborales. Las dos componentes empujan en la misma dirección equivocada. El error es estructural, no ruido.

Ese último caso es exactamente lo que ocurre el 16-11-2026 (sección 11.3).

#### 8.4.6 Hiperparámetros del residuo

| Parámetro | Valor | Efecto |
|---|---:|---|
| `max_depth` | 3 | Hasta 8 hojas por árbol |
| `max_iter` | 150 | 150 árboles |
| `learning_rate` | 0,03 | Encogimiento por árbol |
| `l2_regularization` | 10 | Encoge el valor de cada hoja |
| `min_samples_leaf` | 30 | Evita hojas con pocas filas |
| Capacidad máxima | $150\times8=1.200$ hojas | $\approx15\,\%$ del GBM directo |

La regularización es deliberada: con 25 días, un modelo más flexible reduce el error de train pero agranda la brecha. La sección 10 muestra el intercambio.

---

## 9. Modelo final y resultados

### 9.1 Modelo final

$$
\boxed{
\hat y_{t_0+h} =
\hat c_{h,w} +
\hat g_{\text{GBM}}\left(x_{t_0,h}\right)
}
\qquad (9.1)
$$

con:

- $\hat c_{h,w}$: climatología por hora y tipo de día, estimada con (5.5).
- $\hat g_{\text{GBM}}$: GBM de residuos con `max_depth=3`, `max_iter=150`, `learning_rate=0.03`, `l2_regularization=10`, `min_samples_leaf=30`.
- Entrenamiento: 25 días (todo menos los últimos 5).
- Test: últimos 5 días.

### 9.2 Métricas del modelo final

| Métrica | Valor |
|---|---:|
| MAE train | $0{,}1500$ kW |
| MAE test | $0{,}6431$ kW |
| Brecha train/test | $0{,}4931$ kW |
| RMSE test | $1{,}3394$ kW |
| R² test | $0{,}2335$ |

**Lectura inmediata.** El modelo ajusta el train mucho mejor que el test. La brecha es $0{,}493$ kW, el $77\,\%$ del MAE de test. Esto es lo que hay que explicar, no esconder. La sección 10 lo descompone: $87{,}5\,\%$ de esa brecha se explica por un solo día, el 16-11.

### 9.3 MAE por fold

| Fold | Naive | Climatología | GBM | Híbrido | Ridge OH | Ridge | Persistencia |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1,072 | 0,404 | 1,045 | **0,392** | 0,877 | 0,993 | 1,469 |
| 2 | 0,699 | 0,298 | 0,272 | 0,274 | 0,774 | 0,800 | 1,434 |
| 3 | 0,643 | 0,280 | 0,258 | **0,220** | 0,368 | 0,400 | 1,370 |
| 4 | 0,927 | 0,284 | 0,307 | **0,259** | 0,684 | 0,652 | 0,688 |
| 5 | 0,834 | **0,632** | 0,825 | 0,643 | 0,950 | 0,935 | 0,704 |

**Observaciones:**

- El híbrido gana en los folds 1 a 4. En el fold 5 pierde por $0{,}011$ kW contra la climatología.
- El GBM directo falla claramente en el fold 1 ($1{,}045$ kW) por falta de datos; con 25 días mejora, pero nunca domina.
- Ridge y Ridge one-hot quedan por detrás de la climatología y del híbrido en todos los folds. La forma funcional lineal no es la adecuada.
- La persistencia es peor que el naive en los folds 1–3 y mejor en los folds 4–5; aun así, su mediana ($1{,}370$) es mucho peor. El naive es el baseline correcto.

### 9.4 Resumen entre folds

| Modelo | MAE mediana | MAE media | MAE pooled | RMSE mediana | Skill mediana |
|---|---:|---:|---:|---:|---:|
| **Híbrido** | **0,274** | **0,358** | **0,360** | **0,454** | **0,634** |
| Climatología | 0,298 | 0,380 | 0,381 | 0,477 | 0,574 |
| GBM | 0,307 | 0,541 | 0,507 | 0,474 | 0,600 |
| Ridge one-hot | 0,774 | 0,731 | 0,738 | 1,016 | 0,182 |
| Ridge | 0,800 | 0,756 | 0,762 | 1,045 | 0,074 |
| Seasonal naive | 0,834 | 0,835 | 0,802 | 1,541 | 0,000 |
| Persistencia | 1,370 | 1,133 | 1,169 | 1,918 | −0,370 |

**La mediana no es el peor caso.** El MAE mediano del híbrido es $0{,}274$, pero su MAE medio es $0{,}358$ y su peor fold es $0{,}643$. El MAE pooled ($0{,}360$) pondera el fold 5 por tamaño y se parece más a la media que a la mediana. Las tres cifras son correctas; describen cosas distintas.

### 9.5 R² por fold

| Fold | Climatología | GBM | Híbrido |
|---:|---:|---:|---:|
| 1 | 0,8285 | −0,4255 | **0,8339** |
| 2 | 0,9335 | 0,9358 | **0,9420** |
| 3 | 0,8750 | 0,9040 | **0,9362** |
| 4 | 0,7934 | 0,7963 | **0,8131** |
| 5 | **0,2979** | 0,0378 | 0,2335 |

En el fold 5 el híbrido tiene **peor** $R^2$ que la climatología ($0{,}2335$ vs $0{,}2979$), aunque su MAE sea solo $0{,}011$ kW peor. ¿Por qué? Porque el $R^2$ castiga al cuadrado los errores grandes y el fold 5 contiene el festivo. El MAE los reparte. Es la misma historia que la diferencia MAE/RMSE, aplicada a la comparación entre modelos.

### 9.6 Comparación con el GBM original

| Modelo de residuo | MAE train | MAE test | Brecha |
|---|---:|---:|---:|
| GBM original (`depth=4`, 400 árboles, $\lambda=1$) | 0,063 | **0,628** | 0,564 |
| **GBM regularizado (final)** | **0,150** | 0,643 | **0,493** |
| Ridge | 0,241 | 0,686 | 0,445 |

El GBM original tiene un MAE de test $0{,}015$ kW mejor ($2{,}4\,\%$), pero una brecha $0{,}071$ kW mayor ($14{,}5\,\%$ más grande que la del regularizado). Se eligió el regularizado porque el objetivo del proyecto incluye demostrar que el modelo no memoriza; la diferencia de test está dentro del ruido de un fold con un festivo. Es un intercambio explícito de bias por varianza, no un resultado gratis.

### 9.7 Significancia estadística: lo que no se puede afirmar

Las diferencias de MAE por fold entre híbrido y climatología son:

$$
d_k=\mathrm{MAE}^{\text{hib}}_k-\mathrm{MAE}^{\text{clim}}_k =
(-0{,}0118,\ -0{,}0242,\ -0{,}0599,\ -0{,}0243,\ +0{,}0110).
$$

$$
\bar d=-0{,}0219,
\qquad
s_d=0{,}0257,
\qquad
t=\frac{\bar d}{s_d/\sqrt{5}}=-1{,}905,
\qquad
p\approx0{,}13.
\qquad (9.2)
$$

Con 5 folds, la ventaja del híbrido **no es estadísticamente significativa** al $5\,\%$. Es consistente en 4 de 5 folds, pero el fold 5 y la variabilidad entre folds impiden afirmar que la diferencia no es azar. Un test a nivel de fila daría un $p$ minúsculo, pero sería inválido: las filas están solapadas y no son independientes. La conclusión honesta es: **el híbrido es la mejor opción descriptiva, con una ventaja pequeña y no significativa con esta muestra**.

---

## 10. Generalización: ¿memoriza o aprende?

### 10.1 Brecha train/test

$$
\mathrm{Gap} =
\mathrm{MAE}_{\text{test}}-\mathrm{MAE}_{\text{train}}.
\qquad (10.1)
$$

Para el modelo final:

$$
\mathrm{Gap}=0{,}6431-0{,}1500=0{,}4931\ \text{kW}.
\qquad (10.2)
$$

Una brecha positiva es esperable: el modelo se ajusta a las filas de train y no a las de test. La pregunta es si la brecha es **sobreajuste** o **cambio de régimen**. La descomposición por día responde.

**Descomposición.** En el fold 5, si se excluyen las filas cuyo target es el 16-11:

$$
\mathrm{MAE}_{\text{test}}^{\text{sin 16-11}}=0{,}2116,
\qquad
\mathrm{Gap}^{\text{sin 16-11}}=0{,}2116-0{,}1500=0{,}0615.
\qquad (10.3)
$$

La parte de la brecha atribuible al 16-11 es

$$
\frac{0{,}4931-0{,}0615}{0{,}4931}=87{,}5\,\%.
\qquad (10.4)
$$

**Conclusión.** El $87{,}5\,\%$ de la brecha no es memorización: es un día con un régimen distinto. En el régimen normal, la brecha es $0{,}062$ kW, el $29\,\%$ del MAE test sin festivo. Sigue siendo una brecha, pero es la brecha esperable de un modelo con filas solapadas, no la de un memorizador.

### 10.2 Prueba de etiquetas barajadas

**Hipótesis nula $H_0$:** $y$ es independiente de $x$. Si el pipeline no puede aprender una relación real, debe quedar al nivel de la media.

**Procedimiento.**

1. Se permutan las etiquetas $y$ del train, manteniendo $x$ fijo:
   $y_i^{\pi}=y_{\pi(i)}$, con $\pi$ una permutación aleatoria.
2. Se reentrena **todo** el pipeline: climatología + GBM del residuo.
3. Se evalúa en el test original.
4. Se repite con 5 semillas.

**Resultado.**

| Cantidad | Valor |
|---|---:|
| MAE test medio con etiquetas barajadas | $1{,}2737$ |
| Rango | $[1{,}2588,\ 1{,}2861]$ |
| MAE de la media global | $1{,}2710$ |

El modelo barajado queda **prácticamente al nivel de la media** (1,2737 vs 1,2710, una diferencia del $0{,}2\,\%$). No hay señal residual: si el pipeline tuviera una fuga o memorizara la identidad de las filas, el test barajado seguiría siendo mejor que la media. No lo es.

**Qué prueba y qué no.** Prueba que el pipeline no extrae señal del ruido y que no hay una fuga obvia. **No** prueba que el modelo no esté sobreajustado en el régimen normal; para eso están la brecha y la curva de aprendizaje.

### 10.3 Curva de aprendizaje

Se entrena el mismo modelo con $n=5,10,15,20,25$ días y se evalúa siempre en el mismo test (los últimos 5 días):

| Días train | Filas train | MAE train | MAE test |
|---:|---:|---:|---:|
| 5 | 1.029 | 0,020 | 0,784 |
| 10 | 2.367 | 0,045 | 0,718 |
| 15 | 5.247 | 0,110 | **0,631** |
| 20 | 7.005 | 0,129 | 0,635 |
| 25 | 8.217 | 0,150 | 0,643 |

**Lectura.**

- El test mejora de $0{,}784$ a $0{,}631$ entre 5 y 15 días: el modelo **usa** los datos adicionales. Si memorizara, más datos no ayudarían.
- Entre 15 y 25 días el test se estanca y empeora levemente ($0{,}631\to0{,}643$). La diferencia es pequeña y no monotónica; el test contiene el festivo y días de cobertura irregular, y el modelo con más días no mejora en ese régimen. Con cinco puntos no se puede atribuir a una causa única.
- El train sube de $0{,}020$ a $0{,}150$: al crecer el dataset, el modelo no puede ajustar cada fila y la brecha se reduce en términos relativos. Es la señal de que la regularización funciona.

**Conclusión.** La curva es la evidencia más limpia de aprendizaje: el test mejora con datos. El estancamiento final es compatible con el cambio de régimen y la cobertura irregular; no hay evidencia de memorización.

**¿Por qué el modelo final usa 25 días y no 15?** Porque el criterio de diseño es usar toda la historia disponible y reducir la brecha train/test, no minimizar el test de un fold. La diferencia de $0{,}012$ kW entre 15 y 25 días está dentro del ruido de un solo test; elegir 15 días por ese resultado sería una forma de sobreajustar la selección al fold.

### 10.4 Ablación de features

Se quita un grupo de features y se reentrena el híbrido en el fold 5:

| Configuración | MAE test |
|---|---:|
| Completo | 0,6431 |
| Sin `prev_day` | 0,6383 |
| Sin `prev_day` y `prev_week` | 0,6521 |
| Sin lags (`lag1`, `lag24`, `lag168`) | 0,6439 |
| Sin calendario (hora, dow, weekend, Fourier) | 0,6347 |

**Lectura honesta.** La ablación es **mixta**: quitar `prev_day` o el calendario mejora levemente; quitar `prev_day` y `prev_week` empeora. ¿Por qué?

1. **Redundancia.** `prev_day`, `lag24`, `roll24` y `P_origin` contienen información muy parecida. Quitar una no elimina la información; las otras la compensan.
2. **El calendario ya está en la climatología.** El GBM del residuo no necesita reaprender la hora; la climatología ya la captura. Quitar el calendario del GBM casi no cambia nada.
3. **Un solo fold.** La ablación se hace en el fold 5, el del festivo. El ruido de un día domina las diferencias de $0{,}005$–$0{,}010$ kW.
4. **Features correlacionadas.** La importancia por permutación también muestra valores pequeños y algunos negativos: en un modelo con features redundantes, barajar una sola no mide su importancia causal.

**Conclusión.** La ablación **no es la evidencia fuerte** de que el modelo aprende. La evidencia fuerte es el shuffle (cae a la media) y la curva (mejora con datos). La ablación solo muestra que las features son redundantes y que el fold es ruidoso. Decirlo así es más honesto que presentar la ablación como una prueba contundente.

### 10.5 Capacidad y conteo de parámetros

| Modelo | Parámetros | Filas train (fold 5) | Filas por parámetro |
|---|---:|---:|---:|
| Media global | 1 | 8.217 | 8.217 |
| Climatología | 48 | 8.217 | 171 |
| Ridge | 25 | 8.217 | 329 |
| Ridge one-hot | 54 | 8.217 | 152 |
| GBM directo | $\le 8.000$ hojas | 8.217 | $\approx1$ |
| Híbrido | 48 + hasta 1.200 | 8.217 | $\approx6{,}6$ |

**Lectura.** El GBM directo tiene capacidad para una hoja por fila: su complejidad alcanza para memorizar. El híbrido tiene $1.248$ parámetros como máximo, pero muchos árboles usan menos hojas y la penalización $L_2$ encoge los valores. Aun así, la relación filas/parámetro es baja ($6{,}6$). La regularización no es opcional: es lo que evita que el híbrido se comporte como el GBM directo.

**El tamaño efectivo no son las filas.** Con 25 días y ventanas solapadas, el número de targets distintos es a lo sumo $25\times24=600$, y están correlacionados. La relación real es todavía más desfavorable que $6{,}6$ filas por parámetro. Por eso la brecha existe y por eso se reporta.

### 10.6 Qué prueba cada test

| Prueba | Qué prueba | Qué no prueba |
|---|---|---|
| Brecha train/test | El modelo ajusta mejor el train que el test | Que la brecha sea solo sobreajuste (puede ser cambio de régimen) |
| Etiquetas barajadas | No hay señal en el ruido ni fuga obvia | Que el modelo generalice en el régimen normal |
| Curva de aprendizaje | Más datos mejoran el test | Que el modelo sea óptimo |
| Ablación | El modelo usa (o no) un grupo de features | Causalidad; con features redundantes es débil |
| Conteo de parámetros | La capacidad es alta o baja | El sobreajuste efectivo (depende de la regularización) |
| Holdout 11-17 | El pronóstico funciona en un día fuera de muestra | Que funcione en todos los días |
| Caso 11-16 | El modelo falla por un covariado faltante, no por ruido | Que el modelo sea malo en el régimen normal |

**La conclusión conjunta.** El modelo no memoriza el ruido (shuffle), aprende con datos (curva), y su peor error es explicable por un festivo no modelado (descomposición). La brecha existe y se reporta; no se esconde.

---

## 11. Análisis de errores

### 11.1 Error por horizonte

| Horizonte | Naive | Climatología | GBM | Híbrido |
|---:|---:|---:|---:|---:|
| 1 h | 0,795 | 0,353 | 0,465 | **0,330** |
| 6 h | 0,797 | 0,372 | 0,462 | **0,346** |
| 12 h | 0,802 | 0,384 | 0,503 | **0,361** |
| 18 h | 0,801 | 0,390 | 0,550 | **0,372** |
| 24 h | 0,810 | 0,397 | 0,555 | **0,379** |

El error del híbrido crece de $0{,}330$ a $0{,}379$ kW entre 1 h y 24 h: un $15\,\%$. El del GBM directo crece de $0{,}465$ a $0{,}555$: un $19\,\%$. La climatología crece de $0{,}353$ a $0{,}397$: un $12\,\%$. El híbrido gana en **todos** los horizontes, no solo en el corto plazo. La razón es que la climatología aporta la forma y el GBM corrige el nivel; el error adicional por horizonte es la incertidumbre creciente de la corrección, no una acumulación recursiva (el método es directo).

**Por qué el error no explota a 24 h.** En un método recursivo, el error se compondría. En el método directo, cada horizonte se predice con features conocidas en $t_0$; lo que crece es la dificultad de la corrección, no el error acumulado. La forma suave del perfil hace el resto.

### 11.2 Error de energía diaria

Para cada día con origen a medianoche y al menos 20 horas observadas:

$$
E_d=\sum_{h\in\mathcal{H}_d}P_{t_0+h},
\qquad
\hat E_d=\sum_{h\in\mathcal{H}_d}\hat P_{t_0+h},
\qquad
\Delta_d=\hat E_d-E_d,
\qquad (11.1)
$$

donde $\mathcal{H}_d$ es el conjunto de horas con dato real. **La suma se hace sobre el mismo soporte**: no se comparan 24 horas pronosticadas contra 21 horas reales. Si se comparara el total de 24 h del pronóstico contra el total de 21 h reales, se atribuiría al modelo la energía de las 3 horas faltantes.

| Modelo | Error absoluto mediano | Error absoluto medio | MAPE mediano |
|---|---:|---:|---:|
| **Híbrido** | **3,6 kWh/día** | 6,1 kWh/día | **2,2 %** |
| Climatología | 4,5 kWh/día | 7,6 kWh/día | 3,0 % |

La energía diaria real media de los 13 días es $150{,}1$ kWh. El error mediano del híbrido es $3{,}6$ kWh, el $2{,}4\,\%$ de la energía media; el MAPE mediano es $2{,}2\,\%$.

**Por qué el error diario no es $\sqrt{24}$ veces el error horario.** Si los errores horarios fueran independientes,

$$
\operatorname{Var}\left(\sum_{h=1}^{24}\varepsilon_h\right) =
\sum_{h=1}^{24}\operatorname{Var}(\varepsilon_h)
\approx24\,\sigma_\varepsilon^2,
\qquad (11.2)
$$

y el error diario típico sería $\sqrt{24}\approx4{,}9$ veces el horario. Con un MAE horario típico de $\approx0{,}3$ kW, eso daría $\approx1{,}5$ kWh/día. El valor observado ($3{,}6$ kWh mediano) es mayor: los errores horarios están **positivamente correlacionados**. Tiene sentido: si el modelo se equivoca en el nivel del día (por ejemplo, un festivo), se equivoca en la misma dirección durante muchas horas. La covarianza es la que manda:

$$
\operatorname{Var}\left(\sum_h\varepsilon_h\right) =
\sum_h\operatorname{Var}(\varepsilon_h) +
2\sum_{h<h'}\operatorname{Cov}(\varepsilon_h,\varepsilon_{h'}).
\qquad (11.3)
$$

**Consecuencia práctica.** El error de energía diaria es más pequeño que sumar errores absolutos, pero más grande que si los errores fueran independientes. El pronóstico diario es útil, pero no es la suma de 24 pronósticos independientes.

### 11.3 Caso 11-16: el festivo que el modelo no sabía

El lunes 16 de noviembre de 2026 fue **festivo nacional en Colombia**: la Independencia de Cartagena, trasladada al lunes por la Ley 51 de 1983 (Ley Emiliani). No hubo clases en colegios ni en la mayoría de universidades; la actividad académica se retomó el martes 17.

La evidencia en los datos es concluyente:

| Día | Energía (kWh) | Perfil |
|---|---:|---|
| Domingo 15-11 | 129,7 | plano, base |
| **Lunes 16-11** | **131,3** | plano, $5{,}3$–$5{,}8$ kW |
| Media de fines de semana | 131,4 | plano, base |
| Martes 17-11 | 161,4 (21 h) | perfil laboral |

El 16-11 consumió **como un domingo**, no como un lunes. Su máximo horario fue $5{,}82$ kW a las 11:00; un lunes laboral típico tiene $9$–$10$ kW a esa hora. La carga de ocupación estuvo ausente; solo quedó la base.

El pronóstico para ese día:

| Cantidad | Valor |
|---|---:|
| Real | 131,3 kWh |
| Pronóstico híbrido | 172,7 kWh |
| Pronóstico climatología | 169,9 kWh |
| Error híbrido | $+41{,}4$ kWh ($+31{,}6\,\%$) |
| Error climatología | $+38{,}6$ kWh ($+29{,}4\,\%$) |

**Descomposición.** Sepárese la carga en base y ocupación:

$$
P_t=b_t+o_t,
\qquad
b_t\approx5{,}4\ \text{kW},
\qquad
o_t\ge0.
\qquad (11.4)
$$

La base se pronostica bien: a las 03:00 el real es $5{,}38$ y el modelo predice $\approx5{,}4$. La ocupación es la que falta: a las 10:00 el real es $5{,}60$ y el modelo predice $\approx10{,}1$. El error es, esencialmente, la ocupación que no ocurrió.

**Por qué es un problema de covariado, no de memorización.** El modelo aprendió la regla “lunes ⇒ perfil laboral”. La aplicó correctamente a un lunes que no fue laboral. No memorizó el 16-11 (no lo vio en train); generalizó una regla que es cierta en el régimen normal y falsa en el festivo. La variable que falta es

$$
\text{feriado}_t\in\{0,1\},
\qquad (11.5)
$$

o, más general, una variable latente de ocupación académica. Sin ella, ningún modelo puede distinguir un lunes festivo de un lunes normal.

**Lectura correcta.** El 16-11 no es “el modelo falló porque memoriza”; es “el modelo aplicó una regla válida a un día fuera de la distribución de entrenamiento”. Es un caso de **cambio de régimen**, y es la razón por la que el fold 5 castiga al híbrido.

### 11.4 Fold 5 sin el festivo

| Conjunto | Filas | MAE híbrido | MAE climatología | R² híbrido | R² climatología |
|---|---:|---:|---:|---:|---:|
| Fold 5 completo | 2.010 | 0,6431 | **0,6322** | 0,2335 | **0,2979** |
| Fold 5 sin 16-11 | 1.434 | **0,2116** | 0,2383 | **0,9613** | 0,9411 |

**La inversión del ranking se explica por un solo día.** Sin el festivo, el híbrido le gana a la climatología por $0{,}027$ kW ($11{,}2\,\%$) y su $R^2$ sube a $0{,}9613$. Con el festivo, la climatología gana por $0{,}011$ kW. (El 11-14 es el primer día de test y puede estar levemente beneficiado por el solapamiento descrito en 7.4; la conclusión sobre el 16-11 no depende de ese día.) El fold 5 no dice “el híbrido no generaliza”; dice “el híbrido no sabe que el 16-11 fue festivo”.

### 11.5 Error por día en el fold 5

| Día objetivo | Filas | MAE híbrido | MAE climatología | Sesgo híbrido |
|---|---:|---:|---:|---:|
| 14-11 (sábado) | 231 | 0,098 | **0,084** | +0,073 |
| 15-11 (domingo) | 576 | 0,143 | **0,127** | −0,027 |
| **16-11 (festivo)** | 576 | 1,718 | **1,613** | **+1,718** |
| 17-11 (martes) | 504 | **0,315** | 0,416 | −0,254 |
| 18-11 (miércoles) | 123 | **0,321** | 0,326 | +0,008 |

El sesgo del 16-11 ($+1{,}718$ kW) es positivo y enorme: el modelo sobrestima todo el día. En el 17-11 el sesgo es negativo ($-0{,}254$): el modelo subestima un día de carga alta. Los dos errores se cancelan parcialmente en el agregado, pero no en el MAE.

### 11.6 Regla de anomalía

Con los errores diarios $\Delta_d$ de los 13 días:

$$
\operatorname{median}(\Delta)=-0{,}5,
\qquad
\operatorname{MAD}=3{,}2,
\qquad
\hat\sigma=1{,}4826\times3{,}2=4{,}74.
\qquad (11.6)
$$

El puntaje robusto es

$$
z_d=\frac{\Delta_d-\operatorname{median}(\Delta)}{\hat\sigma}.
\qquad (11.7)
$$

| Día | $\Delta$ (kWh) | $z$ |
|---|---:|---:|
| 16-11 | +41,4 | **+8,83** |
| 19-10 | −10,2 | −2,04 |
| 17-11 | −5,5 | −1,05 |
| 15-11 | −0,7 | −0,04 |

Con un umbral $|z|>3$, solo el 16-11 se marca como anomalía. El umbral corresponde a $| \Delta | > 13{,}7$ kWh. Es una regla **ilustrativa**: se calibró con 13 días y un solo evento; en producción habría que estimarla con más historia. Pero muestra cómo el pronóstico se convierte en una herramienta de detección: no se trata de que el modelo “acierte” el festivo, sino de que **avise** que el día se desvió.

---

## 12. Función de pronóstico

### 12.1 Definición

La función implementada en `forecast.py` es

$$
\texttt{forecast\_day}(\text{historia},\text{bundle})
\;\longrightarrow\;
\left\{
\hat P_{t_0+1},\dots,\hat P_{t_0+24}
\right\}.
\qquad (12.1)
$$

Recibe:

- `historia`: serie horaria de potencia hasta el origen, con posibles huecos.
- `bundle`: diccionario con `features`, `clim`, `fallback` y `gbm_res`.

Devuelve un `DataFrame` con 24 filas: `target`, `P_hat`, `P_clim`, `resid_hat`, `hora`.

### 12.2 Construcción de features en producción

El origen es el último timestamp **válido** de la historia:

$$
t_0=\max\{t:\ P_t\ \text{observado}\}.
\qquad (12.2)
$$

Se reconstruye la grilla horaria completa entre el mínimo y el máximo de la historia:

$$
\mathcal{G}=\{t_{\min},t_{\min}+1\text{ h},\dots,t_{\max}\}.
\qquad (12.3)
$$

Los rezagos se calculan sobre $\mathcal{G}$, no sobre las filas válidas. Esto es importante: si se calcularan por posición, un hueco de 3 horas haría que `lag1` fuera en realidad un lag de 4 h. La grilla garantiza que `lag1` sea $t_0-1$ h, `lag24` sea $t_0-24$ h y `lag168` sea $t_0-168$ h.

Para cada $k=1,\dots,24$, el target es

$$
\tau_k=t_0+k.
\qquad (12.4)
$$

Las features se construyen con las mismas fórmulas de la sección 4.3. El modelo no reentrena: usa el `bundle` guardado.

### 12.3 Predicción

$$
\hat P_{\tau_k} =
\hat c_{h_k,w_k} +
\hat g\left(x_{t_0,k}\right),
\qquad
h_k=\text{hora}(\tau_k),
\quad
w_k=\mathbf{1}\{\text{dow}(\tau_k)\ge5\}.
\qquad (12.5)
$$

Si la celda $(h_k,w_k)$ no existe en la climatología, se usa `fallback`:

$$
\hat c_{h,w}=\bar y_{\text{tr}}.
\qquad (12.6)
$$

### 12.4 Energía, pico y anomalía

$$
\hat E=\sum_{k=1}^{24}\hat P_{\tau_k}
\qquad
(\text{kWh, porque } \Delta t=1\text{ h}),
\qquad (12.7)
$$

$$
\hat P_{\max}=\max_{k}\hat P_{\tau_k},
\qquad
k^*=\arg\max_k\hat P_{\tau_k}.
\qquad (12.8)
$$

La anomalía se evalúa cuando llega el día real, comparando la energía observada con la pronosticada en el mismo soporte:

$$
z=\frac{\hat E-E-\operatorname{median}(\Delta)}{\hat\sigma},
\qquad
\text{alerta si }|z|>3.
\qquad (12.9)
$$

**Advertencia sobre el pico.** El máximo de la media condicional no es la media del máximo:

$$
\max_k \mathbb{E}[P_{\tau_k}]
\ne
\mathbb{E}\left[\max_k P_{\tau_k}\right].
\qquad (12.10)
$$

El pronóstico puntual suaviza los extremos. Si el objetivo fuera el pico, habría que usar un cuantil alto (por ejemplo, $q_{0.9}$) o un modelo específico de picos. Este proyecto pronostica la **curva media** y la energía; el pico se reporta como referencia, no como garantía.

### 12.5 Ejemplo: 17-11-2026

Historia hasta el 16-11 a las 23:00. Modelo entrenado hasta el 13-11 (no vio el 14-18).

| Cantidad | Valor |
|---|---:|
| Pronóstico 24 h | 172,7 kWh |
| Pico pronosticado | 10,15 kW |
| Hora del pico | 11:00 |
| Real 17-11 (21 h) | 161,4 kWh |
| Pico real | 10,89 kW a las 15:00 |
| Pronóstico en las mismas 21 h | 156,0 kWh |
| MAE en las mismas 21 h | 0,317 kW |

> **Nota sobre la ventana.** Este demo usa el origen del 16-11 a las 23:00 y 21 h observadas. La tabla de energía diaria de la sección 11.2 usa el origen del 17-11 a las 00:00 y 20 h observadas. Por eso los totales difieren en una hora de carga base ($\approx5{,}5$ kWh); no son la misma ventana.

**Consistencia del soporte.** La diferencia entre el total de 24 h ($172{,}7$ kWh) y el total de las 21 h observadas ($156{,}0$ kWh) es $16{,}7$ kWh, la suma de las 3 horas faltantes (21:00, 22:00 y 23:00), que el modelo predice en $5{,}66+5{,}57+5{,}51=16{,}74$ kWh (la diferencia de $0{,}01$ es redondeo). No hay magia: es la misma predicción, sumada sobre soportes distintos.

**Lectura.** El pronóstico del 17-11 es bueno: $156{,}0$ kWh contra $161{,}4$ reales en las horas comparables, con un MAE de $0{,}317$ kW. El pico horario se queda corto ($10{,}15$ vs $10{,}89$) y la hora del pico se adelanta (11:00 vs 15:00): el modelo predice la curva media, no el máximo. Es la limitación de (12.10), no un error de la función.

---

## 13. Limitaciones

1. **Cobertura.** $45{,}3\,\%$ de minutos faltantes, $609$ horas válidas, $30$ días de origen, $25$ días de entrenamiento. Es un MVP, no un sistema en producción.
2. **Tamaño efectivo.** Las ventanas se solapan; el número de targets distintos es a lo sumo $600$ en train. La brecha train/test es inevitable en cierta medida.
3. **Sin variables exógenas.** No hay clima, ocupación, calendario académico ni festivos. El caso 11-16 muestra que un solo covariado faltante puede costar $41$ kWh en un día.
4. **Sin pronóstico probabilístico.** Se entrega un punto, no un intervalo. La incertidumbre no se cuantifica.
5. **Selección de hiperparámetros.** El fold 5 se usó para elegir el modelo; no es un holdout prístino.
6. **Sin purga.** El último día de train puede tener targets del primer día de test. El sesgo es leve, pero existe.
7. **Una sola partición temporal.** No hay validación cruzada repetida con distintas semillas de bloques; los 5 folds son los únicos.
8. **El pico no es el objetivo.** El máximo de la media no es la media del máximo; el pico reportado es referencial.
9. **Un solo festivo en test.** La conclusión sobre el 11-16 es sólida, pero generalizar a todos los festivos requiere más eventos.
10. **Sin test de Diebold-Mariano.** La comparación entre modelos es descriptiva; no se probó significancia con errores HAC.

---

## 14. Extensiones matemáticas

### 14.1 Variables de calendario

Agregar

$$
\text{feriado}_t,\qquad
\text{semana\_academica}_t,\qquad
\text{examen}_t
\qquad (14.1)
$$

al vector $x$. El modelo podría aprender la diferencia entre un lunes laboral y un lunes festivo. Con un solo festivo en test no se puede validar, pero es la extensión con mayor relación beneficio/costo.

### 14.2 Pronóstico probabilístico

En lugar de un punto, estimar cuantiles:

$$
\hat q_\tau(x) =
\arg\min_q
\mathbb{E}\left[
\rho_\tau\left(y-q\right)
\right],
\qquad
\rho_\tau(u)=u\left(\tau-\mathbf{1}\{u<0\}\right).
\qquad (14.2)
$$

Con $\tau=0{,}1,0{,}5,0{,}9$ se obtiene un intervalo $[q_{0.1},q_{0.9}]$. La cobertura empírica se evalúa con

$$
\text{cobertura} =
\frac{1}{n}\sum_i
\mathbf{1}\left\{
\hat q_{0.1}(x_i)\le y_i\le\hat q_{0.9}(x_i)
\right\}.
\qquad (14.3)
$$

Esto resolvería la limitación 4 y permitiría decir “el consumo estará entre $X$ e $Y$ kWh con $80\,\%$ de confianza”.

### 14.3 Modelo de dos componentes

$$
P_t=b_t+o_t,
\qquad
b_t\ \text{base lenta},
\qquad
o_t\ \text{ocupacion}.
\qquad (14.4)
$$

La base se modela con un suavizado o un estado latente; la ocupación, con el calendario. Es una descomposición interpretable y ataca directamente el error del 11-16: la base se mantiene, la ocupación se apaga.

### 14.4 Test de Diebold-Mariano

Para comparar dos pronósticos con errores $e_{1,t}$ y $e_{2,t}$:

$$
d_t=\left|e_{1,t}\right|-\left|e_{2,t}\right|,
\qquad
\mathrm{DM} =
\frac{\bar d}{\sqrt{\hat V(\bar d)}},
\qquad (14.5)
$$

donde $\hat V(\bar d)$ es una varianza HAC (Newey-West) que corrige la autocorrelación por el solapamiento. Con 5 folds no hay potencia; con más días, el DM permitiría afirmar si la diferencia híbrido-climatología es real.

### 14.5 Reconciliación jerárquica

El pronóstico horario y el diario deberían ser coherentes:

$$
\hat E_d=\sum_{h}\hat P_{t_0+h}.
\qquad (14.6)
$$

Si se pronostica la energía diaria con un modelo aparte, los dos niveles pueden contradecirse. Una reconciliación (por ejemplo, MinT) ajusta las proyecciones para que sumen. En este proyecto la energía se obtiene sumando las horas, así que la coherencia es exacta por construcción.

### 14.6 Más datos

La extensión más importante no es matemática: es tener 3–6 meses de serie continua. Con $25$ días, cada celda laboral de la climatología tiene $\approx25$ muestras y cada celda de fin de semana $\approx7$; con $90$ días, serían $\approx64$ y $\approx26$. La brecha y la varianza caerían. Ningún truco de modelado reemplaza los datos.

---

## 15. Apéndice

### A. Mapa código-fórmula

| Fórmula | Dónde está |
|---|---|
| (2.1) agregación horaria | `build_notebook.py` — notebook §1 |
| (4.1)–(4.4) dataset | `build_notebook.py` — notebook §3 |
| (5.5) climatología | `build_notebook.py` — notebook §4–§5 |
| (8.4) Ridge | `build_notebook.py` — notebook §4–§5 |
| (8.9)–(8.10) GBM | `build_notebook.py` — notebook §4–§5 |
| (9.1) híbrido | `build_notebook.py` — notebook §5 y §7 |
| (10.1)–(10.4) brecha | `analysis/generalization_checks.py`, `analysis/fold5_analysis.py` |
| Permutación de etiquetas (shuffle) | `analysis/generalization_checks.py` |
| (11.1) energía diaria | `analysis/daily_energy_error.py` |
| (12.5) `forecast_day` | `forecast.py` |
| (12.7)–(12.8) energía y pico | `forecast.py`, `summary_forecast` |

### B. Hiperparámetros

| Modelo | Hiperparámetros |
|---|---|
| Ridge | `alpha=1.0`, `StandardScaler` |
| Ridge one-hot | `alpha=1.0`, `OneHotEncoder(handle_unknown="ignore")` |
| GBM directo | `max_depth=4`, `max_iter=500`, `learning_rate=0.05`, `l2_regularization=1`, `min_samples_leaf=15`, `random_state=0` |
| Híbrido (residuo) | `max_depth=3`, `max_iter=150`, `learning_rate=0.03`, `l2_regularization=10`, `min_samples_leaf=30`, `random_state=0` |

### C. Tablas generadas

| Archivo | Contenido |
|---|---|
| `reports/tables/01_particiones.csv` | Particiones exactas |
| `reports/tables/01_metricas_folds.csv` | MAE y RMSE por fold y modelo |
| `reports/tables/01_resumen_modelos.csv` | Mediana de MAE, RMSE y skill |
| `reports/tables/01_mae_horizonte.csv` | MAE por horizonte |
| `reports/tables/01_generalizacion.csv` | Brecha y shuffle |
| `reports/tables/01_ablacion.csv` | Ablación |
| `reports/tables/01_learning_curve.csv` | Curva de aprendizaje |
| `reports/tables/01_importancia.csv` | Importancia por permutación |
| `reports/tables/01_r2_folds.csv` | R² por fold |
| `reports/tables/01_fold5_por_dia.csv` | MAE por día objetivo en el fold 5 |
| `reports/tables/01_fold5_sin_feriado.csv` | Fold 5 con y sin el 16-11 |

### D. Reproducción

```powershell
cd repo\Proyecto\potencia_activa
python build_notebook.py          # regenera y ejecuta el notebook
python forecast.py                # demo de forecast_day
python analysis\generalization_checks.py
python analysis\fold5_analysis.py
python analysis\daily_energy_error.py
```

### E. Glosario

| Término | Definición |
|---|---|
| Origen | Hora $t_0$ desde la cual se pronostica |
| Horizonte | Número de horas hacia adelante, $h$ |
| Ventana | Conjunto de 24 horizontes desde un origen |
| Solapamiento | Un target puede aparecer en varias ventanas |
| Climatología | Media por hora y tipo de día |
| Residuo | $y$ menos la climatología |
| Híbrido | Climatología más GBM del residuo |
| Fold | Una partición train/test del rolling origin |
| Holdout | El último fold, usado como test final |
| Brecha | MAE test menos MAE train |
| Skill | Mejora relativa frente al seasonal naive |
| Purga/embargo | Eliminar del train las ventanas que cruzan el test |

---

**Resumen final.** El proyecto formula el pronóstico como una regresión directa multi-horizonte con información $\mathcal{F}_{t_0}$-medible, entrena un híbrido climatología + GBM de residuos, valida con rolling origin sin shuffle y reporta tanto el rendimiento típico (MAE mediano $0{,}274$ kW) como el peor caso (fold 5, $0{,}643$ kW). La brecha train/test se descompone: $87{,}5\,\%$ se explica por el festivo del 16-11, no por memorización. En el régimen normal el modelo alcanza $R^2=0{,}961$, MAE $0{,}212$ kW y una brecha de $0{,}062$ kW. La conclusión es honesta: el modelo aprende la estructura del bloque y falla cuando cambia el régimen; la solución principal no es más regularización, es el covariado que falta.