# Taller Pintura Interactiva con Voz y Gestos

## Nombres de los estudiantes

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

## Fecha de entrega

`2026-04-25`

---

## Descripción breve

Este taller explora la creación de una aplicación de pintura digital interactiva en tiempo real utilizando visión por computadora y procesamiento de lenguaje natural (NLP). La herramienta permite al usuario pintar en la pantalla usando su dedo como un pincel virtual e interactuar con la interfaz a través de comandos de voz, creando una experiencia *hands-free* (manos libres).

Se construyó un pipeline visual integrando **MediaPipe HandLandmarker** para el seguimiento y estimación de puntos articulares de la mano, y **SpeechRecognition (Google API)** para capturar comandos hablados. Dependiendo del número de dedos levantados, el pincel cambia de tamaño (fino, medio, brocha gruesa) o de estado (pausa temporal). Con la voz, el usuario logra modificar el color activo, limpiar el lienzo o guardar progresos sin tocar el mouse o el teclado. Todo esto se visualiza con una interfaz inmersiva mediante **OpenCV**.

---

## Implementaciones

### Python y OpenCV

Toda la aplicación principal está montada sobre un bucle de video procesado con OpenCV. Sobre cada frame de la webcam se aplican máscaras y mezclas de interpolación geométrica (`cv2.addWeighted`) para superponer un panel de estado (HUD) translúcido y aplicar el canvas generado sobre el feed directo de la cámara, mejorando el contraste visual oscureciendo el video base al 55%.

### MediaPipe Tasks API (Gestos)

Se migró explícitamente desde la funcionalidad "Legacy Solutions" directamente a la **MediaPipe Tasks API** (`mp.tasks.vision.HandLandmarker`). 
Para los gestos, cuenta los dedos analizando la posición "Y" relativa de las últimas falanges vs sus pívotes de rotación interna (y para el pulgar el eje X relativo a la muñeca).
*   **1 Dedo (Índice):** Trazo fino.
*   **2 Dedos (Paz):** Trazo mediano.
*   **Palma (5 dedos):** Trazo plano estilo brocha marcadora cuadrada.
*   **Puño (0 dedos):** Pausa del trazador (permite mover la mano para reubicar la posición sin pintar de por medio).

### Speech Recognition + SoundDevice (Voz en Hilo Secundario)

Para evitar bloquear el procesamiento de los frames en tiempo real, el reconocimiento de audio está alojado en un `Thread` que se ejecuta como *daemon*. Extrae fragmentos (*chunks*) de 3 segundos utilizando la librería de captura de audio a bajo nivel **sounddevice** (como alternativa cross-platform robusta ante problemas de compilación del header C de *PyAudio*) y los procesa vía API de Google para detectar palabras claves (keyword spotting de comandos como "rojo", "morado", "pincel", "limpiar", "guardar").

---

## Resultados visuales

### Funcionamiento general

![Funcionamiento general](./media/funcionamiento_general.gif)

El usuario puede pintar con la mano, cambiar el color de la brocha con la voz y limpiar el lienzo con la voz.


---

## Código relevante

### Reconocimiento de Voz Continuo asíncrono (`VoiceListener`)

```python
def _listen_loop(self):
    while self.running:
        try:
            # Grabación de audio raw en chunks sin dependencias de PyAudio
            audio_np = self._record_chunk()
            audio_bytes = audio_np.tobytes()
            audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, 2)
            
            # Reconocimiento con la API de Google
            text = self.recognizer.recognize_google(audio_data, language="es-ES").lower().strip()
            # Mapeo a variable de estado segura por concurrencia
            with self._lock:
                self.last_command = text
                self.command_time = time.time()
        except:
            pass # Ignoramos errores de inactividad
```

### Clasificación de Dedos Levantados

```python
def _count_fingers(self, hand):
    tips = [4, 8, 12, 16, 20]     # Puntas de cada dedo
    pips = [3, 6, 10, 14, 18]     # Articulaciones PIP / IP
    count = 0

    # Pulgar se analiza horizontalmente respecto a la muñeca
    wrist_x = hand[0].x
    if abs(hand[4].x - wrist_x) > abs(hand[3].x - wrist_x):
        count += 1

    # Demás dedos se miden verticalmente en pantalla
    for tip, pip in zip(tips[1:], pips[1:]):
        if hand[tip].y < hand[pip].y:
            count += 1
            
    return count
```

### Fusión Visual del Lienzo (Canvas) y la Cámara

```python
# Crear máscara aislando los trazos vs el fondo
gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
_, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

# Oscurecer la cámara gradualmente e incrustar la capa del dibujo vectorial
display = (frame * 0.55).astype(np.uint8)
display[mask > 0] = self.canvas[mask > 0]
```

---

## Diagrama de Flujo del Programa

