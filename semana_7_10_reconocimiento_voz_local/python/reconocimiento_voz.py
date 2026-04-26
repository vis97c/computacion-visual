
"""
Reconocimiento de Voz Local (Ejecución Local con Micrófono)
===========================================================
Captura comandos de voz mediante Speech Recognition + SoundDevice.
- Interpreta comandos ("rojo", "azul", "girar", "iniciar", "detener").
- Reacciona en el canvas gráfico construido con PyGame.
- Envía información por OSC hacia Unity/Processing.
- Retroalimentación auditiva usando pyttsx3.
"""

import pygame
import pyttsx3
import speech_recognition as sr
import sounddevice as sd
import threading
import time
import queue
from pythonosc import udp_client

# -- Configuración Global --
OSC_IP = "127.0.0.1"
OSC_PORT = 5005

COLORS = {
    "rojo": (255, 50, 50),
    "azul": (50, 100, 255),
    "verde": (50, 255, 100),
    "blanco": (240, 240, 240),
    "amarillo": (255, 255, 50)
}

class TTSActor:
    """Hilo de ejecución para Text-to-Speech (PyTTSx3).
    Evita bloquear el hilo principal de Pygame cuando la voz está hablando."""
    def __init__(self):
        self.q = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def say(self, text):
        self.q.put(text)
        
    def _run(self):
        engine = pyttsx3.init()
        engine.setProperty('rate', 160)
        
        # Intentar localizar e instalar una voz en español
        voices = engine.getProperty('voices')
        for v in voices:
            if "es" in v.languages or "spanish" in v.name.lower() or "ES" in v.id:
                engine.setProperty('voice', v.id)
                break
                
        while self.running:
            try:
                text = self.q.get(timeout=0.5)
                engine.say(text)
                engine.runAndWait()
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[TTS Error] {e}")
                
    def stop(self):
        self.running = False


class VoiceListener:
    """Hilo para escucha constante en segundo plano. Usa SoundDevice."""
    SAMPLE_RATE = 16000
    CHANNELS = 1
    CHUNK_SECONDS = 3

    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.cmd_queue = queue.Queue()
        self.running = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def _record_chunk(self):
        num_frames = int(self.SAMPLE_RATE * self.CHUNK_SECONDS)
        audio_np = sd.rec(
            num_frames,
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype='int16',
            blocking=True,
        )
        return audio_np

    def _listen_loop(self):
        while self.running:
            try:
                audio_np = self._record_chunk()
                audio_bytes = audio_np.tobytes()
                audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, 2)
                
                # Reconocer mediante Google Speech (puedes cambiar a Sphinx para totalmente offline)
                text = self.recognizer.recognize_google(audio_data, language="es-ES").lower().strip()
                print(f"[VOZ] Capturado: '{text}'")
                
                # Enviar todas las palabras como posibles comandos
                words = text.split()
                for w in words:
                    self.cmd_queue.put(w)
                    
            except sr.UnknownValueError:
                pass # Silencio o ruido irreconocible
            except sr.RequestError as e:
                print(f"[VOZ] Fallo el servicio: {e}")
                time.sleep(2)
            except Exception:
                pass
                
    def get_commands(self):
        cmds = []
        while not self.cmd_queue.empty():
            cmds.append(self.cmd_queue.get())
        return cmds

    def stop(self):
        self.running = False


