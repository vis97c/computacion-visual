# Taller Reconocimiento de Voz Local con OSC

Aplicación interactiva que escucha constantemente el micrófono integrando comandos de voz hacia una interfaz gráfica o enviándolos mediante el protocolo **OSC** hacia otros entornos (como Unity o Processing).

## Requisitos y Preparación

- Python 3.9+
- Micrófono funcional
- **Nota (Windows):** Este proyecto utiliza `sounddevice` para evitar problemas de compatibilidad de `pyaudio` con entornos C++, y usa `pygame-ce` para asegurar compatibilidad total gráfica con nuevas versiones de Python.

## Instalación

1. Navega al directorio python:
   ```bash
   cd python
   ```
2. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Ejecución

```bash
python reconocimiento_voz.py
```

## Comandos de Voz

La aplicación escucha y extrae los comandos clave del discurso:

| Comando Hablado | Interfaz Local (Python) | Envío de Señal OSC | Audio Feedback (pyttsx3) |
|---|---|---|---|
| `"rojo"` / `"azul"` / `"verde"` / `"amarillo"` / `"blanco"` | Cambia el color del cuadrado | `/voz/color [R, G, B]` | Habla confirmando el color |
| `"girar"` o `"gira"` | Pone a girar el cuadrado en su eje | `/voz/girar 1` (u 0 si detiene) | Confirmación por voz de giro |
| `"iniciar"` o `"mover"` | Suelta el cuadrado para que rebote en pantalla | `/voz/mover 1` | "Iniciando movimiento continuo" |
| `"detener"` / `"parar"` | Congela cualquier movimiento (giro y rebote) | `/voz/mover 0` y `/voz/girar 0` | "Sistema detenido" |

> *Para salir de la aplicación, puedes presionar la tecla `ESC` o la 'X' de la ventana.*

## Integración OSC

El proyecto configura un cliente SimpleUDPClient de protocolo OSC (`python-osc`) por el puerto local de red.  
Esto significa que si abres un sketch en Processing o Unity escuchando en `127.0.0.1:5005`, recibirás los patrones descritos en la tabla directamente cuando hables, logrando comandar una escena entera de un motor gráfico mediante Python.

## Características Técnicas

- **SpeechRecognition con Google Backend:** Sistema `sounddevice` que graba fragmentos de 3 segundos enviando audios en memoria (`sr.AudioData`) directo a Google Speech.
- **Multihilo Paralelizado:**
  - `VoiceListener`: Captura y reconoce la voz asíncronamente (evitando frenar FPS estéticos).
  - `TTSActor`: Encola dictados y los expone mediante PyTTSx3, garantizando que el juego no se cuelgue mientras la máquina de TTS del sistema habla.
  - `PyGame Loop`: Mantiene física matemática para rotar la figura gráfica a 60 FPS fijos reflejando el estado de oscilación.
