#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taller - Reconocimiento de Postura con MediaPipe
Semana 11.2 - Computacion Visual

Sistema de reconocimiento de acciones corporales que detecta y clasifica
posturas en tiempo real usando analisis de landmarks con MediaPipe Pose.

Acciones detectadas:
  - SENTADO: cadera por debajo o al nivel de las rodillas
  - BRAZOS LEVANTADOS: ambas munecas por encima de la cabeza
  - CAMINANDO: alternancia en la posicion de los pies (paso detectado)

Retroalimentacion multimodal:
  - Visual: colores de estado, borde parpadeante, icono de accion
  - Sonora: tonos diferenciados por accion via pygame.mixer

Soporta fallback automatico a video pregrabado o simulacion sintetica
si no se detecta webcam fisica.
"""

import os
import sys
import time
import math
import datetime
import urllib.request
import numpy as np
import cv2

# MediaPipe para deteccion de pose
try:
    import mediapipe as mp
    # Detectar si estamos usando la nueva Tasks API (obligatoria en Python 3.14+ o cuando solutions esta ausente)
    try:
        from mediapipe.tasks.python import BaseOptions
        from mediapipe.tasks.python.vision import pose_landmarker
        from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode
        # Comprobar si solutions no existe
        if not hasattr(mp, 'solutions') or not hasattr(mp.solutions, 'pose'):
            USE_TASKS_API = True
        else:
            USE_TASKS_API = False
    except ImportError:
        USE_TASKS_API = False
except ImportError:
    print("El paquete 'mediapipe' no esta instalado. Ejecute: pip install mediapipe")
    mp = None
    USE_TASKS_API = False

# Pygame para retroalimentacion sonora
try:
    import pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
    SOUND_AVAILABLE = True
except Exception:
    SOUND_AVAILABLE = False

# ============================================================================
# CONFIGURACION GLOBAL
# ============================================================================

DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 640
HUD_TOP_HEIGHT = 70
HUD_BOTTOM_HEIGHT = 50
HUD_SIDE_WIDTH = 260

# Colores principales del HUD (BGR)
COLOR_BG_DARK = (20, 18, 15)
COLOR_BG_PANEL = (30, 26, 22)
COLOR_ACCENT_CYAN = (210, 170, 40)
COLOR_ACCENT_GREEN = (80, 220, 120)
COLOR_ACCENT_ORANGE = (50, 150, 255)
COLOR_ACCENT_RED = (60, 60, 230)
COLOR_ACCENT_PURPLE = (200, 100, 180)
COLOR_TEXT_PRIMARY = (240, 240, 240)
COLOR_TEXT_SECONDARY = (170, 170, 170)
COLOR_TEXT_DIM = (120, 120, 120)

# Colores por accion detectada
ACTION_COLORS = {
    "SENTADO": (210, 170, 40),        # Cyan/Azulado
    "BRAZOS LEVANTADOS": (50, 200, 50),  # Verde
    "CAMINANDO": (50, 150, 255),      # Naranja
    "NEUTRO": (150, 150, 150),        # Gris
}

# Control de estado
active_filter = "ORIGINAL"
is_paused = False
take_snapshot = False
is_recording = False
exit_flag = False
show_angles = True
show_distances = True
mouse_hover_btn = None
fps_display = 0.0

# Historial de deteccion de pasos para clasificacion de caminata
step_history = []
last_step_time = 0.0
step_count = 0

# Botones interactivos del HUD superior
buttons = [
    {"name": "ORIGINAL", "x1": 15, "y1": 16, "x2": 115, "y2": 52, "type": "filter", "active": True},
    {"name": "GRAY", "x1": 125, "y1": 16, "x2": 205, "y2": 52, "type": "filter", "active": False},
    {"name": "BINARY", "x1": 215, "y1": 16, "x2": 310, "y2": 52, "type": "filter", "active": False},
    {"name": "CANNY", "x1": 320, "y1": 16, "x2": 410, "y2": 52, "type": "filter", "active": False},
    {"name": "PAUSE", "x1": 430, "y1": 16, "x2": 530, "y2": 52, "type": "action", "active": False},
    {"name": "SNAPSHOT", "x1": 540, "y1": 16, "x2": 660, "y2": 52, "type": "action", "active": False},
    {"name": "RECORD", "x1": 670, "y1": 16, "x2": 780, "y2": 52, "type": "action", "active": False},
    {"name": "EXIT", "x1": 850, "y1": 16, "x2": 945, "y2": 52, "type": "action", "active": False},
]


# ============================================================================
# GENERACION DE SONIDOS CON PYGAME (Tonos sinteticos)
# ============================================================================

def generate_tone(frequency, duration_ms=200, volume=0.3):
    """Genera un tono sinusoidal puro como un objeto pygame.mixer.Sound."""
    if not SOUND_AVAILABLE:
        return None
    sample_rate = 44100
    n_samples = int(sample_rate * duration_ms / 1000)
    t = np.linspace(0, duration_ms / 1000, n_samples, endpoint=False)
    # Onda sinusoidal con envolvente suave (fade in/out)
    wave = np.sin(2 * np.pi * frequency * t)
    # Aplicar envolvente de tipo raised cosine para evitar clicks
    fade_len = min(int(n_samples * 0.1), 500)
    envelope = np.ones(n_samples)
    envelope[:fade_len] = np.linspace(0, 1, fade_len)
    envelope[-fade_len:] = np.linspace(1, 0, fade_len)
    wave = wave * envelope * volume
    # Convertir a formato 16-bit signed
    wave_int = np.int16(wave * 32767)
    sound = pygame.sndarray.make_sound(wave_int)
    return sound

# Pre-generar los sonidos de cada accion
sounds = {}
if SOUND_AVAILABLE:
    try:
        sounds["SENTADO"] = generate_tone(440, 250, 0.25)        # La4 - tono medio
        sounds["BRAZOS LEVANTADOS"] = generate_tone(660, 200, 0.3)  # Mi5 - tono agudo
        sounds["CAMINANDO"] = generate_tone(330, 300, 0.2)       # Mi4 - tono grave ritmico
        sounds["CAMBIO"] = generate_tone(880, 100, 0.15)         # La5 - bip de transicion
    except Exception:
        sounds = {}
        SOUND_AVAILABLE = False


# ============================================================================
# UTILIDADES DE CARPETA Y MEDIA
# ============================================================================

def ensure_media_folder():
    """Crea la carpeta media en la ruta correcta si no existe."""
    if os.path.exists("media") or os.path.exists("../media"):
        return
    try:
        os.makedirs("media", exist_ok=True)
    except Exception as e:
        print(f"Error al crear carpeta media: {e}")

def get_media_path(filename):
    """Devuelve la ruta correcta para guardar en la carpeta media."""
    if os.path.exists("../media"):
        return os.path.join("../media", filename)
    elif os.path.exists("media"):
        return os.path.join("media", filename)
    else:
        os.makedirs("media", exist_ok=True)
        return os.path.join("media", filename)

def download_fallback_video():
    """Descarga un video de prueba con personas si no hay webcam."""
    target_path = "people-walking.mp4"
    if os.path.exists(target_path):
        return target_path

    url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/people-detection.mp4"
    print(f"No se detecto webcam fisica. Descargando video de prueba desde:\n{url}")
    print("Espere un momento...")
    try:
        urllib.request.urlretrieve(url, target_path)
        print(f"Video descargado con exito: {target_path}")
        return target_path
    except Exception as e:
        print(f"No se pudo descargar el video: {e}")
        return None


# ============================================================================
# GENERACION SINTETICA (Fallback sin camara ni video)
# ============================================================================

def generate_synthetic_frame(t):
    """Genera un frame sintetico animado como ultimo recurso de fallback."""
    frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
    # Fondo gradiente oscuro
    for y in range(DISPLAY_HEIGHT):
        val = int(25 + (y / DISPLAY_HEIGHT) * 35)
        frame[y, :] = [val, 18, 14]

    # Grid decorativo
    for x in range(0, DISPLAY_WIDTH, 50):
        cv2.line(frame, (x, 0), (x, DISPLAY_HEIGHT), (40, 28, 22), 1)
    for y in range(0, DISPLAY_HEIGHT, 50):
        cv2.line(frame, (0, y), (DISPLAY_WIDTH, y), (40, 28, 22), 1)

    # Silueta humana simplificada animada
    cx = DISPLAY_WIDTH // 2
    cy = DISPLAY_HEIGHT // 2
    # Cabeza
    cv2.circle(frame, (cx, cy - 120), 30, (200, 180, 160), -1)
    # Torso
    cv2.line(frame, (cx, cy - 90), (cx, cy + 20), (200, 180, 160), 4)
    # Brazos (animados)
    arm_angle = math.sin(t * 2) * 0.5
    lx = int(cx - 80 * math.cos(arm_angle))
    ly = int(cy - 40 + 80 * math.sin(arm_angle))
    rx = int(cx + 80 * math.cos(arm_angle))
    ry = int(cy - 40 + 80 * math.sin(arm_angle))
    cv2.line(frame, (cx, cy - 70), (lx, ly), (200, 180, 160), 3)
    cv2.line(frame, (cx, cy - 70), (rx, ry), (200, 180, 160), 3)
    # Piernas
    leg_phase = math.sin(t * 3) * 30
    cv2.line(frame, (cx, cy + 20), (cx - 40 + int(leg_phase), cy + 130), (200, 180, 160), 3)
    cv2.line(frame, (cx, cy + 20), (cx + 40 - int(leg_phase), cy + 130), (200, 180, 160), 3)

    cv2.putText(frame, "SIMULACION SINTETICA - SIN WEBCAM",
                (cx - 210, cy + 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 180, 255), 2, cv2.LINE_AA)

    return frame


# ============================================================================
# FUNCIONES DE GEOMETRIA CORPORAL
# ============================================================================

def calculate_angle(a, b, c):
    """
    Calcula el angulo (en grados) formado por tres puntos.
    El vertice del angulo esta en el punto b.
    a, b, c son tuplas (x, y).
    """
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])

    cos_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angle = np.degrees(np.arccos(cos_angle))
    return angle

def calculate_distance(a, b):
    """Calcula la distancia euclidiana entre dos puntos (x, y)."""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)

def get_landmark_coords(landmarks, idx, w, h):
    """Extrae las coordenadas (x, y) en pixeles de un landmark dado su indice."""
    lm = landmarks[idx]
    return (int(lm.x * w), int(lm.y * h))

def get_landmark_visibility(landmarks, idx):
    """Devuelve la visibilidad de un landmark."""
    return landmarks[idx].visibility


# ============================================================================
# CLASIFICACION DE ACCIONES CORPORALES
# ============================================================================

def classify_action(landmarks, w, h):
    """
    Clasifica la accion corporal basandose en la geometria de los landmarks.

    Retorna:
        action (str): Nombre de la accion detectada.
        confidence (float): Confianza de la clasificacion (0.0 - 1.0).
        angles (dict): Angulos calculados relevantes.
        distances (dict): Distancias calculadas relevantes.
    """
    global step_history, last_step_time, step_count

    # Extraer landmarks clave (indices MediaPipe Pose)
    # Referencia: https://developers.google.com/mediapipe/solutions/vision/pose_landmarker
    nose = get_landmark_coords(landmarks, 0, w, h)
    left_shoulder = get_landmark_coords(landmarks, 11, w, h)
    right_shoulder = get_landmark_coords(landmarks, 12, w, h)
    left_elbow = get_landmark_coords(landmarks, 13, w, h)
    right_elbow = get_landmark_coords(landmarks, 14, w, h)
    left_wrist = get_landmark_coords(landmarks, 15, w, h)
    right_wrist = get_landmark_coords(landmarks, 16, w, h)
    left_hip = get_landmark_coords(landmarks, 23, w, h)
    right_hip = get_landmark_coords(landmarks, 24, w, h)
    left_knee = get_landmark_coords(landmarks, 25, w, h)
    right_knee = get_landmark_coords(landmarks, 26, w, h)
    left_ankle = get_landmark_coords(landmarks, 27, w, h)
    right_ankle = get_landmark_coords(landmarks, 28, w, h)

    # ---- Calcular angulos clave ----
    angles = {}
    # Angulo de rodilla izquierda (cadera-rodilla-tobillo)
    angles["rodilla_izq"] = calculate_angle(left_hip, left_knee, left_ankle)
    # Angulo de rodilla derecha
    angles["rodilla_der"] = calculate_angle(right_hip, right_knee, right_ankle)
    # Angulo de codo izquierdo (hombro-codo-muneca)
    angles["codo_izq"] = calculate_angle(left_shoulder, left_elbow, left_wrist)
    # Angulo de codo derecho
    angles["codo_der"] = calculate_angle(right_shoulder, right_elbow, right_wrist)
    # Angulo del hombro izquierdo (cadera-hombro-codo)
    angles["hombro_izq"] = calculate_angle(left_hip, left_shoulder, left_elbow)
    # Angulo del hombro derecho
    angles["hombro_der"] = calculate_angle(right_hip, right_shoulder, right_elbow)

    # ---- Calcular distancias clave ----
    distances = {}
    distances["caderas"] = calculate_distance(left_hip, right_hip)
    distances["hombros"] = calculate_distance(left_shoulder, right_shoulder)
    distances["tobillo_izq_der"] = calculate_distance(left_ankle, right_ankle)

    # Punto medio de las caderas y rodillas
    hip_mid_y = (left_hip[1] + right_hip[1]) / 2
    knee_mid_y = (left_knee[1] + right_knee[1]) / 2
    ankle_mid_y = (left_ankle[1] + right_ankle[1]) / 2

    # ===============================
    # REGLA 1: BRAZOS LEVANTADOS
    # Las munecas estan por encima de la cabeza (nariz)
    # ===============================
    head_y = nose[1]
    wrists_above_head = (left_wrist[1] < head_y and right_wrist[1] < head_y)
    # Tambien verificar que los angulos de hombro sean amplios (brazos extendidos hacia arriba)
    shoulders_raised = (angles["hombro_izq"] > 140 and angles["hombro_der"] > 140)

    if wrists_above_head and shoulders_raised:
        conf = min(1.0, (angles["hombro_izq"] + angles["hombro_der"]) / 360)
        return "BRAZOS LEVANTADOS", conf, angles, distances

    if wrists_above_head:
        conf = 0.75
        return "BRAZOS LEVANTADOS", conf, angles, distances

    # ===============================
    # REGLA 2: SENTADO
    # La cadera esta al nivel o por debajo de las rodillas
    # Los angulos de rodilla estan flexionados (< 130 grados)
    # ===============================
    hip_below_or_level_knee = (hip_mid_y >= knee_mid_y - 30)
    knees_bent = (angles["rodilla_izq"] < 140 and angles["rodilla_der"] < 140)

    if hip_below_or_level_knee and knees_bent:
        avg_knee = (angles["rodilla_izq"] + angles["rodilla_der"]) / 2
        conf = max(0.6, 1.0 - (avg_knee / 180))
        return "SENTADO", conf, angles, distances

    if hip_below_or_level_knee:
        return "SENTADO", 0.65, angles, distances

    # ===============================
    # REGLA 3: CAMINANDO
    # Deteccion de alternancia en la posicion de los pies
    # (un tobillo adelante, el otro atras, con cambios periodicos)
    # ===============================
    ankle_diff_x = left_ankle[0] - right_ankle[0]
    ankle_diff_y = abs(left_ankle[1] - right_ankle[1])
    current_time = time.time()

    # Registrar la posicion relativa de los tobillos
    step_history.append({
        "time": current_time,
        "diff_x": ankle_diff_x,
        "diff_y": ankle_diff_y
    })

    # Mantener solo los ultimos 1.5 segundos de historial
    step_history = [s for s in step_history if current_time - s["time"] < 1.5]

    # Detectar alternancia: buscar cambios de signo en diff_x (cruce de piernas)
    if len(step_history) > 10:
        diffs = [s["diff_x"] for s in step_history]
        sign_changes = 0
        for i in range(1, len(diffs)):
            if diffs[i] * diffs[i-1] < 0 and abs(diffs[i] - diffs[i-1]) > 15:
                sign_changes += 1

        # Tambien considerar variacion vertical de tobillos
        y_variations = [s["diff_y"] for s in step_history]
        avg_y_var = np.mean(y_variations) if y_variations else 0

        # Piernas en posicion de paso (separacion significativa entre tobillos)
        legs_apart = distances["tobillo_izq_der"] > distances["caderas"] * 0.5

        if sign_changes >= 2 or (legs_apart and avg_y_var > 10):
            conf = min(1.0, 0.5 + sign_changes * 0.15 + (avg_y_var / 50))
            return "CAMINANDO", conf, angles, distances

    # ===============================
    # NEUTRO (de pie, sin accion especifica)
    # ===============================
    return "NEUTRO", 0.5, angles, distances


# ============================================================================
# DIBUJO DE ESQUELETO Y LANDMARKS
# ============================================================================

# Conexiones del esqueleto para dibujo manual (subconjunto principal)
SKELETON_CONNECTIONS = [
    # Torso
    (11, 12), (11, 23), (12, 24), (23, 24),
    # Brazo izquierdo
    (11, 13), (13, 15),
    # Brazo derecho
    (12, 14), (14, 16),
    # Pierna izquierda
    (23, 25), (25, 27),
    # Pierna derecha
    (24, 26), (26, 28),
    # Pies
    (27, 29), (27, 31), (29, 31),
    (28, 30), (28, 32), (30, 32),
]

def draw_skeleton(frame, landmarks, w, h, action_color):
    """Dibuja el esqueleto con conexiones y landmarks estilizados."""
    # Dibujar conexiones (lineas)
    for i, j in SKELETON_CONNECTIONS:
        vis_i = get_landmark_visibility(landmarks, i)
        vis_j = get_landmark_visibility(landmarks, j)
        if vis_i > 0.5 and vis_j > 0.5:
            pt1 = get_landmark_coords(landmarks, i, w, h)
            pt2 = get_landmark_coords(landmarks, j, w, h)
            # Linea de conexion con color degradado
            cv2.line(frame, pt1, pt2, action_color, 3, cv2.LINE_AA)
            # Linea interna mas clara para efecto de brillo
            inner_color = tuple(min(255, c + 60) for c in action_color)
            cv2.line(frame, pt1, pt2, inner_color, 1, cv2.LINE_AA)

    # Dibujar landmarks (puntos)
    for idx in range(33):
        vis = get_landmark_visibility(landmarks, idx)
        if vis > 0.5:
            pt = get_landmark_coords(landmarks, idx, w, h)
            # Circulo exterior (halo)
            cv2.circle(frame, pt, 6, action_color, -1, cv2.LINE_AA)
            # Circulo interior blanco
            cv2.circle(frame, pt, 3, (255, 255, 255), -1, cv2.LINE_AA)

def draw_angle_annotation(frame, vertex, angle_val, label, color):
    """Dibuja una anotacion de angulo cerca del vertice."""
    text = f"{label}: {angle_val:.0f} deg"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.35
    thickness = 1
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)

    # Fondo semi-transparente para el texto
    x, y = vertex[0] + 10, vertex[1] - 5
    cv2.rectangle(frame, (x - 2, y - th - 3), (x + tw + 4, y + 4), (0, 0, 0), -1)
    cv2.putText(frame, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)


# ============================================================================
# CALLBACK DEL MOUSE
# ============================================================================

def on_mouse(event, x, y, flags, param):
    """Callback de mouse para manejar interacciones con los botones del HUD."""
    global active_filter, is_paused, take_snapshot, is_recording, exit_flag, mouse_hover_btn, buttons

    if event == cv2.EVENT_MOUSEMOVE:
        mouse_hover_btn = None
        for btn in buttons:
            if btn["x1"] <= x <= btn["x2"] and btn["y1"] <= y <= btn["y2"]:
                mouse_hover_btn = btn["name"]
                break

    elif event == cv2.EVENT_LBUTTONDOWN:
        for btn in buttons:
            if btn["x1"] <= x <= btn["x2"] and btn["y1"] <= y <= btn["y2"]:
                if btn["type"] == "filter":
                    for b in buttons:
                        if b["type"] == "filter":
                            b["active"] = False
                    btn["active"] = True
                    active_filter = btn["name"]
                    print(f"Filtro cambiado a: {active_filter}")
                elif btn["name"] == "PAUSE":
                    is_paused = not is_paused
                    btn["active"] = is_paused
                    btn["name"] = "PLAY" if is_paused else "PAUSE"
                    print("Pausado" if is_paused else "Reanudado")
                elif btn["name"] == "PLAY":
                    is_paused = not is_paused
                    btn["active"] = is_paused
                    btn["name"] = "PAUSE" if not is_paused else "PLAY"
                    print("Pausado" if is_paused else "Reanudado")
                elif btn["name"] == "SNAPSHOT":
                    take_snapshot = True
                elif btn["name"] == "RECORD":
                    is_recording = not is_recording
                    btn["active"] = is_recording
                    print("Grabacion iniciada" if is_recording else "Grabacion finalizada")
                elif btn["name"] == "EXIT":
                    exit_flag = True
                    print("Saliendo...")
                break


# ============================================================================
# FILTROS VISUALES
# ============================================================================

def apply_filters(frame):
    """Aplica los filtros solicitados al frame y los devuelve en BGR de 3 canales."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    if active_filter == "GRAY":
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
    elif active_filter == "BINARY":
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    elif active_filter == "CANNY":
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)

    return frame  # ORIGINAL


