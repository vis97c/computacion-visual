# Proyecto: Pipeline de Procesamiento y Clasificación de Microplásticos

Este proyecto implementa una herramienta automatizada e interactiva para el preprocesamiento, segmentación y clasificación de microplásticos en muestras de playa. Diseñado como parte de la asignatura de **Computación Visual** en la **Universidad Nacional de Colombia**, el sistema utiliza técnicas clásicas de visión artificial (OpenCV) combinadas con aprendizaje supervisado (scikit-learn) para superar los cuellos de botella del análisis manual.

---

## 1. Arquitectura y Funcionamiento

El proyecto está dividido en dos grandes fases según el brief original:

1. **Fase A: Preprocesamiento Gráfico (OpenCV):**
    - **Suavizado y corrección de iluminación:** Reducción de ruido físico y textura del papel mediante desenfoque Gaussiano.
    - **Umbralización Adaptativa:** Segmentación local para aislar partículas oscuras sobre el fondo del filtro/papel.
    - **Filtro de Región de Interés (ROI):** Exclusión de contornos que tocan los bordes y exclusión relativa de los scale bars (escalas de medición) ubicadas en posiciones fijas de la imagen.

2. **Fase B: Extracción de Características y Clasificación (IA):**
    - **Feature Engineering (16 Descriptores):** Para cada contorno detectado, se extraen propiedades morfológicas (área, perímetro, circularidad, relación de aspecto, elongación, solidez, excentricidad) y cromáticas (medias y desviaciones estándar en canales RGB y HSV).
    - **Clasificador (Random Forest):** Entrenado usando ponderación de clases balanceada para mitigar el desequilibrio en clases minoritarias.

### Modelos de Clasificación Soportados

Para mejorar las estimaciones y explorar datasets de mejor calidad, el sistema soporta tres modelos clasificadores distintos:

- **Modelo Original (`ceroplastic`):** Basado en el consenso estricto de los 3 anotadores del dataset original (Melissa, Brayan y Camila).
- **Modelo Valerio (`valerio`):** Entrenado exclusivamente sobre el dataset de Roboflow (formato COCO) con etiquetas de alta calidad. Mapea clases de origen (`beads` -> `Pellet`, `fibers` -> `Fibra`, `fragments` -> `Fragmento`) y usa bounding boxes para asociar etiquetas con contornos OpenCV.
- **Modelo Fusión (`ceroplastic_valerio`):** Combina de manera equilibrada ambos datasets (Ceroplastic + Valerio) para maximizar la generalización y robustez del modelo.

---

## 2. Estructura del Proyecto

```text
microplasticos/
├── brief.pdf                           # Documento de requerimientos del proyecto
├── Ceroplastic/                        # Directorios de imágenes TIFF (Dataset original)
├── Valerio/                            # Directorio del dataset adicional de Roboflow (COCO)
├── backend/                            # Servidor API de Python
│   ├── pipeline.py                     # Lógica de procesamiento de imágenes con OpenCV
│   ├── model_trainer.py                # Script de mapeo de datasets, extracción y entrenamiento
│   ├── app.py                          # Servidor Flask y enrutamiento API
│   ├── test_api.py                     # Pruebas unitarias de los endpoints de la API
│   ├── microplastics_model_ceroplastic.joblib        # Pesos del modelo original
│   ├── microplastics_model_valerio.joblib            # Pesos del modelo Valerio
│   ├── microplastics_model_ceroplastic_valerio.joblib # Pesos del modelo Fusión
│   └── valerio_features_cache.joblib   # Cache de descriptores para optimización de entrenamiento
├── frontend/                           # Panel interactivo en React
│   ├── src/
│   │   ├── App.jsx                     # Dashboard principal, lógica de lote y visor interactivo
│   │   ├── App.css                     # Estilos específicos de componentes y gráficos SVG
│   │   ├── index.css                   # Sistema de diseño general de Glassmorphism
│   │   └── main.jsx                    # Punto de entrada de React
│   ├── package.json
│   └── vite.config.js
└── README.md                           # Guía de instalación y documentación (este archivo)
```

