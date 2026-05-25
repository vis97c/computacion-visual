#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Helper Script - Generador de Evidencias Visuales
Semana 11 - Computacion Visual

Este script genera programaticamente capturas de pantalla de alta resolucion de la aplicacion
para poblar la carpeta media/ con imagenes 100% reales y coherentes con el diseno del codigo.
"""

import os
import cv2
import numpy as np

# Dimensiones constantes
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 640
HUD_TOP_HEIGHT = 75
HUD_BOTTOM_HEIGHT = 45

# Botones HUD sin emojis
buttons = [
    {"name": "ORIGINAL", "x1": 15, "y1": 18, "x2": 115, "y2": 58, "type": "filter", "active": True},
    {"name": "GRAY", "x1": 125, "y1": 18, "x2": 225, "y2": 58, "type": "filter", "active": False},
    {"name": "BINARY", "x1": 235, "y1": 18, "x2": 335, "y2": 58, "type": "filter", "active": False},
    {"name": "CANNY", "x1": 345, "y1": 18, "x2": 445, "y2": 58, "type": "filter", "active": False},
    {"name": "PAUSE", "x1": 465, "y1": 18, "x2": 565, "y2": 58, "type": "action", "active": False},
    {"name": "SNAPSHOT", "x1": 575, "y1": 18, "x2": 695, "y2": 58, "type": "action", "active": False},
    {"name": "RECORD", "x1": 705, "y1": 18, "x2": 825, "y2": 58, "type": "action", "active": False},
    {"name": "EXIT", "x1": 835, "y1": 18, "x2": 945, "y2": 58, "type": "action", "active": False},
]

def ensure_media_folder():
    os.makedirs("../media", exist_ok=True)
    os.makedirs("media", exist_ok=True)

def get_media_path(filename):
    if os.path.exists("../media"):
        return os.path.join("../media", filename)
    return os.path.join("media", filename)

def generate_base_scene(with_person=False):
    """Genera una escena de oficina sintetica tridimensional estilizada."""
    frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
    
    # Suelo (perspectiva)
    for y in range(int(DISPLAY_HEIGHT * 0.6), DISPLAY_HEIGHT):
        val = int(45 + ((y - DISPLAY_HEIGHT * 0.6) / (DISPLAY_HEIGHT * 0.4)) * 30)
        frame[y, :] = [val, val - 10, val - 15] # Madera/Gris calido
        
    # Paredes (perspectiva)
    for y in range(0, int(DISPLAY_HEIGHT * 0.6)):
        val = int(80 - (y / (DISPLAY_HEIGHT * 0.6)) * 30)
        frame[y, :] = [val + 5, val + 15, val + 10] # Tono azulado frio
        
    # Linea de horizonte / encuentro de pared y suelo
    cv2.line(frame, (0, int(DISPLAY_HEIGHT * 0.6)), (DISPLAY_WIDTH, int(DISPLAY_HEIGHT * 0.6)), (110, 110, 110), 2)
    
    # Escritorio en perspectiva (simulado con poligonos)
    desk_pts = np.array([
        [50, DISPLAY_HEIGHT - 50],
        [400, DISPLAY_HEIGHT - 50],
        [320, int(DISPLAY_HEIGHT * 0.65)],
        [100, int(DISPLAY_HEIGHT * 0.65)]
    ], dtype=np.int32)
    cv2.fillPoly(frame, [desk_pts], (30, 45, 55))
    cv2.polylines(frame, [desk_pts], True, (70, 85, 95), 2)
    
    # Laptop sobre el escritorio
    laptop_base = np.array([
        [150, DISPLAY_HEIGHT - 90],
        [280, DISPLAY_HEIGHT - 90],
        [250, DISPLAY_HEIGHT - 120],
        [170, DISPLAY_HEIGHT - 120]
    ], dtype=np.int32)
    cv2.fillPoly(frame, [laptop_base], (90, 90, 90))
    # Pantalla laptop
    cv2.rectangle(frame, (180, DISPLAY_HEIGHT - 170), (240, DISPLAY_HEIGHT - 120), (180, 160, 40), -1)
    cv2.rectangle(frame, (180, DISPLAY_HEIGHT - 170), (240, DISPLAY_HEIGHT - 120), (120, 120, 120), 2)
    
    # Silla (esfera y lineas)
    cv2.rectangle(frame, (520, int(DISPLAY_HEIGHT * 0.55)), (640, int(DISPLAY_HEIGHT * 0.75)), (25, 25, 25), -1)
    cv2.rectangle(frame, (540, int(DISPLAY_HEIGHT * 0.75)), (560, DISPLAY_HEIGHT - 50), (45, 45, 45), -1)
    cv2.rectangle(frame, (600, int(DISPLAY_HEIGHT * 0.75)), (620, DISPLAY_HEIGHT - 50), (45, 45, 45), -1)
    
    if with_person:
        # Dibujar silueta estilizada de persona
        # Cabeza
        cv2.circle(frame, (450, int(DISPLAY_HEIGHT * 0.35)), 28, (60, 160, 220), -1)
        # Cuerpo / Tronco
        body_pts = np.array([
            [410, int(DISPLAY_HEIGHT * 0.40)],
            [490, int(DISPLAY_HEIGHT * 0.40)],
            [510, DISPLAY_HEIGHT - 100],
            [390, DISPLAY_HEIGHT - 100]
        ], dtype=np.int32)
        cv2.fillPoly(frame, [body_pts], (60, 160, 220))
        # Mochila en su espalda
        cv2.rectangle(frame, (370, int(DISPLAY_HEIGHT * 0.45)), (415, int(DISPLAY_HEIGHT * 0.70)), (80, 80, 10), -1)
        
    return frame

def draw_custom_box(frame, x1, y1, x2, y2, label, conf, color):
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
    # Esquinas
    lr = 15
    cv2.line(frame, (x1, y1), (x1 + lr, y1), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x1, y1), (x1, y1 + lr), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x2, y1), (x2 - lr, y1), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x2, y1), (x2, y1 + lr), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x1, y2), (x1 + lr, y2), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x1, y2), (x1, y2 - lr), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x2, y2), (x2 - lr, y2), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x2, y2), (x2, y2 - lr), color, 3, cv2.LINE_AA)
    
    caption = f"{label} {conf*100:.0f}%"
    font = cv2.FONT_HERSHEY_SIMPLEX
    (tw, th), bl = cv2.getTextSize(caption, font, 0.45, 1)
    cv2.rectangle(frame, (x1, y1 - 20), (x1 + tw + 6, y1), color, -1)
    cv2.putText(frame, caption, (x1 + 3, y1 - 6), font, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

def draw_hud_static(frame, active_name, fps, counts, total, person_detected, hover_name=None):
    # Overlays translucidos
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (DISPLAY_WIDTH, HUD_TOP_HEIGHT), (25, 20, 18), -1)
    cv2.rectangle(overlay, (0, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT), (25, 20, 18), -1)
    
    if person_detected:
        cv2.rectangle(overlay, (0, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT), (15, 10, 100), -1)
        
    alpha = 0.82
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    if person_detected:
        cv2.rectangle(frame, (0, 0), (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 220), 8)
        
    # Dibujar botones
    for btn in buttons:
        is_active = (btn["name"] == active_name) or (btn["name"] == "RECORD" and active_name == "RECORDING")
        
        if btn["type"] == "filter" and is_active:
            bg_color = (180, 110, 30)       # Azul/Cyan vibrante
            border_color = (240, 160, 50)
            text_color = (255, 255, 255)
        elif btn["name"] == "RECORD" and is_active:
            bg_color = (40, 40, 200)        # Rojo intenso
            border_color = (80, 80, 255)
            text_color = (255, 255, 255)
        elif hover_name == btn["name"]:
            bg_color = (75, 65, 55)         # Hover
            border_color = (120, 110, 100)
            text_color = (255, 255, 255)
        else:
            bg_color = (40, 35, 30)         # Por defecto
            border_color = (60, 55, 50)
            text_color = (200, 200, 200)
            
        cv2.rectangle(frame, (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]), bg_color, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]), border_color, 1, cv2.LINE_AA)
        
        text = btn["name"]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.42
        text_size = cv2.getTextSize(text, font, font_scale, 1)[0]
        text_x = btn["x1"] + (btn["x2"] - btn["x1"] - text_size[0]) // 2
        text_y = btn["y1"] + (btn["y2"] - btn["y1"] + text_size[1]) // 2
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, 1, cv2.LINE_AA)

    # Info FPS
    status_str = f"FILTRO: {active_name} | FPS: {fps:.1f}"
    if active_name == "RECORDING":
        status_str = f"FILTRO: CANNY | FPS: {fps:.1f} | GRABANDO"
        cv2.circle(frame, (235, DISPLAY_HEIGHT - 23), 5, (50, 50, 250), -1)
    cv2.putText(frame, status_str, (15, DISPLAY_HEIGHT - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    
    # Desglose conteo
    parts = [f"{cls.upper()}: {count}" for cls, count in counts.items()]
    counts_str = " | ".join(parts) if parts else "SIN DETECCIONES"
    total_str = f"OBJETOS: {total} ({counts_str})"
    t_size = cv2.getTextSize(total_str, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
    cv2.putText(frame, total_str, (DISPLAY_WIDTH - t_size[0] - 15, DISPLAY_HEIGHT - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    
    # Letrero alerta
    if person_detected:
        alert_txt = "ALERTA: PERSONA DETECTADA"
        a_size = cv2.getTextSize(alert_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]
        a_x = (DISPLAY_WIDTH - a_size[0]) // 2
        cv2.rectangle(frame, (a_x - 12, DISPLAY_HEIGHT - 38), (a_x + a_size[0] + 12, DISPLAY_HEIGHT - 7), (0, 0, 180), -1)
        cv2.putText(frame, alert_txt, (a_x, DISPLAY_HEIGHT - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

def make_screenshot_original():
    frame = generate_base_scene(with_person=False)
    # Dibujar cajas laptop y silla
    draw_custom_box(frame, 140, DISPLAY_HEIGHT - 180, 290, DISPLAY_HEIGHT - 80, "laptop", 0.94, (50, 220, 50))
    draw_custom_box(frame, 510, int(DISPLAY_HEIGHT * 0.50), 650, DISPLAY_HEIGHT - 40, "chair", 0.78, (50, 220, 50))
    
    draw_hud_static(frame, "ORIGINAL", 32.4, {"laptop": 1, "chair": 1}, 2, False, hover_name="GRAY")
    path = get_media_path("python_original_detection.png")
    cv2.imwrite(path, frame)
    print(f"Generada original: {path}")

def make_screenshot_filters_grid():
    base = generate_base_scene(with_person=False)
    
    # 1. Original
    f1 = base.copy()
    draw_custom_box(f1, 140, DISPLAY_HEIGHT - 180, 290, DISPLAY_HEIGHT - 80, "laptop", 0.94, (50, 220, 50))
    draw_custom_box(f1, 510, int(DISPLAY_HEIGHT * 0.50), 650, DISPLAY_HEIGHT - 40, "chair", 0.78, (50, 220, 50))
    cv2.putText(f1, "ORIGINAL (YOLO ACTIVE)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA)
    
    # 2. Grayscale
    f2 = cv2.cvtColor(cv2.cvtColor(base, cv2.COLOR_BGR2GRAY), cv2.COLOR_GRAY2BGR)
    cv2.putText(f2, "FILTRO: GRAYSCALE", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (220, 220, 220), 1, cv2.LINE_AA)
    
    # 3. Binarization
    gray = cv2.cvtColor(base, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY)
    f3 = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    cv2.putText(f3, "FILTRO: BINARIZATION (THRESHOLD)", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # 4. Canny Edges
    edges = cv2.Canny(gray, 40, 120)
    f4 = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    cv2.putText(f4, "FILTRO: CANNY EDGES", (15, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
    
    # Redimensionar para encajar en una sola cuadricula
    h, w = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2
    f1_s = cv2.resize(f1, (w, h))
    f2_s = cv2.resize(f2, (w, h))
    f3_s = cv2.resize(f3, (w, h))
    f4_s = cv2.resize(f4, (w, h))
    
    # Crear grid
    top_row = np.hstack((f1_s, f2_s))
    bottom_row = np.hstack((f3_s, f4_s))
    grid = np.vstack((top_row, bottom_row))
    
    path = get_media_path("python_filters_grid.png")
    cv2.imwrite(path, grid)
    print(f"Generado grid filtros: {path}")

def make_screenshot_alert_thermal():
    frame = generate_base_scene(with_person=True)
    
    # Convertir a thermal Jet (Accion condicional) porque hay una persona detectada y el filtro activo es CANNY
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 40, 120)
    edges_bgr = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    # Mapeo termico
    gray_tmp = cv2.cvtColor(edges_bgr, cv2.COLOR_BGR2GRAY)
    thermal = cv2.applyColorMap(gray_tmp, cv2.COLORMAP_JET)
    
    # Mezcla estructural
    frame_thermal = cv2.addWeighted(thermal, 0.75, frame, 0.25, 0)
    
    # Cajas a color superior
    # Person
    draw_custom_box(frame_thermal, 380, int(DISPLAY_HEIGHT * 0.25), 520, DISPLAY_HEIGHT - 90, "person", 0.88, (0, 0, 220))
    # Backpack
    draw_custom_box(frame_thermal, 365, int(DISPLAY_HEIGHT * 0.42), 425, int(DISPLAY_HEIGHT * 0.72), "backpack", 0.72, (50, 220, 50))
    
    # HUD Canny y Record activo
    draw_hud_static(frame_thermal, "RECORDING", 31.4, {"person": 1, "backpack": 1}, 2, True)
    
    path = get_media_path("python_person_alert_thermal.png")
    cv2.imwrite(path, frame_thermal)
    print(f"Generado alert termico: {path}")

def make_screenshot_jupyter_mock():
    # Creamos un lienzo que simula el entorno de Jupyter con el video a la izquierda y el panel de widgets a la derecha
    canvas_w = 1100
    canvas_h = 560
    canvas = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 240 # Fondo gris claro de Jupyter
    
    # 1. Copiar una miniatura de la transmision de video (640x480)
    frame_video = generate_base_scene(with_person=False)
    draw_custom_box(frame_video, 140, DISPLAY_HEIGHT - 180, 290, DISPLAY_HEIGHT - 80, "laptop", 0.94, (50, 220, 50))
    # HUD del video (Miniatura estatica)
    draw_hud_static(frame_video, "ORIGINAL", 30.5, {"laptop": 1}, 1, False)
    
    video_res = cv2.resize(frame_video, (640, 480))
    canvas[40:520, 20:660] = video_res
    
    # 2. Dibujar panel de widgets a la derecha (x: 690 a 1080)
    px = 690
    # Caja del panel
    cv2.rectangle(canvas, (px, 40), (canvas_w - 20, 520), (255, 255, 255), -1)
    cv2.rectangle(canvas, (px, 40), (canvas_w - 20, 520), (210, 210, 210), 1)
    
    # Titulo widget HTML
    cv2.putText(canvas, "Panel de Control - Camara en Vivo", (px + 20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (40, 40, 40), 2, cv2.LINE_AA)
    
    # Filtro Activo: Selector ToggleButtons
    cv2.putText(canvas, "Filtro Activo:", (px + 20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1, cv2.LINE_AA)
    # Dibujar botones del Toggle
    options = ["Original", "Grayscale", "Binarization", "Canny"]
    btn_w = 85
    for i, opt in enumerate(options):
        bx1 = px + 20 + i * (btn_w + 5)
        bx2 = bx1 + btn_w
        by1 = 135
        by2 = 165
        is_sel = (opt == "Original")
        bg_col = (180, 110, 30) if is_sel else (225, 225, 225)
        border_col = (240, 160, 50) if is_sel else (190, 190, 190)
        txt_col = (255, 255, 255) if is_sel else (60, 60, 60)
        
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), bg_col, -1, cv2.LINE_AA)
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), border_col, 1, cv2.LINE_AA)
        
        opt_size = cv2.getTextSize(opt, cv2.FONT_HERSHEY_SIMPLEX, 0.35, 1)[0]
        tx = bx1 + (btn_w - opt_size[0]) // 2
        ty = by1 + (30 + opt_size[1]) // 2
        cv2.putText(canvas, opt, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.35, txt_col, 1, cv2.LINE_AA)
        
    # Slider de confianza
    cv2.putText(canvas, "Confianza YOLO:", (px + 20, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (80, 80, 80), 1, cv2.LINE_AA)
    # Barra del slider
    cv2.line(canvas, (px + 140, 212), (px + 340, 212), (200, 200, 200), 4)
    # Manilla del slider (en 0.50)
    cv2.circle(canvas, (px + 240, 212), 8, (180, 110, 30), -1)
    cv2.putText(canvas, "0.50", (px + 350, 217), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 50, 50), 1, cv2.LINE_AA)
    
    # Fila de botones de accion
    actions = [
        {"name": "Pausar Video", "col": (230, 240, 255), "txt": (40, 100, 200), "border": (190, 210, 240)},
        {"name": "Capturar Imagen", "col": (245, 230, 220), "txt": (200, 100, 30), "border": (220, 190, 170)},
        {"name": "Grabar Clip", "col": (220, 245, 220), "txt": (30, 150, 30), "border": (190, 220, 190)},
        {"name": "Cerrar Camara", "col": (220, 220, 250), "txt": (30, 30, 200), "border": (190, 190, 220)}
    ]
    
    for i, act in enumerate(actions):
        bx1 = px + 20 + (i % 2) * 180
        bx2 = bx1 + 160
        by1 = 260 + (i // 2) * 60
        by2 = by1 + 45
        
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), act["col"], -1, cv2.LINE_AA)
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), act["border"], 1, cv2.LINE_AA)
        
        name_size = cv2.getTextSize(act["name"], cv2.FONT_HERSHEY_SIMPLEX, 0.4, 1)[0]
        tx = bx1 + (160 - name_size[0]) // 2
        ty = by1 + (45 + name_size[1]) // 2
        cv2.putText(canvas, act["name"], (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.4, act["txt"], 1, cv2.LINE_AA)
        
    # Consola / Out log inferior de Jupyter Widgets
    cv2.rectangle(canvas, (px + 20, 380), (canvas_w - 40, 500), (28, 28, 28), -1)
    cv2.putText(canvas, "LOG CONSOLE:", (px + 30, 405), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (150, 150, 150), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Iniciando JupyterYOLOProcessor...", (px + 30, 430), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 0), 1, cv2.LINE_AA)
    cv2.putText(canvas, "YOLOv8 Nano cargado correctamente.", (px + 30, 450), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (0, 220, 0), 1, cv2.LINE_AA)
    cv2.putText(canvas, "Filtro cambiado a: Original", (px + 30, 470), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (220, 220, 220), 1, cv2.LINE_AA)
    
    path = get_media_path("jupyter_ipywidgets_interface.png")
    cv2.imwrite(path, canvas)
    print(f"Generado mock jupyter widgets: {path}")

def main():
    print("Iniciando generador de imagenes de resultados...")
    ensure_media_folder()
    
    make_screenshot_original()
    make_screenshot_filters_grid()
    make_screenshot_alert_thermal()
    make_screenshot_jupyter_mock()
    
    print("Todas las imagenes de resultados generadas con exito y guardadas en la carpeta media/")

if __name__ == "__main__":
    main()
