# Taller Reconocimiento de Voz Local con OSC

## Nombres de los estudiantes

Victor Saa, Juan Jose Alvarez, Juan Pablo Correa, Jose Arturo Herrera Rivera, Manuel Santiago Mori Ardila

## Fecha de entrega

`2026-04-25`

---

## Descripción breve

Este taller implementa un sistema interactivo centrado puramente en comandos de voz (Natural Language Processing y comandos de audio locales) como mecanismo de interacción, superando los controladores de teclado y ratón tradicionales. La aplicación escucha, interpreta, grafica localmente y exporta vía red las órdenes del usuario.

Se empleó **SpeechRecognition (API Offline/Online según backend)** acoplado de forma nativa a **SoundDevice** para evitar las caídas clásicas de PyAudio. El entorno dibuja gráficos reaccionales con **PyGame-ce** y mantiene de manera transparente un hilo de notificación auditiva dictada por una voz robótica gracias a **PyTTSx3**. Adicionalmente, el sistema no está encerrado en Python, ya que cada comando detectado y aprobado se serializa y emite ininterrumpidamente a través del protocolo **OSC** vía UDP por el puerto 5005, logrando comandar una escena entera de un motor gráfico tercero mediante red local y permitiendo que un proyecto de Processing o Unity adquiera controles de voz sin cargar el peso lógico computacional de STT (Speech To Text).

---

## Implementaciones

### Python y PyGame-ce

El entorno visual de validación local se levanta sobre PyGame-ce, proveyendo un Canvas estático a 60 FPS donde se manipulan lógicas de colisión, rebote matemático y rotación del objeto en base a boleanos de estado controlados exclusivamente por la voz (Ej: `girando=True`, `moviendo=False`).

### Speech Recognition + SoundDevice (Captura por Chunks)

Para evitar que el la escucha del micrófono bloquee el FPS de renderizado o la física del rebote, se encapsuló un método en `VoiceListener` ejecutándose en un hilo como daemon de Python. Este extrae la cinta de audio de la tarjeta de sonido por medio de matrices de bytes *Int16*, entregándolos a SpeechRecognition. La ventaja aquí fue parsear las oraciones enteras que se hablan (`"verde girar iniciar"`) y dividirlas con una tokenización sencilla, guardándolas en una cola Thread-Safe (`queue.Queue()`) de la que el script de lectura despacha.

### Retroalimentación de Voz: Text-To-Speech (TTSActor)

Cada vez que se interpreta de forma fehaciente una orden ("rojo"), no solo cambia un color, la computadora debe notificar de vuelta la asimilación del comando sin trabar la interfaz. Esto lo administra la librería nativa multiplataforma **PyTTSx3** seleccionando la voz española ("ES") del motor SAPI5 / NSSpeechSynthesizer montado también en una pequeña `Queue` de consumidor/productor aislada.

### Serialización UDP por OSC (Open Sound Control)

Haciendo uso de la librería estándar `python-osc`, la arquitectura declara un `SimpleUDPClient` y convierte lógicas de estado en bytes directos. "Rojo" equivale a despachar por la ruta `/voz/color` una lista de floats `[255.0, 50.0, 50.0]`. Esto significa que si Unity escucha en esa variable OSC, los tonos de Unity empatarían perfectamente los de la consola de Python. Un giro emite `/voz/girar 1` de la misma manera intuitiva.

---

## Resultados visuales

### Pila de Aplicación Visual y Estados

![Funcionamiento general](./media/funcionamiento.gif)

 Muestra el funcionamiento de la app en general, probando los distintos comandos.


---

## Código relevante

### Reconocimiento de Voz Limpio y Encolamiento Asíncrono

```python
def _listen_loop(self):
    while self.running:
        try:
            # Bypass PyAudio usando SoundDevice Int16 array recording
            audio_np = self._record_chunk()
            audio_bytes = audio_np.tobytes()
            audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, 2)
            
            # STT Processing
            text = self.recognizer.recognize_google(audio_data, language="es-ES").lower().strip()
            
            # Divisor de múltiples comandos por oración y uso de Queue
            words = text.split()
            for w in words:
                self.cmd_queue.put(w)
                
        except sr.UnknownValueError:
            pass # Silencio
```

### Motor TTS No Bloqueante en Hilo Daemonizado

```python
def _run(self):
    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    # Selecciona la mejor voz robótica local que soporte "es"
    for v in engine.getProperty('voices'):
        if "es" in v.languages or "spanish" in v.name.lower():
            engine.setProperty('voice', v.id)
            break
            
    while self.running:
        try:
            text = self.q.get(timeout=0.5)
            engine.say(text)
            engine.runAndWait() # Esto traba su propio hilo, pero no la UI ni la cámara 
        except queue.Empty:
            pass
```

### Traducción de Comandos y Emisión OSC en Bucle Principal

```python
for c in comandos:
    c = c.replace(',', '').replace('.', '') # sanitizar
    if c in COLORS:
        color_actual = COLORS[c]
        mensaje_ui = f"Cambiado a color {c}"
        tts.say(f"Color {c}")
        osc_client.send_message("/voz/color", [color_actual[0], color_actual[1], color_actual[2]])
    
    elif c == "girar" or c == "gira":
        girando = not girando
        tts.say("Girando" if girando else "Rotación detenida")
        osc_client.send_message("/voz/girar", 1 if girando else 0)
```

---

## Diagrama de Flujo del Programa

