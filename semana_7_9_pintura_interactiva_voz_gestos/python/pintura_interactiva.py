"""
Pintura Interactiva con Voz y Gestos
=====================================
Detecta gestos de mano con MediaPipe y comandos de voz con SpeechRecognition
para pintar en un lienzo digital en tiempo real.

Controles:
  - Dedo índice levantado (solo):  Pintar con pincel fino
  - Palma abierta (5 dedos):       Pintar con pincel grueso
  - Puño cerrado (0 dedos):        No pintar (mover sin trazo)
  - Voz "rojo":                    Cambiar color a rojo
  - Voz "verde":                   Cambiar color a verde
  - Voz "azul":                    Cambiar color a azul
  - Voz "amarillo":                Cambiar color a amarillo
  - Voz "blanco":                  Cambiar color a blanco
  - Voz "morado":                  Cambiar color a morado
  - Voz "naranja":                 Cambiar color a naranja
  - Voz "rosa":                    Cambiar color a rosa
  - Voz "cyan":                    Cambiar color a cyan
  - Voz "pincel":                  Alternar entre pincel fino y grueso
  - Voz "limpiar" / "borrar":      Limpiar el lienzo
  - Voz "guardar" / "salvar":      Guardar la obra como imagen
  Teclado:
  - 'c':  Limpiar lienzo
  - 's':  Guardar imagen
  - 'q':  Salir
"""

import cv2
import numpy as np
import mediapipe as mp
import speech_recognition as sr
import threading
import time
import os
from datetime import datetime


# ──────────────────────────────────────────────
#  Configuración global
# ──────────────────────────────────────────────
CANVAS_WIDTH = 1280
CANVAS_HEIGHT = 720

# Paleta de colores (BGR para OpenCV)
COLORS = {
    "rojo":     (60, 60, 230),
    "verde":    (80, 200, 80),
    "azul":     (230, 140, 60),
    "amarillo": (50, 220, 240),
    "blanco":   (240, 240, 240),
    "morado":   (200, 80, 180),
    "naranja":  (50, 140, 255),
    "rosa":     (180, 120, 230),
    "cyan":     (220, 200, 60),
}

# Colores de UI
BG_DARK      = (30, 30, 35)
PANEL_BG     = (42, 42, 50)
TEXT_WHITE    = (230, 230, 235)
TEXT_DIM      = (140, 140, 150)
ACCENT_GLOW  = (200, 120, 60)     # Azulado brillante en BGR
BORDER_COLOR = (70, 70, 80)

# Pinceles
BRUSH_THIN  = 4
BRUSH_THICK = 18
BRUSH_ROUND = "round"
BRUSH_SQUARE = "square"


class VoiceListener:
    """Hilo de escucha de voz en segundo plano usando sounddevice."""

    SAMPLE_RATE = 16000   # Hz – suficiente para voz
    CHANNELS = 1
    CHUNK_SECONDS = 3     # Duración de cada fragmento de escucha

    def __init__(self):
        import sounddevice as sd  # noqa: F811

        self.sd = sd
        self.recognizer = sr.Recognizer()
        self.last_command = ""
        self.command_time = 0
        self.running = True
        self._lock = threading.Lock()

        # Verificar que hay dispositivo de entrada
        try:
            dev_info = sd.query_devices(kind='input')
            print(f"[VOZ] Micrófono detectado: {dev_info['name']}")
        except Exception as e:
            raise RuntimeError(f"No se encontró micrófono: {e}")

        print("[VOZ] Listo para escuchar comandos")

        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def _record_chunk(self):
        """Graba un fragmento de audio con sounddevice."""
        num_frames = int(self.SAMPLE_RATE * self.CHUNK_SECONDS)
        audio_np = self.sd.rec(
            num_frames,
            samplerate=self.SAMPLE_RATE,
            channels=self.CHANNELS,
            dtype='int16',
            blocking=True,
        )
        return audio_np

    def _listen_loop(self):
        """Bucle continuo de escucha."""
        while self.running:
            try:
                audio_np = self._record_chunk()
                # Convertir a bytes para SpeechRecognition
                audio_bytes = audio_np.tobytes()
                audio_data = sr.AudioData(audio_bytes, self.SAMPLE_RATE, 2)  # 2 bytes/sample (int16)

                text = self.recognizer.recognize_google(audio_data, language="es-ES").lower().strip()
                print(f"[VOZ] Reconocido: '{text}'")
                with self._lock:
                    self.last_command = text
                    self.command_time = time.time()
            except sr.UnknownValueError:
                pass
            except sr.RequestError as e:
                print(f"[VOZ] Error de servicio: {e}")
                time.sleep(2)
            except Exception:
                pass

    def get_command(self):
        """Devuelve el último comando si es reciente (< 3s)."""
        with self._lock:
            if time.time() - self.command_time < 3:
                cmd = self.last_command
                self.last_command = ""
                return cmd
        return ""

    def stop(self):
        self.running = False