```
                     ┌───────────────────────────────────┐
                     │                                   │
              ┌──────▼───────┐                       ┌───┴──────────┐
  Cámara WEB ─► Frame (OPENCV)                       │ Hilo de Voz  │ ◄─── Micrófono
              └──────┬───────┘                       └───┬──────────┘
                     │                            text = recognize_google()
         ( HandLandmarker.detect() )                     │
                     │                                   │ (Verifica > Timeout?)
              ┌──────▼────────┐                      ┌───▼──────────┐
              │ landmarks_list│                      │ Voice Cmd    │
              │ finger_count  │                      │ "rojo","pincel"
              │ index_pos     │                      │ "guardar",...│
              └──────┬────────┘                      └───┬──────────┘
                     │                                   │
                     ├───────────────────────────────────┘
              ┌──────▼─────────┐
              │ Canvas Updates │
              │ - Dibujo pos x,y
              │ - Cambio de Color
              │ - Modos de Trazo
              └──────┬─────────┘
                     │
              ┌──────▼─────────┐    Si se activa voz "guardar":
              │ UI Render HUD  │ ─────► cv2.imwrite("./obras/...")
              └──────┬─────────┘
                     │
               ┌─────▼──────┐
               │ cv2.imshow │
               └────────────┘
```

---

## Prompts utilizados

```
"Escribe una clase de Python que utilice mediapipe para detectar una y solo una 
mano desde un feed de opencv. Crea una función que evalúe y retorne numéricamente 
cuántos dedos hay levantados comparando la altura de las falanges."

"Reemplaza el uso de PyAudio con `sounddevice` para el paquete de reconocimiento
de voz de python, ya que PyAudio no compila bajo Python 3.14 o Windows. Captura
los fotogramas de audio en arreglos numpy, conviértelos a Bytes y pásalos 
directamente al objeto `sr.AudioData` de SpeechRecognition."

"Crea una interfaz de OpenCV HUD inmersiva. Agrega un panel opaco a la izquierda 
con la paleta de colores disponibles y un texto semitransparente superior 
mostrando el Color actual y el modo de grosor del pincel. Combina estas interfaces
usando cv2.addWeighted."
```

---

## Aprendizajes y dificultades

### Aprendizajes

La integración de NLP y Visión por Computadora en un entorno en tiempo real enseña importantes lecciones de control de concurrencia. Extraer el analizador de voz a un hilo separado usando locks protegió el rendimiento de FPS, permitiendo que la cámara continuara rendereando fluido a 30fps sin sufrir pausas provocadas por las peticiones de timeout hacia la red en cada detección de voz.

La lógica de contar dedos utilizando *relaciones espaciales absolutas* (saber que si *tip.y* es menor que *pip.y* asumiendo coordenadas desde la parte superior-izquierda cuenta como "levantado") demostró ser matemáticamente sencilla pero inmensamente robusta y predecible que alternativas más pesadas, consolidando la superioridad geométrica directa.

### Dificultades

**API deprecada de MediaPipe:** Entre versiones (particularmente recientes de 0.10.x), MediaPipe abandonó su clásica estructura de `mp.solutions.hands` trasladando a una exigencia absoluta y documentada de interactuar vía `Tasks API (Vision)`. Esto presentó problemas donde el ambiente de ejecución retornaba excepciones de módulos faltantes o atributos omitidos. La solución conllevó una refactorización masiva para manejar tensores, cargar archivos estáticos modelo `.task` del disco y convertir las viejas configuraciones.

**Problemas de Header de Audio con PyAudio:** En versiones vanguardistas de Python o equipos de 64-bit Windows mal acoplados para C++ Build Tools de PortAudio, la instalación fallaba fatalmente al levantar `PyAudio`. En lugar de forzar instalaciones de *pipwin* (que fracasaron por inconsistencias de paths), se reescribió el módulo completo de captura para usar `sounddevice` (el cual carga su DLL binario precompilado *PortAudio* por detrás), parseando la cinta de bytes por nosotros mismos hacia el Reconocedor original de *SpeechRecognition*.

---

## Contribuciones grupales

Taller realizado de forma individual.

---

## Estructura del proyecto

```
semana_7_9_pintura_interactiva_voz_gestos/
├── python/
│   ├── pintura_interactiva.py       # Aplicación principal
│   ├── requirements.txt             # Dependencias del proyecto
│   ├── hand_landmarker.task         # Modelo nativo de predicción Tensor MediaPipe
│   └── README.md                    # Documentación legacy / quickstart
├── media/
│   ├── pincel_fino.gif
│   ├── pincel_grueso.gif
│   ├── hud_voz.gif
│   └── mediapipe_hand.png
├── obras/                           # Salida local de snapshots generados con el canvas
└── README.md                        # Documentación principal en formato taller
```

---

## Referencias

- MediaPipe Hand Landmarker Tasks: https://developers.google.com/mediapipe/solutions/vision/hand_landmarker/python
- Python SpeechRecognition Documentation: https://pypi.org/project/SpeechRecognition/
- Python SoundDevice Library: https://python-sounddevice.readthedocs.io/
- OpenCV Python Tutorials: https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html


