# Taller Reconocimiento de Postura con MediaPipe

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

Fecha de entrega: 2026-05-25

## Descripcion breve

El objetivo de este taller fue disenar e implementar un sistema de reconocimiento de acciones corporales en tiempo real que detecta y clasifica posturas humanas utilizando analisis de landmarks con MediaPipe Pose. El sistema es capaz de rastrear los 33 puntos clave (landmarks) del cuerpo humano definidos por el modelo de MediaPipe y, a partir de ellos, calcular angulos articulares y distancias entre puntos para clasificar las siguientes acciones:

1. **Sentado**: La cadera se encuentra al nivel o por debajo de las rodillas, con angulos de rodilla flexionados (< 140 grados).
2. **Brazos Levantados**: Ambas munecas se posicionan por encima de la cabeza (nariz) y los angulos de hombro superan los 140 grados.
3. **Caminando**: Se detecta alternancia periodica en la posicion horizontal de los tobillos (cambios de signo en la diferencia X) dentro de una ventana temporal de 1.5 segundos.

El sistema incluye retroalimentacion multimodal: visual (esqueleto coloreado por accion, badge de estado, borde parpadeante, panel lateral con angulos y distancias en tiempo real) y sonora (tonos sinteticos diferenciados por accion generados con pygame). Ademas, incorpora un HUD interactivo con botones clicables para filtros visuales (Original, Gris, Binario, Canny), control de pausa/play, captura de instantaneas, grabacion de video y salida.

Al igual que el taller anterior de YOLO, el sistema cuenta con un modo de contingencia de triple nivel para garantizar su ejecucion en cualquier computadora: intenta abrir la webcam, descarga un video de prueba si no hay camara, y genera una simulacion sintetica animada como ultimo recurso.

## Implementaciones

### 1. Entorno Python Independiente (main.py)

El archivo `python/main.py` contiene el pipeline completo de procesamiento en tiempo real. Sus componentes principales son:

- **MediaPipe Pose Engine**: Se inicializa el modelo `mp.solutions.pose.Pose` con `model_complexity=1` para un balance optimo entre precision y rendimiento. El modelo detecta y rastrea los 33 landmarks del cuerpo humano con suavizado temporal (`smooth_landmarks=True`) para reducir el jitter entre frames consecutivos.

- **Motor de Geometria Corporal**: Funciones matematicas dedicadas al calculo de:
    - **Angulos articulares** (`calculate_angle`): Calcula el angulo formado entre tres puntos usando producto punto y arcocoseno. Se calculan 6 angulos clave: rodillas (cadera-rodilla-tobillo), codos (hombro-codo-muneca) y hombros (cadera-hombro-codo).
    - **Distancias euclidianas** (`calculate_distance`): Mide la separacion entre pares de landmarks relevantes (caderas, hombros, tobillos).

- **Clasificador de Acciones por Reglas Geometricas** (`classify_action`): Implementa una cascada de condiciones logicas priorizadas:
    1. **Brazos Levantados**: Verifica que `wrist.y < nose.y` para ambas munecas y que los angulos de hombro excedan 140 grados.
    2. **Sentado**: Detecta cuando el punto medio Y de las caderas iguala o supera al de las rodillas, con angulos de rodilla flexionados (< 140 grados).
    3. **Caminando**: Mantiene un historial temporal de posiciones de tobillos de 1.5 segundos. Detecta cambios de signo en la diferencia horizontal de tobillos (alternancia de paso), con un umbral minimo de 15px para filtrar ruido.

- **Visualizacion de Esqueleto Estilizado**: Dibuja 16 conexiones oseas principales con efecto de doble linea (exterior coloreada, interior brillante) y 33 landmarks con halo coloreado y centro blanco. El color del esqueleto cambia dinamicamente segun la accion detectada.

- **Panel Lateral de Telemetria**: Muestra en tiempo real: accion detectada con nombre y barra de confianza, los 6 angulos articulares calculados, las 3 distancias principales, conteo de landmarks visibles y numero de pasos acumulados.

- **Retroalimentacion Sonora via Pygame**: Genera tonos sinusoidales sinteticos con envolvente de raised cosine para evitar clicks de audio. Cada accion tiene una frecuencia unica: 440Hz (Sentado), 660Hz (Brazos Levantados), 330Hz (Caminando). Un tono de transicion de 880Hz suena al cambiar de accion. Un sistema de cooldown de 1.5 segundos previene la saturacion sonora.

- **HUD Glassmorphic Interactivo**: Identico al del taller de YOLO, con botones clicables, efectos de hover, estados activos y acciones de snapshot/grabacion/pausa.

## Resultados visuales


### 1. Video deteccion de poses

![Neutro](./media/pose_detection.gif)

_GIF del programa en funcionamiento detectando todas las poses requeridas_

## Codigo relevante

### 1. Calculo de Angulos Articulares

Funcion central de geometria que calcula el angulo entre tres landmarks usando el producto punto vectorial:

```python
def calculate_angle(a, b, c):
    """
    Calcula el angulo (en grados) formado por tres puntos.
    El vertice del angulo esta en el punto b.
    """
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])

    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))
    return angle
```

### 2. Clasificacion de Acciones por Geometria Corporal

Cascada de reglas condicionales que analiza la posicion relativa de los landmarks y los angulos articulares para determinar la accion:

```python
# REGLA 1: BRAZOS LEVANTADOS
wrists_above_head = (left_wrist[1] < head_y and right_wrist[1] < head_y)
shoulders_raised = (angles["hombro_izq"] > 140 and angles["hombro_der"] > 140)

if wrists_above_head and shoulders_raised:
    conf = min(1.0, (angles["hombro_izq"] + angles["hombro_der"]) / 360)
    return "BRAZOS LEVANTADOS", conf, angles, distances

# REGLA 2: SENTADO
hip_below_or_level_knee = (hip_mid_y >= knee_mid_y - 30)
knees_bent = (angles["rodilla_izq"] < 140 and angles["rodilla_der"] < 140)

if hip_below_or_level_knee and knees_bent:
    avg_knee = (angles["rodilla_izq"] + angles["rodilla_der"]) / 2
    conf = max(0.6, 1.0 - (avg_knee / 180))
    return "SENTADO", conf, angles, distances

# REGLA 3: CAMINANDO (alternancia temporal de tobillos)
if sign_changes >= 2 or (legs_apart and avg_y_var > 10):
    conf = min(1.0, 0.5 + sign_changes * 0.15 + (avg_y_var / 50))
    return "CAMINANDO", conf, angles, distances
```


### 3. Deteccion de Caminata por Historial Temporal

El algoritmo de deteccion de caminata mantiene un buffer deslizante de 1.5 segundos con las posiciones relativas de los tobillos:

```python
# Registrar posicion relativa
ankle_diff_x = left_ankle[0] - right_ankle[0]
step_history.append({"time": current_time, "diff_x": ankle_diff_x, "diff_y": ankle_diff_y})

# Ventana temporal deslizante
step_history = [s for s in step_history if current_time - s["time"] < 1.5]

# Contar cambios de signo (cruces de piernas)
diffs = [s["diff_x"] for s in step_history]
sign_changes = 0
for i in range(1, len(diffs)):
    if diffs[i] * diffs[i-1] < 0 and abs(diffs[i] - diffs[i-1]) > 15:
        sign_changes += 1
```

## Instrucciones de Instalacion y Ejecucion

### 1. Preparacion del Entorno Virtual (Recomendado)

```bash
python -m venv .venv

# En Windows (PowerShell):
.venv\Scripts\Activate.ps1

# En Windows (CMD):
.venv\Scripts\activate.bat

# En macOS/Linux:
source .venv/bin/activate

# Instalar dependencias:
pip install -r python/requirements.txt

```

### 2. Ejecucion del Script Principal

```bash
cd python
python main.py
```

## Prompts utilizados

- No esta capturando la pose de estar sentado. Como lo soluciono?

IDE, compilador y generacion de documentacion: Antigravity

## Aprendizajes y dificultades

### Aprendizajes

- **Geometria Corporal Aplicada**: Se aprendio a traducir conceptos geometricos clasicos (angulos entre vectores, distancias euclidianas) en reglas de clasificacion practica para acciones humanas. La eleccion de angulos articulares como features principales demostro ser robusta ante variaciones de escala y distancia a la camara.
- **Analisis Temporal para Deteccion de Movimiento**: La deteccion de caminata requirio ir mas alla del analisis estatico por frame y disenar un sistema de ventana deslizante temporal que acumula patrones de alternancia. Esto enseno la diferencia fundamental entre clasificar poses estaticas (sentado, brazos arriba) y acciones dinamicas (caminar).
- **Retroalimentacion Multimodal sin Dependencias Externas**: Se genero audio sintetico proceduralmente con numpy y pygame, eliminando la necesidad de archivos de sonido. La envolvente raised cosine previene artefactos de audio (clicks) que surgian con ondas cortadas abruptamente.

### Dificultades

- **Umbral de Deteccion de Caminata**: La deteccion de alternancia en los tobillos resulto ser muy sensible al ruido del tracking. Se soluciono implementando un umbral minimo de 15 pixeles en los cambios de posicion y requiriendo al menos 2 cruces de signo confirmados dentro de la ventana temporal, filtrando asi los falsos positivos por jitter.
- **Prioridad de Clasificacion**: Cuando un usuario esta sentado y levanta los brazos, ambas reglas se activan simultaneamente. Se soluciono implementando una cascada priorizada donde BRAZOS LEVANTADOS tiene precedencia sobre SENTADO, reflejando la logica de que la accion de los brazos es la mas visualmente distinguible y la que el usuario espera ver reconocida primero.
- **Compatibilidad de Pygame en Entornos sin Audio**: En servidores o contenedores sin tarjeta de sonido, `pygame.mixer.init()` falla silenciosamente. Se encapsulo toda la logica de audio en bloques try/except con un flag `SOUND_AVAILABLE` para degradacion elegante a modo solo visual.

## Estructura del proyecto

```
semana_11_2_reconocimiento_postura_mediapipe/
├── python/
│   ├── main.py              # Script principal con deteccion de postura en tiempo real
│   └── requirements.txt     # Listado de dependencias
├── media/                   # Evidencias visuales de ejecucion (capturas PNG)
└── README.md                # Este archivo de documentacion academica
```

## Referencias

- MediaPipe Pose Landmarker: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
- MediaPipe Pose Landmark Indices: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker#pose_landmarker_model
- OpenCV - Mouse as a Paint Brush: https://docs.opencv.org/4.x/db/d5b/tutorial_py_mouse_handling.html
- OpenCV - VideoWriter Class Reference: https://docs.opencv.org/4.x/dd/d9e/classcv_1_1VideoWriter.html
- Pygame Mixer Documentation: https://www.pygame.org/docs/ref/mixer.html
- Numpy Signal Processing: https://numpy.org/doc/stable/reference/routines.fft.html