# ============================================================================
# HUD (Heads-Up Display) INTERACTIVO
# ============================================================================

def draw_hud(frame, fps, action, confidence, angles, distances, landmarks_count):
    """Renderiza el HUD completo con botones, telemetria y panel lateral de datos."""
    global mouse_hover_btn, buttons, is_recording

    action_color = ACTION_COLORS.get(action, (150, 150, 150))

    # ---- Barra superior translucida ----
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (DISPLAY_WIDTH, HUD_TOP_HEIGHT), COLOR_BG_DARK, -1)

    # ---- Panel lateral derecho (informacion de pose) ----
    panel_x = DISPLAY_WIDTH - HUD_SIDE_WIDTH
    cv2.rectangle(overlay, (panel_x, HUD_TOP_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), COLOR_BG_PANEL, -1)

    # ---- Barra inferior ----
    cv2.rectangle(overlay, (0, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT), COLOR_BG_DARK, -1)

    # Aplicar transparencia
    alpha = 0.80
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # Linea de separacion decorativa del panel lateral
    cv2.line(frame, (panel_x, HUD_TOP_HEIGHT), (panel_x, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), (60, 50, 45), 2)

    # ---- Botones superiores ----
    for btn in buttons:
        if btn["type"] == "filter" and btn["active"]:
            bg_color = (180, 110, 30)
            border_color = (240, 160, 50)
            text_color = (255, 255, 255)
        elif btn["name"] == "RECORD" and btn["active"]:
            bg_color = (40, 40, 200)
            border_color = (80, 80, 255)
            text_color = (255, 255, 255)
        elif btn["name"] in ("PAUSE", "PLAY") and btn["active"]:
            bg_color = (80, 80, 80)
            border_color = (130, 130, 130)
            text_color = (255, 255, 255)
        elif mouse_hover_btn == btn["name"]:
            bg_color = (70, 60, 50)
            border_color = (110, 100, 90)
            text_color = (255, 255, 255)
        else:
            bg_color = (40, 35, 30)
            border_color = (55, 50, 45)
            text_color = (190, 190, 190)

        cv2.rectangle(frame, (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]), bg_color, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]), border_color, 1, cv2.LINE_AA)

        text = btn["name"]
        font = cv2.FONT_HERSHEY_SIMPLEX
        fs = 0.40
        ts = cv2.getTextSize(text, font, fs, 1)[0]
        tx = btn["x1"] + (btn["x2"] - btn["x1"] - ts[0]) // 2
        ty = btn["y1"] + (btn["y2"] - btn["y1"] + ts[1]) // 2
        cv2.putText(frame, text, (tx, ty), font, fs, text_color, 1, cv2.LINE_AA)

    # ---- Panel lateral: Info de accion detectada ----
    py = HUD_TOP_HEIGHT + 20
    font = cv2.FONT_HERSHEY_SIMPLEX

    # Titulo del panel
    cv2.putText(frame, "ANALISIS DE POSTURA", (panel_x + 15, py), font, 0.45, COLOR_TEXT_PRIMARY, 1, cv2.LINE_AA)
    py += 8
    cv2.line(frame, (panel_x + 15, py), (DISPLAY_WIDTH - 15, py), (60, 50, 45), 1)
    py += 22

    # Accion detectada con color
    cv2.putText(frame, "ACCION:", (panel_x + 15, py), font, 0.38, COLOR_TEXT_SECONDARY, 1, cv2.LINE_AA)
    py += 25
    cv2.putText(frame, action, (panel_x + 15, py), font, 0.65, action_color, 2, cv2.LINE_AA)
    py += 22

    # Barra de confianza
    bar_x1 = panel_x + 15
    bar_x2 = DISPLAY_WIDTH - 15
    bar_w = bar_x2 - bar_x1
    cv2.rectangle(frame, (bar_x1, py), (bar_x2, py + 10), (50, 45, 40), -1)
    fill_w = int(bar_w * confidence)
    cv2.rectangle(frame, (bar_x1, py), (bar_x1 + fill_w, py + 10), action_color, -1)
    cv2.putText(frame, f"{confidence*100:.0f}%", (bar_x2 - 35, py + 9), font, 0.3, COLOR_TEXT_PRIMARY, 1, cv2.LINE_AA)
    py += 25

    # Separador
    cv2.line(frame, (panel_x + 15, py), (DISPLAY_WIDTH - 15, py), (50, 45, 40), 1)
    py += 18

    # Angulos detectados
    if show_angles and angles:
        cv2.putText(frame, "ANGULOS (grados)", (panel_x + 15, py), font, 0.35, COLOR_ACCENT_CYAN, 1, cv2.LINE_AA)
        py += 18
        for name, val in angles.items():
            label = name.replace("_", " ").title()
            cv2.putText(frame, f"  {label}: {val:.1f}", (panel_x + 15, py), font, 0.32, COLOR_TEXT_SECONDARY, 1, cv2.LINE_AA)
            py += 15
        py += 8

    # Distancias
    if show_distances and distances:
        cv2.putText(frame, "DISTANCIAS (px)", (panel_x + 15, py), font, 0.35, COLOR_ACCENT_ORANGE, 1, cv2.LINE_AA)
        py += 18
        for name, val in distances.items():
            label = name.replace("_", " ").title()
            cv2.putText(frame, f"  {label}: {val:.1f}", (panel_x + 15, py), font, 0.32, COLOR_TEXT_SECONDARY, 1, cv2.LINE_AA)
            py += 15
        py += 8

    # Landmarks detectados
    cv2.line(frame, (panel_x + 15, py), (DISPLAY_WIDTH - 15, py), (50, 45, 40), 1)
    py += 18
    cv2.putText(frame, f"LANDMARKS: {landmarks_count}/33", (panel_x + 15, py), font, 0.35, COLOR_TEXT_DIM, 1, cv2.LINE_AA)
    py += 15
    cv2.putText(frame, f"PASOS: {step_count}", (panel_x + 15, py), font, 0.35, COLOR_TEXT_DIM, 1, cv2.LINE_AA)

    # ---- Barra inferior ----
    status_str = f"FILTRO: {active_filter} | FPS: {fps:.1f}"
    if is_recording:
        status_str += " | GRABANDO"
        cv2.circle(frame, (len(status_str) * 7 + 30, DISPLAY_HEIGHT - 25), 5, (50, 50, 250), -1)
    cv2.putText(frame, status_str, (15, DISPLAY_HEIGHT - 18), font, 0.42, COLOR_TEXT_PRIMARY, 1, cv2.LINE_AA)

    # Indicador sonido
    sound_str = "SONIDO: ON" if SOUND_AVAILABLE else "SONIDO: OFF"
    s_size = cv2.getTextSize(sound_str, font, 0.38, 1)[0]
    cv2.putText(frame, sound_str, (DISPLAY_WIDTH - s_size[0] - 15, DISPLAY_HEIGHT - 18),
                font, 0.38, COLOR_TEXT_DIM, 1, cv2.LINE_AA)

    # ---- Indicador de accion en la zona del video (esquina superior izquierda del area de video) ----
    badge_y = HUD_TOP_HEIGHT + 15
    badge_x = 15
    badge_text = f"  {action}  "
    b_size = cv2.getTextSize(badge_text, font, 0.55, 2)[0]
    # Fondo del badge
    cv2.rectangle(frame, (badge_x, badge_y), (badge_x + b_size[0] + 10, badge_y + b_size[1] + 14), action_color, -1, cv2.LINE_AA)
    cv2.putText(frame, badge_text, (badge_x + 5, badge_y + b_size[1] + 6), font, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

    # Borde de accion parpadeante cuando no es NEUTRO
    if action != "NEUTRO" and int(time.time() * 3) % 2 == 0:
        cv2.rectangle(frame, (2, HUD_TOP_HEIGHT + 2), (panel_x - 2, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT - 2),
                      action_color, 3, cv2.LINE_AA)


# ============================================================================
# FUNCION PRINCIPAL
# ============================================================================

def main():
    global active_filter, is_paused, take_snapshot, is_recording, exit_flag
    global fps_display, step_count

    print("=" * 65)
    print("  Taller - Reconocimiento de Postura con MediaPipe")
    print("  Semana 11.2 - Computacion Visual")
    print("=" * 65)
    ensure_media_folder()

    # Verificar MediaPipe
    if mp is None:
        print("ERROR: MediaPipe no esta disponible. Instale con: pip install mediapipe")
        return

    # Inicializar MediaPipe Pose
    if USE_TASKS_API:
        task_path = "pose_landmarker.task"
        # Comprobar si existe el archivo del modelo, si no, descargarlo
        if not os.path.exists(task_path):
            # Comprobar ubicaciones alternativas
            if os.path.exists("python/pose_landmarker.task"):
                task_path = "python/pose_landmarker.task"
            elif os.path.exists("../pose_landmarker.task"):
                task_path = "../pose_landmarker.task"
            else:
                print("No se encontro 'pose_landmarker.task'. Descargando modelo desde Google CDN...")
                url = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_full/float16/1/pose_landmarker_full.task"
                try:
                    urllib.request.urlretrieve(url, task_path)
                    print("Descarga del modelo completada con exito.")
                except Exception as e:
                    print(f"Error al descargar el modelo: {e}")
                    print("La deteccion de pose podria fallar si el archivo no se encuentra.")

        try:
            options = pose_landmarker.PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=task_path),
                running_mode=VisionTaskRunningMode.IMAGE
            )
            pose = pose_landmarker.PoseLandmarker.create_from_options(options)
            print("MediaPipe Pose (Tasks API) inicializado correctamente.")
        except Exception as e:
            print(f"Error al inicializar PoseLandmarker: {e}")
            return
    else:
        mp_pose = mp.solutions.pose
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )
        print("MediaPipe Pose (Legacy solutions API) inicializado correctamente.")

    # Inicializar captura de video
    cap = cv2.VideoCapture(0)
    using_fallback = False
    using_synthetic = False

    if not cap.isOpened():
        print("ADVERTENCIA: No se pudo abrir la webcam (index 0).")
        video_path = download_fallback_video()
        if video_path and os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                print(f"Modo Fallback: Reproduciendo video: {video_path}")
                using_fallback = True
            else:
                print("Error: No se pudo cargar el video de prueba. Usando simulacion sintetica.")
                using_synthetic = True
        else:
            print("Modo Fallback: Generando simulacion sintetica animada.")
            using_synthetic = True

    # Configurar ventana
    win_name = "Taller - Reconocimiento de Postura MediaPipe"
    cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(win_name, on_mouse)

    # Video writer para grabacion
    video_writer = None

    # Variables de rendimiento
    prev_time = time.time()
    frame_count = 0
    t_start = time.time()

    last_frame = None
    prev_action = "NEUTRO"
    prev_confidence = 0.0
    prev_angles = {}
    prev_distances = {}
    prev_lm_count = 0

    # Control de sonido: evitar repetir sonido demasiado rapido
    last_sound_time = 0.0
    last_sound_action = ""
    SOUND_COOLDOWN = 1.5  # Segundos entre repeticion del mismo sonido

    print("\nControles:")
    print("  - Click en los botones del HUD para filtros y acciones")
    print("  - Tecla 'q' o ESC para salir")
    print("  - La deteccion de postura es automatica y en tiempo real")
    print("")

    try:
        while not exit_flag:
            # ---- Modo pausa ----
            if is_paused and last_frame is not None:
                display_frame = last_frame.copy()
                now = time.time()
                frame_count += 1
                if now - prev_time >= 1.0:
                    fps_display = frame_count / (now - prev_time)
                    frame_count = 0
                    prev_time = now
                draw_hud(display_frame, fps_display, prev_action, prev_confidence,
                         prev_angles, prev_distances, prev_lm_count)
                cv2.imshow(win_name, display_frame)
                key = cv2.waitKey(30) & 0xFF
                if key == 27 or key == ord('q'):
                    break
                continue

            # ---- Leer frame ----
            if using_synthetic:
                t_curr = time.time() - t_start
                frame = generate_synthetic_frame(t_curr)
            else:
                ret, frame = cap.read()
                if not ret:
                    if using_fallback:
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        print("Error: Perdida de conexion con la camara.")
                        break

            # Redimensionar
            frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))

            # ---- Procesar con MediaPipe Pose ----
            action = "NEUTRO"
            confidence = 0.0
            angles = {}
            distances = {}
            lm_count = 0

            if not using_synthetic:
                # MediaPipe requiere RGB
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                landmarks = None
                if USE_TASKS_API:
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                    results = pose.detect(mp_image)
                    if results.pose_landmarks and len(results.pose_landmarks) > 0:
                        landmarks = results.pose_landmarks[0]
                else:
                    results = pose.process(rgb_frame)
                    if results.pose_landmarks:
                        landmarks = results.pose_landmarks.landmark

                if landmarks is not None:
                    h, w = frame.shape[:2]

                    # Contar landmarks visibles
                    lm_count = sum(1 for lm in landmarks if lm.visibility > 0.5)

                    # Clasificar accion
                    action, confidence, angles, distances = classify_action(landmarks, w, h)

                    # Aplicar filtro visual ANTES de dibujar esqueleto
                    frame = apply_filters(frame)

                    # Dibujar esqueleto sobre el frame filtrado
                    action_color = ACTION_COLORS.get(action, (150, 150, 150))
                    draw_skeleton(frame, landmarks, w, h, action_color)

                    # Anotar angulos directamente sobre el frame
                    if show_angles:
                        # Rodilla izquierda
                        knee_l = get_landmark_coords(landmarks, 25, w, h)
                        if get_landmark_visibility(landmarks, 25) > 0.5:
                            draw_angle_annotation(frame, knee_l, angles.get("rodilla_izq", 0),
                                                  "Rod.I", COLOR_ACCENT_CYAN)
                        # Rodilla derecha
                        knee_r = get_landmark_coords(landmarks, 26, w, h)
                        if get_landmark_visibility(landmarks, 26) > 0.5:
                            draw_angle_annotation(frame, knee_r, angles.get("rodilla_der", 0),
                                                  "Rod.D", COLOR_ACCENT_CYAN)
                        # Codo izquierdo
                        elbow_l = get_landmark_coords(landmarks, 13, w, h)
                        if get_landmark_visibility(landmarks, 13) > 0.5:
                            draw_angle_annotation(frame, elbow_l, angles.get("codo_izq", 0),
                                                  "Codo.I", COLOR_ACCENT_GREEN)
                        # Codo derecho
                        elbow_r = get_landmark_coords(landmarks, 14, w, h)
                        if get_landmark_visibility(landmarks, 14) > 0.5:
                            draw_angle_annotation(frame, elbow_r, angles.get("codo_der", 0),
                                                  "Codo.D", COLOR_ACCENT_GREEN)

                    # Retroalimentacion sonora
                    if SOUND_AVAILABLE and sounds:
                        current_time = time.time()
                        if action != "NEUTRO":
                            # Si cambio de accion, reproducir sonido de transicion
                            if action != last_sound_action:
                                if "CAMBIO" in sounds and sounds["CAMBIO"]:
                                    sounds["CAMBIO"].play()
                                last_sound_action = action
                                last_sound_time = current_time
                            # Reproducir sonido de la accion con cooldown
                            elif current_time - last_sound_time > SOUND_COOLDOWN:
                                if action in sounds and sounds[action]:
                                    sounds[action].play()
                                last_sound_time = current_time
                else:
                    # Sin landmarks detectados
                    frame = apply_filters(frame)
            else:
                frame = apply_filters(frame)

            # Guardar estado anterior para modo pausa
            prev_action = action
            prev_confidence = confidence
            prev_angles = angles
            prev_distances = distances
            prev_lm_count = lm_count
            last_frame = frame.copy()

            # ---- Calcular FPS ----
            now = time.time()
            frame_count += 1
            if now - prev_time >= 1.0:
                fps_display = frame_count / (now - prev_time)
                frame_count = 0
                prev_time = now

            # ---- Renderizar HUD ----
            draw_hud(frame, fps_display, action, confidence, angles, distances, lm_count)

            # ---- Snapshot ----
            if take_snapshot:
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = get_media_path(f"pose_snapshot_{ts}.png")
                cv2.imwrite(filepath, frame)
                print(f"Snapshot guardado: {filepath}")
                take_snapshot = False
                # Efecto flash
                flash = np.ones_like(frame) * 255
                cv2.imshow(win_name, cv2.addWeighted(frame, 0.4, flash, 0.6, 0))
                cv2.waitKey(60)

            # ---- Grabacion ----
            if is_recording:
                if video_writer is None:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    v_filepath = get_media_path(f"pose_clip_{ts}.avi")
                    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                    video_writer = cv2.VideoWriter(v_filepath, fourcc, 20.0, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
                    print(f"Grabando video: {v_filepath}")
                video_writer.write(frame)
            else:
                if video_writer is not None:
                    video_writer.release()
                    video_writer = None
                    print("Video guardado y cerrado.")

            # ---- Mostrar frame ----
            cv2.imshow(win_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break

    finally:
        print("\nLiberando recursos...")
        if cap is not None:
            cap.release()
        if video_writer is not None:
            video_writer.release()
        if mp is not None:
            pose.close()
        if SOUND_AVAILABLE:
            pygame.mixer.quit()
        cv2.destroyAllWindows()
        print("Recursos liberados. Programa finalizado correctamente.")


if __name__ == "__main__":
    main()
