# Pintura Interactiva con Voz y Gestos

Aplicación de pintura digital en tiempo real que combina **detección de gestos de mano** (MediaPipe) con **comandos de voz** (SpeechRecognition) para crear una experiencia de dibujo inmersiva usando la webcam.

## Requisitos

- Python 3.9+
- Webcam
- Micrófono
- Conexión a internet (para reconocimiento de voz con Google API)

## Instalación

```bash
pip install -r requirements.txt
```

> **Nota:** Se usa `sounddevice` en lugar de `PyAudio` para compatibilidad con Python 3.12+.
> `sounddevice` incluye su propio binario de PortAudio, sin necesidad de compilación.

## Ejecución

```bash
python pintura_interactiva.py
```

## Controles

### Gestos de mano

|           Gesto         | Acción |
|-------------------------|--------|
| ☝️ **1 dedo** (índice) | Pincel fino redondo |
| ✌️ **2 dedos** | Pincel mediano redondo |
| 🖐️ **Palma abierta** (5 dedos) | Pincel grueso cuadrado |
| ✊ **Puño cerrado** (0 dedos) | Pausa (mover sin pintar) |

### Comandos de voz (español)

| Comando | Acción |
|---|---|
| `"rojo"`, `"verde"`, `"azul"`, `"amarillo"`, `"blanco"`, `"morado"`, `"naranja"`, `"rosa"`, `"cyan"` | Cambiar color del pincel |
| `"pincel"` / `"brocha"` | Alternar entre pincel fino y grueso |
| `"limpiar"` / `"borrar"` | Limpiar el lienzo |
| `"guardar"` / `"salvar"` | Guardar la obra como PNG |

### Teclado

| Tecla | Acción |
|---|---|
| `Q` | Salir de la aplicación |
| `C` | Limpiar el lienzo |
| `S` | Guardar la obra |

## Estructura del proyecto

```
semana_7_9_pintura_interactiva_voz_gestos/
├── pintura_interactiva.py   # Aplicación principal
├── requirements.txt         # Dependencias
├── README.md                # Este archivo
└── obras/                   # Carpeta de imágenes guardadas (se crea automáticamente)
```

## Características

- **Detección de gestos en tiempo real** con MediaPipe Hands
- **Reconocimiento de voz en español** con Google Speech API (hilo en segundo plano)
- **9 colores** disponibles mediante comandos de voz
- **3 tipos de pincel** que cambian según el gesto (fino, mediano, grueso/cuadrado)
- **HUD interactivo**: paleta de colores, estado del pincel, indicador de micrófono
- **Retroalimentación visual** con texto animado al ejecutar comandos
- **Guardado de obras** en formato PNG con timestamp
- **Cursor visual** que muestra la posición y forma del pincel en tiempo real

## Herramientas utilizadas

| Librería | Uso |
|        ---        |---|
| `mediapipe` | Detección de manos y landmarks |
| `opencv-python` | Captura de cámara, dibujo, composición de imagen |
| `speech_recognition` | Reconocimiento de comandos de voz |
| `sounddevice` | Captura de audio del micrófono |
| `numpy` | Operaciones con matrices de píxeles |
