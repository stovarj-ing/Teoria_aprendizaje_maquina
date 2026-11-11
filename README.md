# Teoría del Aprendizaje de Máquina

Implementaciones, talleres y parciales del curso **Teoría del Aprendizaje de Máquina** (TAM), Universidad Nacional de Colombia, semestre 2026-2.

Cada notebook es autocontenido: carga o genera sus propios datos y puede ejecutarse de principio a fin.

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

## Estructura del repositorio

```
.
├── Implementaciones/
│   ├── ActividadTAM.ipynb
│   └── ActividadTAM_con_interfaz.ipynb
├── Parciales/
│   ├── Parcial_TAM_1.ipynb
│   └── Parcial_TAM_1.pdf
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