```
                         ┌───── Micrófono Central ──────┐
                         │                              │
                  ┌──────▼───────┐              ┌───────┴────────┐
                  │ VoiceListener│              │    TTSActor    │
                  │ (Hilo 2 STT) │              │  (Hilo 3 Voz)  │
                  └──────┬───────┘              └───────▲────────┘
                         │ cola de strings              │ lee en UI
                "verde", "girar", "iniciar"     ( "Color Verde", "Girando",... )
                         │                              │
                         └───────────┬──────────────────┘
                                     │
                             ┌───────▼────────┐
                             │ PYGAME EVENT   │ 
                             │ LOOP PRINCIPAL │
                             └───────┬────────┘
                                     │
                    ┌────────────────┴──────────────────┐
                    │                                   │
            ┌───────▼────────┐                  ┌───────▼────────┐
            │   OSC CLIENT   │                  │ GRAPHICS REND  │
            │ python-osc UDP │                  │ UI PyGame      │
            └───────┬────────┘                  └───────┬────────┘
                    │                                   │
    /voz/color 50.0 255.0 50.0            (Dibuja Cuadrado, actualiza Pos)
    /voz/girar 1                                (Update Angular)
                    │                                   │
            ┌───────▼───────────┐               ┌───────▼────────┐
            │ UNITY/PROCESSING  │               │ PC DE USUARIO  │
            └───────────────────┘               └────────────────┘
```

---

## Prompts utilizados

```
"Escribe un módulo local de Python que grabe el micrófono directamente
evitando los crashes habituales de PyAudio usando un fallback con `sounddevice`
de numpy arrays."

"En Python, utilizando pyttsx3 ocurre un gran problema: la llamada a la función
runAndWait() congela cualquier bucle posterior. Construye un hilo robusto con una
queue.Queue en Python nativo para que todos los envíos de lectura de voz se manejen 
separados, esperando una instrucción en loop para que la UI no se rompa."

"Levántame un servidor simple y liviano llamado receptor_osc.py utilizando python-osc.
En ese servidor inicializa un Dispatcher atrapalotodo que imprima en consola de Python
las URL que el Unity o Processing se supone iban a recibir, comprobando las comunicaciones."
```

---

## Aprendizajes y dificultades

### Aprendizajes

La programación con sistemas interconectados (OSC, NLP, Gráficas y TTS al mismo tiempo) dejó como aprendizaje esencial la arquitectura de colas mutuas en Python. Para construir aplicaciones interactivas en tiempo no estático (juegos o físicas reaccionables), llamar funciones de la red nativas en el GameLoop principal termina demudándolo todo. El encapsulamiento vía `Queue` previene bloqueos catastróficos. 

También aprendimos que OSC (Open Sound Control) es un mecanismo ridículamente liviano y efectivo comparado con protocolos grandes como HTTP, Websockets, o Serial JSON para la intercomunicación robusta entre Engine a Engine o Engine a Interfaz. Enviar un array de colores demoraba literales microsegundos.

### Dificultades

**Deprecaciones de instalación de PyAudio (Windows / Python 3.14):** El clásico y ampliamente tutorializado `sr.Microphone` de *SpeechRecognition* funciona internamente atado a PyAudio, cuya compilación requería el Visual Studio Toolchains y los headers C/C++ de un PortAudio arcaico. Tras varios fracasos intentando `pipwin`, logramos reescribir e intervenir la funcionalidad directamente transponiéndolo a un numpy matrix con librerías robustas (`sounddevice`).

**Alineación Modular de PyGame:** Instalando los prerrequisitos en sistemas de vanguardia, `pygame` básico a menudo falla su Build process en Python > 3.12, tuvimos que adaptarnos a la iteración optimizada retrocompatible de la comunidad: `pygame-ce` (Community Edition). El código fuente no cambió nada, demostrándonos lo inter-cambiables que llegan a ser algunas librerías si se buscan los forks apropiados.

---

## Contribuciones grupales

Taller realizado de forma individual.

---

## Estructura del proyecto

```
semana_7_10_reconocimiento_voz_local/
├── python/
│   ├── reconocimiento_voz.py   # Aplicación principal visual (Voice, Pygame, OSC, TTS)
│   ├── receptor_osc.py         # Mock server local útil para loggear envíos por OSC
│   ├── requirements.txt        # Dependencias robustas (Pygame-ce y Sounddevice)
│   └── README.md               # Quickstart del código 
├── media/
│   ├── visualizador_ui.png     # Capturas visuales del bucle gráfico
│   └── receptor_osc.png        # Logs de pruebas del despacho UDP OSC
└── README.md                   # Documentación principal estandarizada de taller
```

---

## Referencias

- Documentación Python-OSC: https://github.com/attwad/python-osc
- Alternativa a Pyaudio: SoundDevice library docs: https://python-sounddevice.readthedocs.io/
- Manejo de Voice Text (Pyttsx3): https://github.com/nateshmbhat/pyttsx3
- Event loops y concurrencia Threading - Python Org: https://docs.python.org/3/library/threading.html
- PyGame-CE Repositorio: https://pyga.me/docs/

---

## Checklist de entrega

- [x] Carpeta con nombre `semana_7_10_reconocimiento_voz_local`
- [x] Scripts limpios y comentados en `python/`
- [x] Creado un Script Adicional Mock Receptor para facilitar correcciones
- [x] README general en formato estandarizado
- [x] Multitreading / Diagrama funcional
- [x] Feedback y Respuestas Auditivas aplicadas (PyTTSx3)
- [x] Sistema reaccional para envío al puerto `5005` (OSC protocol)
- [ ] Incorporar la recepción Unity / Proccesing (opcional extendido)
- [ ] Commits descriptivos en inglés
- [ ] Repositorio organizado y público