class GestureDetector:
    """Detecta gestos de mano usando MediaPipe HandLandmarker (Tasks API)."""

    # Conexiones de la mano para dibujo manual
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Pulgar
        (0, 5), (5, 6), (6, 7), (7, 8),        # Índice
        (0, 9), (9, 10), (10, 11), (11, 12),   # Medio
        (0, 13), (13, 14), (14, 15), (15, 16), # Anular
        (0, 17), (17, 18), (18, 19), (19, 20), # Meñique
        (5, 9), (9, 13), (13, 17),              # Palma
    ]

    def __init__(self):
        vision = mp.tasks.vision
        base_opts = mp.tasks.BaseOptions

        # Ruta al modelo descargado
        model_path = os.path.join(os.path.dirname(__file__), "hand_landmarker.task")
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Modelo no encontrado: {model_path}\n"
                "Descárgalo de: https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
            )

        options = vision.HandLandmarkerOptions(
            base_options=base_opts(model_asset_path=model_path),
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.7,
            min_hand_presence_confidence=0.6,
            min_tracking_confidence=0.6,
        )
        self.detector = vision.HandLandmarker.create_from_options(options)

    def process(self, frame):
        """Procesa un frame y retorna (landmarks_list, num_dedos_levantados, posición_indice)."""
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        results = self.detector.detect(mp_image)

        index_pos = None
        finger_count = 0
        landmarks_list = None

        if results.hand_landmarks:
            hand = results.hand_landmarks[0]  # Lista de NormalizedLandmark
            landmarks_list = hand
            h, w, _ = frame.shape

            # Obtener posición del dedo índice (punta = landmark 8)
            ix = int(hand[8].x * w)
            iy = int(hand[8].y * h)
            index_pos = (ix, iy)

            # Contar dedos levantados
            finger_count = self._count_fingers(hand)

        return landmarks_list, finger_count, index_pos

    def _count_fingers(self, hand):
        """Cuenta cuántos dedos están levantados."""
        tips = [4, 8, 12, 16, 20]     # Puntas de cada dedo
        pips = [3, 6, 10, 14, 18]     # Articulaciones PIP / IP

        count = 0

        # Pulgar: comparar posición x (tip vs ip) relativo a la muñeca
        wrist_x = hand[0].x
        thumb_tip_x = hand[4].x
        thumb_ip_x = hand[3].x
        if abs(thumb_tip_x - wrist_x) > abs(thumb_ip_x - wrist_x):
            count += 1

        # Demás dedos: punta más arriba (menor y) que PIP
        for tip, pip in zip(tips[1:], pips[1:]):
            if hand[tip].y < hand[pip].y:
                count += 1

        return count

    def draw_landmarks(self, frame, landmarks_list):
        """Dibuja los landmarks de la mano sobre el frame manualmente."""
        if not landmarks_list:
            return

        h, w, _ = frame.shape
        # Dibujar conexiones
        for start_idx, end_idx in self.HAND_CONNECTIONS:
            x1 = int(landmarks_list[start_idx].x * w)
            y1 = int(landmarks_list[start_idx].y * h)
            x2 = int(landmarks_list[end_idx].x * w)
            y2 = int(landmarks_list[end_idx].y * h)
            cv2.line(frame, (x1, y1), (x2, y2), (100, 100, 110), 1, cv2.LINE_AA)

        # Dibujar puntos
        for lm in landmarks_list:
            cx = int(lm.x * w)
            cy = int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, (200, 120, 60), -1, cv2.LINE_AA)

    def close(self):
        self.detector.close()


