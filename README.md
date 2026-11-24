# Teoría Aprendizaje de Máquina

Implementaciones, talleres, parciales y proyecto final del curso **Teoría del Aprendizaje de Máquina** (TAM), Universidad Nacional de Colombia, semestre 2026-2.

Los notebooks de práctica son autocontenidos: cargan o generan sus propios datos y pueden ejecutarse de principio a fin. Los notebooks del proyecto final se entregan ejecutados; sus datos crudos no se publican en este repositorio.

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![TensorFlow](https://img.shields.io/badge/TensorFlow-FF6F00?logo=tensorflow&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-EE4C2C?logo=pytorch&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-F7931E?logo=scikitlearn&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?logo=jupyter&logoColor=white)

## Contenido

| Carpeta | Notebook | Tema | Material adicional |
|---|---|---|---|
| `Implementaciones/` | [ActividadTAM.ipynb](Implementaciones/ActividadTAM.ipynb) | Perceptrón multicapa (784 → 64 → 16 → 10) sobre MNIST: arquitectura, compilación, entrenamiento y evaluación | — |
| `Implementaciones/` | [ActividadTAM_con_interfaz.ipynb](Implementaciones/ActividadTAM_con_interfaz.ipynb) | Extensión del anterior: `EarlyStopping`, matriz de confusión, guardado del modelo en `.keras`, preprocesamiento de imágenes propias e interfaz con Gradio | — |
| `Parciales/` | [Parcial_TAM_1.ipynb](Parciales/Parcial_TAM_1.ipynb) | **Ejercicio 1.5:** comparación de OLS, ML, Ridge y MAP en regresión lineal sobre características polinomiales. **Ejercicio 2.4:** estimación de MMD² con kernel RBF entre MNIST y Fashion-MNIST, con matrices de similitud por clase | [Parcial_TAM_1.pdf](Parciales/Parcial_TAM_1.pdf) |
| `Talleres/` | [Taller1.ipynb](Talleres/Taller1.ipynb) | Covarianza y correlación de Pearson sobre píxeles de MNIST, y su equivalente en el espacio del kernel mediante la matriz de Gram | — |
| `Talleres/` | [Taller_2_TAM.ipynb](Talleres/Taller_2_TAM.ipynb) | Señal senoidal con ruido gaussiano (AWGN), matriz de diseño polinomial y reconstrucción con LS, RLS, ML y MAP | — |
| `Talleres/` | [Taller_TAM_Alternativo.ipynb](Talleres/Taller_TAM_Alternativo.ipynb) | Solución computacional del Taller 1: clasificación lineal y perceptrón, k-NN con k = 1, 5, 15, matriz de confusión y métricas de evaluación | [Taller_TAM_Alternativo.pdf](Talleres/Taller_TAM_Alternativo.pdf) |
| `Talleres/` | [TAM_clase.ipynb](Talleres/TAM_clase.ipynb) | Demostración de clase: generación de una señal, adición de ruido y reconstrucción | — |

## Proyecto final

**[PeakGuard](Proyecto/README.md)** responde cuál es la probabilidad de que la potencia activa supere 12 kW en los próximos 15 minutos, usando mediciones de los medidores 200 y 201 de una subestación universitaria. El trabajo cubre auditoría de datos, regresión logística calibrada, validación `rolling-origin` y evaluación operativa retrospectiva (alertas, lead time y costos).

| Libreta | Contenido |
|---|---|
| [01_data_audit.ipynb](Proyecto/01_data_audit.ipynb) | Construcción de la serie de 1 min, auditoría de huecos y validación física |
| [02_peak_model.ipynb](Proyecto/02_peak_model.ipynb) | Definición del target, ajuste de la ecuación, validación temporal, calibración y generalización |
| [03_evaluation.ipynb](Proyecto/03_evaluation.ipynb) | Evaluación de episodios de pico, alertas, lead time, costos y análisis de errores |

También se incluye el proyecto de **pronóstico de potencia activa a 24 h** en [`potencia_activa/`](Proyecto/potencia_activa/README.md).

Los ZIP con las mediciones originales no se publican. Las libretas conservan sus salidas y los datos procesados, tablas, figuras y modelos sí están disponibles. Para regenerar la auditoría se necesitan `analizador 200.zip` y `analizador 201.zip` dentro de `Proyecto/`.

## Temas cubiertos

- **Estimación y regresión lineal:** mínimos cuadrados, máxima verosimilitud, regularización Ridge y máximo a posteriori (MAP).
- **Métodos kernel:** matrices de Gram, covarianza y correlación en el espacio de características, máxima discrepancia media (MMD²).
- **Clasificación:** perceptrón, k-NN y fronteras de decisión.
- **Evaluación de modelos:** matriz de confusión, accuracy, precision, recall, F1 y limitaciones del accuracy con clases desbalanceadas.
- **Redes neuronales:** perceptrón multicapa en TensorFlow/Keras, entrenamiento, `EarlyStopping` e inferencia sobre imágenes propias.
- **Preprocesamiento:** normalización, redimensionamiento y adaptación de imágenes al formato de MNIST.

## Cómo ejecutar

### En Google Colab

1. Abre el notebook desde GitHub.
2. Usa **Open in Colab** o descárgalo y súbelo a [colab.research.google.com](https://colab.research.google.com/).
3. Ejecuta con **Runtime → Run all**.

Todos los notebooks funcionan en Colab. El único que importa `google.colab` es `ActividadTAM_con_interfaz`, como alternativa al cargue de archivos con Gradio.

### En local

Se recomienda un entorno virtual con Python 3.10 o superior:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install numpy pandas matplotlib seaborn scikit-learn tensorflow torch torchvision opencv-python pillow gradio jupyter
jupyter notebook
```

No es necesario descargar datasets: MNIST y Fashion-MNIST se obtienen automáticamente mediante `tensorflow.keras.datasets` y `torchvision`, y `make_moons` se genera con `scikit-learn`.

Para el proyecto final, instale las dependencias de `Proyecto/requirements.txt` y siga las instrucciones de [su README](Proyecto/README.md). Recuerde que los ZIP originales no están incluidos.

## Estructura del repositorio

```
.
├── Implementaciones/
│   ├── ActividadTAM.ipynb
│   └── ActividadTAM_con_interfaz.ipynb
├── Parciales/
│   ├── Parcial_TAM_1.ipynb
│   └── Parcial_TAM_1.pdf
├── Proyecto/
│   ├── 01_data_audit.ipynb
│   ├── 02_peak_model.ipynb
│   ├── 03_evaluation.ipynb
│   ├── analysis/, data/processed/, models/, reports/
│   ├── PEAKGUARD.md, README.md, requirements.txt
│   └── potencia_activa/
└── Talleres/
    ├── TAM_clase.ipynb
    ├── Taller1.ipynb
    ├── Taller_2_TAM.ipynb
    ├── Taller_TAM_Alternativo.ipynb
    └── Taller_TAM_Alternativo.pdf
```

## Notas

- Los notebooks conservan las salidas de ejecución (gráficas, métricas y matrices) como referencia de los resultados obtenidos.
- El entrenamiento del MLP puede tardar unos minutos según el hardware; en Colab se recomienda activar GPU.
- Los PDF adjuntos corresponden al enunciado o al informe entregado junto con el notebook.

## Autor

**Sebastian Tovar** — [@stovarj-ing](https://github.com/stovarj-ing)

Curso Teoría del Aprendizaje de Máquina, Universidad Nacional de Colombia, 2026-2.
