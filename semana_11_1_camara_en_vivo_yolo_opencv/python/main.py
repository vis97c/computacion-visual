#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Taller - Camara en Vivo: Captura y Procesamiento de Video en Tiempo Real con YOLO
Semana 11 - Computacion Visual

Desarrollado con HUD Virtual Clicable, multiples filtros y accion condicional de intrusion.
Soporta fallback automatico a descarga de video o simulacion sintetica si no hay webcam.
"""

import os
import sys
import time
import datetime
import urllib.request
import numpy as np
import cv2

# Intentar importar ultralytics de forma dinamica
try:
    from ultralytics import YOLO
except ImportError:
    print("El paquete 'ultralytics' no esta instalado o se esta instalando. Ejecute pip install ultralytics.")
    # Fallback placeholder si no esta disponible al inicio
    YOLO = None

# Configuracion de resolucion y UI
DISPLAY_WIDTH = 960
DISPLAY_HEIGHT = 640
HUD_TOP_HEIGHT = 75
HUD_BOTTOM_HEIGHT = 45

# Inicializacion de variables globales de control
active_filter = "ORIGINAL"     # ORIGINAL, GRAY, BINARY, CANNY
is_paused = False
take_snapshot = False
is_recording = False
exit_flag = False
mouse_hover_btn = None
confidence_threshold = 0.50    # Minimo 50% de confianza
fps_display = 0.0

# Botones interactivos sin emojis
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
    """Crea la carpeta media en la ruta correcta si no existe."""
    # Buscar si estamos en el subdirectorio python o en el directorio raiz
    if os.path.exists("media") or os.path.exists("../media"):
        return
    try:
        os.makedirs("media", exist_ok=True)
    except Exception as e:
        print(f"Error al crear carpeta media: {e}")

def get_media_path(filename):
    """Devuelve la ruta absoluta o relativa correcta para guardar en la carpeta media."""
    if os.path.exists("../media"):
        return os.path.join("../media", filename)
    elif os.path.exists("media"):
        return os.path.join("media", filename)
    else:
        os.makedirs("media", exist_ok=True)
        return os.path.join("media", filename)

def download_fallback_video():
    """Descarga un video corto de personas caminando si no hay webcam fisica."""
    target_path = "people-detection.mp4"
    if os.path.exists(target_path):
        return target_path
    
    url = "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/people-detection.mp4"
    print(f"No se detecto webcam fisica. Descargando video de prueba desde:\n{url}")
    print("Espere un momento...")
    try:
        # Descarga con timeout
        urllib.request.urlretrieve(url, target_path)
        print(f"Video descargado con exito y guardado en: {target_path}")
        return target_path
    except Exception as e:
        print(f"No se pudo descargar el video debido a: {e}")
        return None

def generate_synthetic_frame(t):
    """Genera un frame sintetico animado como ultimo recurso de fallback."""
    frame = np.zeros((DISPLAY_HEIGHT, DISPLAY_WIDTH, 3), dtype=np.uint8)
    # Fondo con gradiente azul oscuro
    for y in range(DISPLAY_HEIGHT):
        val = int(30 + (y / DISPLAY_HEIGHT) * 40)
        frame[y, :] = [val, 20, 15]
    
    # Grid de fondo decorativo
    grid_size = 60
    for x in range(0, DISPLAY_WIDTH, grid_size):
        cv2.line(frame, (x, 0), (x, DISPLAY_HEIGHT), (45, 30, 25), 1)
    for y in range(0, DISPLAY_HEIGHT, grid_size):
        cv2.line(frame, (0, y), (DISPLAY_WIDTH, y), (45, 30, 25), 1)

    # Circulo central (simulando un objeto)
    cx = int(DISPLAY_WIDTH / 2 + np.sin(t * 2) * 150)
    cy = int(DISPLAY_HEIGHT / 2 + np.cos(t * 3) * 100)
    cv2.circle(frame, (cx, cy), 45, (0, 180, 255), -1)
    cv2.circle(frame, (cx, cy), 45, (255, 255, 255), 2)
    
    # Cuadrado (simulando una persona)
    px = int(DISPLAY_WIDTH / 2 + np.cos(t * 1.5) * 200)
    py = int(DISPLAY_HEIGHT / 2 + np.sin(t * 1.5) * 120)
    cv2.rectangle(frame, (px - 50, py - 90), (px + 50, py + 90), (50, 220, 50), -1)
    cv2.rectangle(frame, (px - 50, py - 90), (px + 50, py + 90), (255, 255, 255), 2)
    
    # Etiqueta decorativa para simular YOLO si no estuviese activo
    cv2.putText(frame, "SIMULACION SINTETICA", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2, cv2.LINE_AA)
    
    return frame, [(px - 50, py - 90, px + 50, py + 90, "person", 0.92), (cx - 45, cy - 45, cx + 45, cy + 45, "sports ball", 0.88)]

def on_mouse(event, x, y, flags, param):
    """Callback de mouse para manejar interacciones con los botones en pantalla."""
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
                    # Desactivar todos los demas filtros
                    for b in buttons:
                        if b["type"] == "filter":
                            b["active"] = False
                    btn["active"] = True
                    active_filter = btn["name"]
                    print(f"Filtro cambiado a: {active_filter}")
                elif btn["name"] == "PAUSE":
                    is_paused = not is_paused
                    btn["active"] = is_paused
                    # Actualizar texto del boton visualmente
                    btn["name"] = "PLAY" if is_paused else "PAUSE"
                    print("Reproduccion pausada" if is_paused else "Reproduccion reanudada")
                elif btn["name"] == "PLAY":
                    is_paused = not is_paused
                    btn["active"] = is_paused
                    btn["name"] = "PAUSE" if not is_paused else "PLAY"
                    print("Reproduccion pausada" if is_paused else "Reproduccion reanudada")
                elif btn["name"] == "SNAPSHOT":
                    take_snapshot = True
                elif btn["name"] == "RECORD":
                    is_recording = not is_recording
                    btn["active"] = is_recording
                    print("Grabacion iniciada" if is_recording else "Grabacion finalizada")
                elif btn["name"] == "EXIT":
                    exit_flag = True
                    print("Saliendo de la aplicacion...")
                break

def apply_filters(frame):
    """Aplica los filtros solicitados al frame y los devuelve en formato BGR de 3 canales."""
    global active_filter
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    if active_filter == "GRAY":
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        
    elif active_filter == "BINARY":
        # Umbralizacion simple con valor 127
        _, thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
        
    elif active_filter == "CANNY":
        # Deteccion de bordes Canny
        edges = cv2.Canny(gray, 50, 150)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
    return frame  # ORIGINAL

def draw_custom_box(frame, x1, y1, x2, y2, label, conf, color):
    """Dibuja una caja delimitadora estetica con esquinas reforzadas."""
    # Dibujar la caja principal con linea fina
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 1, cv2.LINE_AA)
    
    # Dibujar las esquinas reforzadas
    len_ratio = 15
    # Esquina superior izquierda
    cv2.line(frame, (x1, y1), (x1 + len_ratio, y1), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x1, y1), (x1, y1 + len_ratio), color, 3, cv2.LINE_AA)
    # Esquina superior derecha
    cv2.line(frame, (x2, y1), (x2 - len_ratio, y1), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x2, y1), (x2, y1 + len_ratio), color, 3, cv2.LINE_AA)
    # Esquina inferior izquierda
    cv2.line(frame, (x1, y2), (x1 + len_ratio, y2), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x1, y2), (x1, y2 - len_ratio), color, 3, cv2.LINE_AA)
    # Esquina inferior derecha
    cv2.line(frame, (x2, y2), (x2 - len_ratio, y2), color, 3, cv2.LINE_AA)
    cv2.line(frame, (x2, y2), (x2, y2 - len_ratio), color, 3, cv2.LINE_AA)
    
    # Crear fondo para la etiqueta
    caption = f"{label} {conf*100:.0f}%"
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.45
    thickness = 1
    (text_w, text_h), baseline = cv2.getTextSize(caption, font, font_scale, thickness)
    
    # Ajustar para que no se salga de la pantalla
    label_y = y1 - 8 if y1 - 8 > text_h + 10 else y1 + text_h + 8
    
    cv2.rectangle(frame, (x1, label_y - text_h - 4), (x1 + text_w + 6, label_y + baseline - 2), color, -1)
    cv2.putText(frame, caption, (x1 + 3, label_y - 2), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

def draw_hud(frame, fps, counts, total_objects, person_detected):
    """Renderiza el HUD interactivo con botones clicables y barra de telemetria."""
    global active_filter, is_recording, mouse_hover_btn, buttons
    
    # 1. Crear overlays translucidos (Efecto Glassmorphic)
    overlay = frame.copy()
    # Barra Superior
    cv2.rectangle(overlay, (0, 0), (DISPLAY_WIDTH, HUD_TOP_HEIGHT), (25, 20, 18), -1)
    # Barra Inferior
    cv2.rectangle(overlay, (0, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT), (25, 20, 18), -1)
    
    # Si se detecta persona y esta activa la alerta condicional, tenir barra inferior de rojo
    if person_detected:
        cv2.rectangle(overlay, (0, DISPLAY_HEIGHT - HUD_BOTTOM_HEIGHT), (DISPLAY_WIDTH, DISPLAY_HEIGHT), (15, 10, 100), -1)
    
    # Aplicar transparencia
    alpha = 0.82
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
    
    # Dibujar borde parpadeante si se detecta persona
    if person_detected:
        if int(time.time() * 2) % 2 == 0:
            cv2.rectangle(frame, (0, 0), (DISPLAY_WIDTH, DISPLAY_HEIGHT), (0, 0, 220), 8)
            
    # 2. Dibujar Botones en Pantalla
    for btn in buttons:
        # Definir color del boton por su estado
        if btn["type"] == "filter" and btn["active"]:
            bg_color = (180, 110, 30)       # Azul/Cyan vibrante activo
            border_color = (240, 160, 50)
            text_color = (255, 255, 255)
        elif btn["name"] == "RECORD" and btn["active"]:
            bg_color = (40, 40, 200)        # Rojo intenso para grabacion
            border_color = (80, 80, 255)
            text_color = (255, 255, 255)
        elif btn["name"] == "PAUSE" and btn["active"]:
            bg_color = (80, 80, 80)         # Gris para pausa activa
            border_color = (130, 130, 130)
            text_color = (255, 255, 255)
        elif mouse_hover_btn == btn["name"]:
            bg_color = (75, 65, 55)         # Gris calido Hover
            border_color = (120, 110, 100)
            text_color = (255, 255, 255)
        else:
            bg_color = (40, 35, 30)         # Fondo por defecto
            border_color = (60, 55, 50)
            text_color = (200, 200, 200)
            
        cv2.rectangle(frame, (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]), bg_color, -1, cv2.LINE_AA)
        cv2.rectangle(frame, (btn["x1"], btn["y1"]), (btn["x2"], btn["y2"]), border_color, 1, cv2.LINE_AA)
        
        # Centrar texto
        text = btn["name"]
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.42
        thickness = 1
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = btn["x1"] + (btn["x2"] - btn["x1"] - text_size[0]) // 2
        text_y = btn["y1"] + (btn["y2"] - btn["y1"] + text_size[1]) // 2
        cv2.putText(frame, text, (text_x, text_y), font, font_scale, text_color, thickness, cv2.LINE_AA)

    # 3. Informacion de FPS e Info de Sistema (Barra Inferior Izquierda)
    status_str = f"FILTRO: {active_filter} | FPS: {fps:.1f}"
    if is_recording:
        # Añadir circulo rojo simulando grabacion
        status_str += " | GRABANDO"
        cv2.circle(frame, (235, DISPLAY_HEIGHT - 23), 5, (50, 50, 250), -1)
    cv2.putText(frame, status_str, (15, DISPLAY_HEIGHT - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    
    # 4. Desglose del conteo de objetos (Barra Inferior Derecha)
    parts = [f"{cls.upper()}: {count}" for cls, count in counts.items()]
    counts_str = " | ".join(parts) if parts else "SIN DETECCIONES"
    total_str = f"OBJETOS: {total_objects} ({counts_str})"
    
    t_size = cv2.getTextSize(total_str, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)[0]
    cv2.putText(frame, total_str, (DISPLAY_WIDTH - t_size[0] - 15, DISPLAY_HEIGHT - 17), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (220, 220, 220), 1, cv2.LINE_AA)
    
    # 5. Letrero de Alerta en pantalla (Sin Emojis)
    if person_detected:
        alert_txt = "ALERTA: PERSONA DETECTADA"
        if int(time.time() * 2.5) % 2 == 0:
            a_size = cv2.getTextSize(alert_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)[0]
            a_x = (DISPLAY_WIDTH - a_size[0]) // 2
            cv2.rectangle(frame, (a_x - 12, DISPLAY_HEIGHT - 38), (a_x + a_size[0] + 12, DISPLAY_HEIGHT - 7), (0, 0, 180), -1)
            cv2.putText(frame, alert_txt, (a_x, DISPLAY_HEIGHT - 16), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)

def main():
    global active_filter, is_paused, take_snapshot, is_recording, exit_flag, fps_display, YOLO
    
    print("Iniciando Taller - Camara en Vivo YOLO + OpenCV...")
    ensure_media_folder()
    
    # 1. Inicializar modelo YOLOv8
    model = None
    if YOLO is not None:
        try:
            print("Cargando modelo YOLOv8 Nano...")
            # Descargara yolov8n.pt automaticamente de internet si no existe
            model = YOLO("yolov8n.pt")
            print("YOLOv8 cargado correctamente.")
        except Exception as e:
            print(f"Error al cargar el modelo de YOLO: {e}")
            print("Se continuara en modo procesamiento sin detecciones profundas si no se resuelve.")
    else:
        print("Ultralytics YOLO no esta disponible. Se ejecutara en modo simulación de objetos.")

    # 2. Inicializar Captura de Video (Webcam por defecto)
    cap = cv2.VideoCapture(0)
    using_fallback = False
    
    if not cap.isOpened():
        print("ADVERTENCIA: No se pudo abrir la webcam por defecto (index 0).")
        video_path = download_fallback_video()
        if video_path and os.path.exists(video_path):
            cap = cv2.VideoCapture(video_path)
            if cap.isOpened():
                print(f"Modo Fallback: Reproduciendo video de prueba: {video_path}")
                using_fallback = True
            else:
                print("Error: Tampoco se pudo cargar el video de prueba.")
        else:
            print("Modo Fallback: Generando simulación de video sintético animado.")
            using_fallback = True

    # Configurar ventana OpenCV y callback de mouse
    win_name = "Taller - Camara en Vivo YOLOv8"
    cv2.namedWindow(win_name, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(win_name, on_mouse)
    
    # Configurar VideoWriter para grabacion
    video_writer = None
    
    # Variables de rendimiento
    prev_time = time.time()
    frame_count = 0
    t_start = time.time()
    
    last_frame = None
    
    try:
        while not exit_flag:
            t0 = time.perf_counter()
            
            # Si esta pausado, renderizar el ultimo frame guardado para mantener botones interactivos
            if is_paused and last_frame is not None:
                display_frame = last_frame.copy()
                
                # Calcular FPS estatico
                now = time.time()
                frame_count += 1
                if now - prev_time >= 1.0:
                    fps_display = frame_count / (now - prev_time)
                    frame_count = 0
                    prev_time = now
                
                # Volver a dibujar HUD sobre el duplicado para mantener hover effects
                # Obtener info previa
                draw_hud(display_frame, fps_display, prev_counts, prev_total, prev_person)
                cv2.imshow(win_name, display_frame)
                
                # Pequeña espera para evitar saturar CPU en pausa
                key = cv2.waitKey(30) & 0xFF
                if key == 27 or key == ord('q'):
                    break
                continue
            
            # Leer frame
            if not using_fallback or (using_fallback and cap.isOpened()):
                ret, frame = cap.read()
                if not ret:
                    if using_fallback:
                        # Reiniciar el video de prueba en bucle
                        cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    else:
                        print("Error: Perdi la conexion con la camara.")
                        break
            else:
                # Generar simulacion sintetica
                t_curr = time.time() - t_start
                frame, synthetic_detections = generate_synthetic_frame(t_curr)
                ret = True
            
            # Redimensionar el frame de entrada a resolucion constante para el HUD
            frame = cv2.resize(frame, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
            
            # 3. Procesar deteccion de objetos con YOLO
            detections = []
            person_detected = False
            counts = {}
            total_objects = 0
            
            if model is not None and not (using_fallback and not cap.isOpened()):
                # Correr inferencia en el frame
                # Usar verbose=False para no llenar la terminal y conf=0.5
                results = model.predict(frame, verbose=False, conf=confidence_threshold)
                
                if results and len(results) > 0:
                    result = results[0]
                    boxes = result.boxes
                    for box in boxes:
                        # Obtener clase, confianza y coordenadas
                        cls_id = int(box.cls[0])
                        cls_name = model.names[cls_id]
                        conf = float(box.conf[0])
                        
                        # Obtener coordenadas de caja
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = map(int, xyxy)
                        
                        detections.append((x1, y1, x2, y2, cls_name, conf))
                        
                        # Conteo por clase
                        counts[cls_name] = counts.get(cls_name, 0) + 1
                        total_objects += 1
                        
                        # Accion condicional: persona detectada (clase persona en COCO es 'person')
                        if cls_name == "person":
                            person_detected = True
            elif using_fallback and not cap.isOpened():
                # Detecciones simuladas sinteticas
                for x1, y1, x2, y2, cls_name, conf in synthetic_detections:
                    detections.append((x1, y1, x2, y2, cls_name, conf))
                    counts[cls_name] = counts.get(cls_name, 0) + 1
                    total_objects += 1
                    if cls_name == "person":
                        person_detected = True
                        
            # Guardar ultimos contadores para el modo pausa
            prev_counts = counts
            prev_total = total_objects
            prev_person = person_detected

            # 4. Aplicar Filtros Visuales
            # Si se detecta persona y hay un filtro activo, el filtro se fuerza en color termico (Bonus de Accion Condicional)
            if person_detected and active_filter in ["GRAY", "BINARY", "CANNY"]:
                # Creamos el frame filtrado estandar
                filtered_frame = apply_filters(frame.copy())
                # Lo convertimos a mapa de color JET (apariencia termica infrarroja)
                # cv2.applyColorMap requiere un frame de un solo canal en escala de grises
                gray_tmp = cv2.cvtColor(filtered_frame, cv2.COLOR_BGR2GRAY)
                thermal = cv2.applyColorMap(gray_tmp, cv2.COLORMAP_JET)
                
                # Mezclar un 30% del original para no perder contornos
                frame_to_display = cv2.addWeighted(thermal, 0.7, frame, 0.3, 0)
            else:
                frame_to_display = apply_filters(frame.copy())

            # 5. Dibujar cajas delimitadoras de YOLO
            # Se dibujan despues del filtro para que las cajas se mantengan a color sobre frames en grises/canny
            for x1, y1, x2, y2, label, conf in detections:
                color = (50, 220, 50)  # Verde por defecto para objetos
                if label == "person":
                    color = (0, 0, 220)  # Rojo para alerta persona
                draw_custom_box(frame_to_display, x1, y1, x2, y2, label, conf, color)

            # Calcular FPS reales de procesamiento
            now = time.time()
            frame_count += 1
            if now - prev_time >= 1.0:
                fps_display = frame_count / (now - prev_time)
                frame_count = 0
                prev_time = now

            # Guardar el frame actual procesado en memoria por si se pausa
            last_frame = frame_to_display.copy()

            # 6. Renderizar HUD
            draw_hud(frame_to_display, fps_display, counts, total_objects, person_detected)

            # 7. Acciones de Snapshot y Grabacion
            # Guardar Snapshot (Instantanea)
            if take_snapshot:
                # Generar nombre unico con marca de tiempo
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"snapshot_{ts}.png"
                filepath = get_media_path(filename)
                
                # Guardar el frame visualizado (con HUD y cajas)
                cv2.imwrite(filepath, frame_to_display)
                print(f"Snapshot guardado con exito en: {filepath}")
                take_snapshot = False
                
                # Pequeño efecto visual de flash blanco en pantalla al tomar snapshot
                flash = np.ones_like(frame_to_display) * 255
                cv2.imshow(win_name, cv2.addWeighted(frame_to_display, 0.4, flash, 0.6, 0))
                cv2.waitKey(60)

            # Manejar Grabacion de Video
            if is_recording:
                if video_writer is None:
                    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    v_filename = f"clip_{ts}.avi"
                    v_filepath = get_media_path(v_filename)
                    # Codec MJPG, 20 FPS, resolucion del display
                    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
                    video_writer = cv2.VideoWriter(v_filepath, fourcc, 20.0, (DISPLAY_WIDTH, DISPLAY_HEIGHT))
                    print(f"Iniciando escritura en video: {v_filepath}")
                
                # Escribir frame al video
                video_writer.write(frame_to_display)
            else:
                if video_writer is not None:
                    # Cerrar y liberar el escritor de video
                    video_writer.release()
                    video_writer = None
                    print("Archivo de video guardado y cerrado.")

            # Mostrar frame
            cv2.imshow(win_name, frame_to_display)
            
            # Tecla fisica 'q' o ESC como alternativa redundante para salir
            key = cv2.waitKey(1) & 0xFF
            if key == 27 or key == ord('q'):
                break
                
    finally:
        # Liberar recursos de manera limpia
        print("Liberando recursos...")
        if cap is not None:
            cap.release()
        if video_writer is not None:
            video_writer.release()
        cv2.destroyAllWindows()
        print("Recursos liberados. Programa finalizado correctamente.")

if __name__ == "__main__":
    main()