class InteractivePainter:
    """Aplicación principal de pintura interactiva."""

    def __init__(self):
        # Canvas de dibujo (fondo negro transparente — solo el dibujo)
        self.canvas = np.zeros((CANVAS_HEIGHT, CANVAS_WIDTH, 3), dtype=np.uint8)
        self.prev_pos = None

        # Estado del pincel
        self.color_name = "azul"
        self.color = COLORS["azul"]
        self.brush_size = BRUSH_THIN
        self.brush_shape = BRUSH_ROUND

        # Retroalimentación visual
        self.feedback_text = ""
        self.feedback_time = 0
        self.feedback_color = TEXT_WHITE

        # Historial de trazos para undo (opcional)
        self.stroke_count = 0

        # Componentes
        self.gesture = GestureDetector()
        print("[SISTEMA] Iniciando reconocimiento de voz...")
        try:
            self.voice = VoiceListener()
            self.voice_enabled = True
        except Exception as e:
            print(f"[SISTEMA] No se pudo iniciar el micrófono: {e}")
            print("[SISTEMA] Continuando sin reconocimiento de voz.")
            self.voice = None
            self.voice_enabled = False

        # Cámara
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CANVAS_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CANVAS_HEIGHT)

        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara.")

        print("[SISTEMA] Cámara abierta correctamente")
        print("[SISTEMA] Presiona 'q' para salir, 'c' para limpiar, 's' para guardar")

    # ── Retroalimentación ──

    def _set_feedback(self, text, color=None):
        """Establece un mensaje de retroalimentación temporal."""
        self.feedback_text = text
        self.feedback_time = time.time()
        self.feedback_color = color or TEXT_WHITE

    # ── Comandos de voz ──

    def _process_voice(self):
        """Procesa el último comando de voz."""
        if not self.voice_enabled:
            return

        cmd = self.voice.get_command()
        if not cmd:
            return

        # Colores
        for color_name, color_bgr in COLORS.items():
            if color_name in cmd:
                self.color_name = color_name
                self.color = color_bgr
                self._set_feedback(f"Color: {color_name.upper()}", color_bgr)
                return

        # Acciones
        if "pincel" in cmd or "brocha" in cmd:
            if self.brush_size == BRUSH_THIN:
                self.brush_size = BRUSH_THICK
                self._set_feedback("Pincel GRUESO", ACCENT_GLOW)
            else:
                self.brush_size = BRUSH_THIN
                self._set_feedback("Pincel FINO", ACCENT_GLOW)
            return

        if "limpiar" in cmd or "borrar" in cmd or "limpia" in cmd:
            self.canvas[:] = 0
            self.prev_pos = None
            self.stroke_count = 0
            self._set_feedback("Lienzo LIMPIADO", (80, 80, 230))
            return

        if "guardar" in cmd or "salvar" in cmd or "guarda" in cmd:
            self._save_canvas()
            return

    # ── Dibujo ──

    def _draw_stroke(self, pos, finger_count):
        """Dibuja un trazo en el lienzo según la posición y el gesto."""
        if finger_count == 0:
            # Puño cerrado: no dibujar, resetear posición previa
            self.prev_pos = None
            return

        # Determinar tamaño y forma según gesto
        if finger_count >= 5:
            # Palma abierta: pincel grueso cuadrado
            size = BRUSH_THICK
            shape = BRUSH_SQUARE
        elif finger_count == 1:
            # Solo índice: pincel fino redondo
            size = self.brush_size
            shape = BRUSH_ROUND
        elif finger_count == 2:
            # Dos dedos: pincel mediano
            size = (BRUSH_THIN + BRUSH_THICK) // 2
            shape = BRUSH_ROUND
        else:
            size = self.brush_size
            shape = self.brush_shape

        if self.prev_pos is not None:
            if shape == BRUSH_ROUND:
                cv2.line(self.canvas, self.prev_pos, pos, self.color, size,
                         lineType=cv2.LINE_AA)
            else:
                # Pincel cuadrado: dibujar rectángulos a lo largo de la línea
                self._draw_square_line(self.prev_pos, pos, size)
        else:
            # Primer punto
            if shape == BRUSH_ROUND:
                cv2.circle(self.canvas, pos, size // 2, self.color, -1,
                           lineType=cv2.LINE_AA)
            else:
                half = size // 2
                cv2.rectangle(self.canvas,
                              (pos[0] - half, pos[1] - half),
                              (pos[0] + half, pos[1] + half),
                              self.color, -1)

        self.prev_pos = pos
        self.stroke_count += 1

    def _draw_square_line(self, p1, p2, size):
        """Dibuja una línea usando rectángulos (pincel cuadrado)."""
        dist = max(1, int(np.hypot(p2[0] - p1[0], p2[1] - p1[1])))
        half = size // 2
        for i in range(0, dist, max(1, size // 3)):
            t = i / dist
            x = int(p1[0] + t * (p2[0] - p1[0]))
            y = int(p1[1] + t * (p2[1] - p1[1]))
            cv2.rectangle(self.canvas,
                          (x - half, y - half),
                          (x + half, y + half),
                          self.color, -1)

    # ── Guardar ──

    def _save_canvas(self):
        """Guarda el lienzo como imagen PNG."""
        output_dir = os.path.join(os.path.dirname(__file__), "obras")
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(output_dir, f"pintura_{timestamp}.png")
        cv2.imwrite(filename, self.canvas)
        self._set_feedback(f"Guardado: pintura_{timestamp}.png", (80, 200, 80))
        print(f"[SISTEMA] Imagen guardada: {filename}")

    # ── UI / HUD ──

    def _draw_hud(self, frame, finger_count, index_pos):
        """Dibuja la interfaz superpuesta sobre el frame."""
        h, w = frame.shape[:2]

        # ── Panel lateral izquierdo (paleta de colores) ──
        panel_w = 60
        panel_x = 10
        panel_y = 10
        panel_h = len(COLORS) * 45 + 20

        # Fondo del panel con transparencia
        overlay = frame.copy()
        cv2.rectangle(overlay, (panel_x, panel_y),
                      (panel_x + panel_w, panel_y + panel_h),
                      PANEL_BG, -1)
        cv2.rectangle(overlay, (panel_x, panel_y),
                      (panel_x + panel_w, panel_y + panel_h),
                      BORDER_COLOR, 1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

        # Muestras de color
        for i, (name, bgr) in enumerate(COLORS.items()):
            cy = panel_y + 25 + i * 45
            cx = panel_x + panel_w // 2
            radius = 15

            # Indicador de selección
            if name == self.color_name:
                cv2.circle(frame, (cx, cy), radius + 5, ACCENT_GLOW, 2,
                           lineType=cv2.LINE_AA)

            cv2.circle(frame, (cx, cy), radius, bgr, -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (cx, cy), radius, (80, 80, 90), 1,
                       lineType=cv2.LINE_AA)

        # ── Panel superior (info actual) ──
        info_panel_w = 450
        info_panel_h = 50
        info_x = (w - info_panel_w) // 2
        info_y = 8

        overlay2 = frame.copy()
        cv2.rectangle(overlay2, (info_x, info_y),
                      (info_x + info_panel_w, info_y + info_panel_h),
                      PANEL_BG, -1, lineType=cv2.LINE_AA)
        # Bordes redondeados simulados con líneas
        cv2.rectangle(overlay2, (info_x, info_y),
                      (info_x + info_panel_w, info_y + info_panel_h),
                      BORDER_COLOR, 1)
        cv2.addWeighted(overlay2, 0.65, frame, 0.35, 0, frame)

        # Texto del estado
        brush_label = "GRUESO" if self.brush_size == BRUSH_THICK else "FINO"
        gesture_label = self._get_gesture_label(finger_count)
        status = f"Color: {self.color_name.upper()}  |  Pincel: {brush_label}  |  {gesture_label}"

        # Muestra del color actual al lado del texto
        cv2.circle(frame, (info_x + 18, info_y + info_panel_h // 2),
                   8, self.color, -1, lineType=cv2.LINE_AA)

        cv2.putText(frame, status,
                    (info_x + 35, info_y + 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, TEXT_WHITE, 1,
                    cv2.LINE_AA)

        # ── Retroalimentación de comando ──
        if self.feedback_text and (time.time() - self.feedback_time < 2.5):
            alpha = max(0, 1.0 - (time.time() - self.feedback_time) / 2.5)
            fb_color = tuple(int(c * alpha) for c in self.feedback_color)

            # Fondo del mensaje
            text_size = cv2.getTextSize(self.feedback_text,
                                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)[0]
            fb_x = (w - text_size[0]) // 2
            fb_y = h - 80

            overlay3 = frame.copy()
            pad = 15
            cv2.rectangle(overlay3,
                          (fb_x - pad, fb_y - text_size[1] - pad),
                          (fb_x + text_size[0] + pad, fb_y + pad),
                          PANEL_BG, -1)
            cv2.addWeighted(overlay3, 0.6 * alpha, frame, 1 - 0.6 * alpha, 0,
                            frame)

            cv2.putText(frame, self.feedback_text,
                        (fb_x, fb_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, fb_color, 2,
                        cv2.LINE_AA)

        # ── Cursor del pincel ──
        if index_pos:
            if finger_count >= 5:
                half = BRUSH_THICK // 2
                cv2.rectangle(frame,
                              (index_pos[0] - half, index_pos[1] - half),
                              (index_pos[0] + half, index_pos[1] + half),
                              self.color, 2, lineType=cv2.LINE_AA)
            elif finger_count >= 1:
                cv2.circle(frame, index_pos, self.brush_size + 4,
                           self.color, 2, lineType=cv2.LINE_AA)
                cv2.circle(frame, index_pos, 2,
                           (255, 255, 255), -1, lineType=cv2.LINE_AA)

        # ── Indicador de voz ──
        mic_x = w - 50
        mic_y = 35
        mic_color = (80, 200, 80) if self.voice_enabled else (80, 80, 200)
        cv2.circle(frame, (mic_x, mic_y), 12, mic_color, -1,
                   lineType=cv2.LINE_AA)
        cv2.putText(frame, "MIC", (mic_x - 14, mic_y + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, TEXT_WHITE, 1,
                    cv2.LINE_AA)

        # ── Instrucciones (esquina inferior derecha) ──
        instructions = [
            "Q: Salir  |  C: Limpiar  |  S: Guardar",
            "Voz: rojo, verde, azul, pincel, limpiar, guardar",
        ]
        for i, txt in enumerate(instructions):
            ty = h - 15 - (len(instructions) - 1 - i) * 22
            cv2.putText(frame, txt, (10, ty),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.42, TEXT_DIM, 1,
                        cv2.LINE_AA)

    def _get_gesture_label(self, finger_count):
        """Devuelve una etiqueta legible del gesto actual."""
        if finger_count == 0:
            return "Gesto: PAUSA"
        elif finger_count == 1:
            return "Gesto: PINCEL FINO"
        elif finger_count == 2:
            return "Gesto: PINCEL MEDIO"
        elif finger_count >= 5:
            return "Gesto: PALMA (grueso)"
        else:
            return f"Gesto: {finger_count} dedos"

    # ── Bucle principal ──

    def run(self):
        """Bucle principal de la aplicación."""
        cv2.namedWindow("Pintura Interactiva", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Pintura Interactiva", CANVAS_WIDTH, CANVAS_HEIGHT)

        while True:
            ret, frame = self.cap.read()
            if not ret:
                print("[ERROR] No se pudo leer frame de la cámara.")
                break

            # Espejo horizontal para experiencia más natural
            frame = cv2.flip(frame, 1)

            # Redimensionar al tamaño del canvas
            frame = cv2.resize(frame, (CANVAS_WIDTH, CANVAS_HEIGHT))

            # ── Detectar gestos ──
            landmarks, finger_count, index_pos = self.gesture.process(frame)

            # ── Procesar voz ──
            self._process_voice()

            # ── Dibujar trazo ──
            if index_pos and finger_count > 0:
                self._draw_stroke(index_pos, finger_count)
            else:
                self.prev_pos = None

            # ── Componer: frame + canvas ──
            # Crear máscara donde el canvas tiene contenido
            gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
            _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

            # Oscurecer ligeramente el frame de la cámara
            display = (frame * 0.55).astype(np.uint8)

            # Superponer el dibujo
            display[mask > 0] = self.canvas[mask > 0]

            # ── Dibujar landmarks de la mano ──
            self.gesture.draw_landmarks(display, landmarks)

            # ── HUD ──
            self._draw_hud(display, finger_count, index_pos)

            # ── Mostrar ──
            cv2.imshow("Pintura Interactiva", display)

            # ── Teclado ──
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.canvas[:] = 0
                self.prev_pos = None
                self.stroke_count = 0
                self._set_feedback("Lienzo LIMPIADO", (80, 80, 230))
            elif key == ord('s'):
                self._save_canvas()

        self._cleanup()

    def _cleanup(self):
        """Libera recursos."""
        print("[SISTEMA] Cerrando aplicación...")
        if self.voice:
            self.voice.stop()
        self.gesture.close()
        self.cap.release()
        cv2.destroyAllWindows()
        print("[SISTEMA] ¡Adiós!")


# ──────────────────────────────────────────────
#  Punto de entrada
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 55)
    print("  PINTURA INTERACTIVA CON VOZ Y GESTOS")
    print("=" * 55)
    print()

    app = InteractivePainter()
    app.run()