def main():
    print("="*60)
    print("   Iniciando Reconocimiento de Voz Local (Con Interfaz)")
    print("="*60)
    
    # Inicializar cliente OSC
    osc_client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)
    print(f"[OSC] Cliente registrado apuntando a {OSC_IP}:{OSC_PORT}")
    
    pygame.init()
    width, height = 800, 600
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Visualizador de Comandos de Voz")
    clock = pygame.time.Clock()
    
    font_large = pygame.font.SysFont("Arial", 36, bold=True)
    font_small = pygame.font.SysFont("Arial", 20)
    
    tts = TTSActor()
    
    try:
        voice = VoiceListener()
    except Exception as e:
        print(f"[ERROR] No se pudo inicializar micrófono: {e}")
        return
        
    print("[SISTEMA] Sistema iniciado.")
    tts.say("Módulo de reconocimiento de voz encendido.")
    
    # Estados del visualizador
    color_actual = COLORS["blanco"]
    osc_client.send_message("/voz/color", [color_actual[0], color_actual[1], color_actual[2]])
    girando = False
    moviendo = False
    angulo = 0
    pos_x, pos_y = width//2, height//2
    vel_x, vel_y = 5, 5
    
    mensaje_ui = "Di un comando..."
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
        # Consumir y analizar los comandos en la cola de voz
        comandos = voice.get_commands()
        for c in comandos:
            c = c.replace(',', '').replace('.', '') # sanitizar
            if c in COLORS:
                color_actual = COLORS[c]
                mensaje_ui = f"Cambiado a color {c}"
                tts.say(f"Color {c}")
                osc_client.send_message("/voz/color", [color_actual[0], color_actual[1], color_actual[2]])
            
            elif c == "girar" or c == "gira":
                girando = not girando
                estado = "girando" if girando else "rotación detenida"
                mensaje_ui = f"Estado: {estado}"
                tts.say("Girando" if girando else "Rotación detenida")
                osc_client.send_message("/voz/girar", 1 if girando else 0)
                
            elif c == "iniciar" or c == "inicia" or c == "mover":
                moviendo = True
                mensaje_ui = "Estado: En movimiento"
                tts.say("Iniciando movimiento continuo")
                osc_client.send_message("/voz/mover", 1)
                
            elif c == "detener" or c == "detén" or c == "parar":
                moviendo = False
                girando = False
                mensaje_ui = "Estado: Detenido totalmente"
                tts.say("Sistema detenido")
                osc_client.send_message("/voz/mover", 0)
                osc_client.send_message("/voz/girar", 0)

        # Actualizar físicas
        if girando:
            angulo = (angulo + 3) % 360
            
        if moviendo:
            pos_x += vel_x
            pos_y += vel_y
            if pos_x < 50 or pos_x > width-50: vel_x *= -1
            if pos_y < 50 or pos_y > height-50: vel_y *= -1
            
        # Dibujar Fondo
        screen.fill((35, 35, 40))
        
        # Figura interactiva
        rect_surf = pygame.Surface((120, 120), pygame.SRCALPHA)
        rect_surf.fill(color_actual)
        
        # Rotar y acomodar centro
        rotated_surf = pygame.transform.rotate(rect_surf, angulo)
        rotated_rect = rotated_surf.get_rect(center=(pos_x, pos_y))
        
        # Borde brillante
        pygame.draw.rect(screen, (255,255,255), rotated_rect.inflate(6,6), border_radius=4)
        screen.blit(rotated_surf, rotated_rect)
        
        # Textos de UI
        text_surf = font_large.render(mensaje_ui, True, (240, 240, 240))
        screen.blit(text_surf, (20, 20))
        
        status_osc = font_small.render(f"OSC Emitiendo en: udp://{OSC_IP}:{OSC_PORT}", True, (120, 180, 120))
        screen.blit(status_osc, (20, 60))
        
        # Pie de página con los comandos
        panel = pygame.Surface((width, 40), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        screen.blit(panel, (0, height-40))
        
        comandos_str = "COMANDOS PERMITIDOS: rojo, azul, verde, amarillo, blanco, girar, iniciar, detener"
        instrucciones = font_small.render(comandos_str, True, (200, 200, 200))
        screen.blit(instrucciones, (15, height-30))
        
        # Refrescar Pantalla
        pygame.display.flip()
        clock.tick(60)
        
    print("[SISTEMA] Cerrando motores...")
    voice.stop()
    tts.stop()
    pygame.quit()

if __name__ == "__main__":
    main()