---

## 3. Instalación y Configuración

### Requisitos Previos

- **Python 3.11** o superior
- **Node.js** v18 o superior con **npm**

### Paso 1: Configurar el Backend (Python)

Instala las dependencias necesarias utilizando `pip`:

```bash
# With requirements.txt
pip install -r backend/requirements.txt
# Manually
pip install opencv-python pandas scikit-learn openpyxl joblib flask flask-cors
```

### Paso 2: Configurar el Frontend (React)

Navega a la carpeta del frontend e instala los paquetes de Node:

```bash
cd frontend
npm install
```

---

## 4. Ejecución del Proyecto

### 1. Iniciar el Servidor Backend (API Flask)

Desde la raíz del proyecto, ejecuta:

```bash
python backend/app.py
```

El servidor backend se levantará en `http://localhost:5000`.
_Nota: Si alguno de los modelos `.joblib` no existe al iniciar, el backend los entrenará automáticamente antes de abrir el puerto._

### 2. Iniciar el Servidor Frontend (Vite)

Abre otra terminal, navega a la carpeta `frontend/` y ejecuta:

```bash
cd frontend
npm run dev
```

La aplicación web estará disponible de inmediato en la dirección local `http://localhost:5173`.

---

## 5. Descripción de la API Flask

La API cuenta con cuatro endpoints principales habilitados con CORS y parametrizados por modelo:

- **`POST /api/predict?model=<nombre_modelo>`:**
    - Recibe un archivo de imagen (soporta formatos `.tif`, `.tiff`, `.png`, `.jpg`).
    - Procesa la imagen, segmenta las partículas, predice sus clases en tiempo real con el clasificador seleccionado (`ceroplastic`, `valerio`, o `ceroplastic_valerio`).
    - Devuelve un JSON con la imagen anotada (en base64, con cajas y etiquetas dibujadas en OpenCV) y un listado de partículas con su área, circularidad y coordenadas exactas.
- **`GET /api/model-info?model=<nombre_modelo>`:**
    - Devuelve las métricas del clasificador seleccionado (exactitud media de validación cruzada, matriz de confusión e importancia de características).
- **`POST /api/train?model=<nombre_modelo>`:**
    - Desencadena el reentrenamiento del modelo especificado usando validación cruzada y actualiza el archivo `.joblib` correspondiente.
    - Para optimizar la velocidad, utiliza un cache persistente (`valerio_features_cache.joblib`) para evitar recalcular descriptores del dataset Valerio (1,600+ imágenes).
- **`GET /api/stats`:**
    - Analiza dinámicamente el archivo Excel `Clasificación microplasticos-guia.xlsx` y calcula el ratio de consenso de los anotadores (Melissa, Brayan y Camila) del dataset original.

---

## 6. Funcionalidades Avanzadas de Interfaz

- **Reprocesamiento Automático de Lote:** Si el usuario ya ha procesado o intentado procesar un lote de imágenes de microscopio, pero decide cambiar el modelo de clasificación en el menú desplegable del Dashboard, la interfaz **resetea y reprocesa automáticamente el lote completo** utilizando el nuevo modelo.
- **Prevención de Condiciones de Carrera:** El frontend cuenta con un control de sesión asíncrona (`processSessionIdRef`) que cancela de forma segura cualquier procesamiento anterior en progreso si el usuario cambia el modelo de clasificación a mitad del proceso, garantizando la consistencia de los datos en pantalla.

---

## 7. Desarrollado por

Estudiantes de Computación Visual - Universidad Nacional de Colombia:

- Jose Arturo Herrera Rivera
- Juan Jose Alvarez Lozano
- Juan Pablo Correa Sierra
- Manuel Santiago Mori Ardila
- Victor Ivan Saa Caicedo

**Presentado a:** Aura Maria Forero Pachon
Bogotá D.C., 2026.
