"""
Taller Gestos con Webcam — Control Visual con MediaPipe
=========================================================

Aplicación principal de webcam en tiempo real que:
1. Detecta manos y gestos con MediaPipe Hands
2. Cuenta dedos extendidos
3. Mide distancia entre pulgar e índice (pinch)
4. Ejecuta acciones visuales según el gesto:
   - Puño (FIST): fondo rojo
   - Palma abierta (OPEN_PALM): fondo verde — cambia de escena
   - Señalar (POINTING): mueve un cursor en pantalla
   - Peace (PEACE): fondo azul
   - Pinch (PINCH): escala un objeto
5. Incluye un mini-juego de atrapar objetos controlado con la mano

Ejecución:
    python main.py              # Modo detección de gestos
    python main.py --game       # Modo juego interactivo

Requiere: webcam funcional, mediapipe, opencv-python, numpy
"""

import cv2
import numpy as np
import sys
import time

# Importar MediaPipe
import mediapipe as mp

# Importar utilidades propias
from gesture_utils import (
    mp_hands, mp_drawing, mp_styles,
    count_fingers, finger_distance, detect_gesture,
    get_palm_center, draw_hand_info, get_landmark_coords
)


# ============================================================
# Colores de fondo por gesto
# ============================================================

GESTURE_COLORS = {
    'FIST':       (50, 50, 200),      # Rojo
    'OPEN_PALM':  (50, 200, 50),      # Verde
    'POINTING':   (200, 200, 50),     # Amarillo
    'PEACE':      (200, 50, 50),      # Azul
    'PINCH':      (200, 50, 200),     # Magenta
    'THREE':      (50, 200, 200),     # Cyan
    'THUMBS_UP':  (100, 200, 255),    # Naranja
}

DEFAULT_COLOR = (40, 40, 40)


# ============================================================
# Modo 1: Detección de gestos con acciones visuales
# ============================================================

def run_gesture_detection():
    """
    Modo principal: detecta gestos y ejecuta acciones visuales.

    Acciones:
    - FIST: fondo rojo, texto "STOP"
    - OPEN_PALM: fondo verde, texto "GO" — simula cambio de escena
    - POINTING: cursor sigue el dedo índice
    - PEACE: fondo azul, texto "PEACE"
    - PINCH: muestra distancia thumb-index, escala un círculo
    - Otros: muestra conteo de dedos
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la webcam")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Objeto controlable (círculo)
    obj_x, obj_y = 640, 360
    obj_radius = 40
    scene_index = 0
    scenes = ['Escena 1: Detección', 'Escena 2: Control', 'Escena 3: Juego']

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    ) as hands:

        print("Gestos disponibles:")
        print("  - Puño (FIST): fondo rojo")
        print("  - Palma abierta (OPEN_PALM): cambiar escena")
        print("  - Señalar (POINTING): mover cursor")
        print("  - Peace (PEACE): fondo azul")
        print("  - Pinch (PINCH): escalar objeto")
        print("  - ESC para salir")

        prev_gesture = None
        gesture_start_time = 0

        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)  # Espejo
            h, w = frame.shape[:2]

            # Convertir BGR → RGB para MediaPipe
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            # Fondo semi-transparente
            overlay = frame.copy()
            bg_color = DEFAULT_COLOR
            gesture = 'NONE'
            finger_count = 0

            if results.multi_hand_landmarks:
                for hand_landmarks, hand_info in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness
                ):
                    handedness = hand_info.classification[0].label

                    # Detectar gesto
                    gesture, finger_count, fingers = detect_gesture(
                        hand_landmarks, (h, w), handedness
                    )

                    # Color de fondo según gesto
                    bg_color = GESTURE_COLORS.get(gesture, DEFAULT_COLOR)

                    # Dibujar landmarks
                    draw_hand_info(frame, hand_landmarks, gesture, finger_count, handedness)

                    # --- Acciones específicas por gesto ---

                    if gesture == 'POINTING':
                        # Cursor sigue la punta del índice
                        coords = get_landmark_coords(hand_landmarks, (h, w))
                        idx_tip = coords[8]
                        cv2.circle(frame, idx_tip, 15, (0, 255, 255), -1)
                        cv2.circle(frame, idx_tip, 18, (0, 200, 200), 2)
                        obj_x, obj_y = idx_tip

                    elif gesture == 'PINCH':
                        # Escalar objeto con distancia thumb-index
                        dist, pa, pb = finger_distance(hand_landmarks, (h, w))
                        obj_radius = max(20, min(120, int(dist / 2)))
                        cv2.line(frame, pa, pb, (255, 0, 255), 2)
                        cv2.putText(frame, f'Dist: {dist:.0f}px',
                                    (pa[0], pa[1] - 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)

                    elif gesture == 'OPEN_PALM':
                        # Cambiar escena si se mantiene 1 segundo
                        if prev_gesture != 'OPEN_PALM':
                            gesture_start_time = time.time()
                        elif time.time() - gesture_start_time > 1.0:
                            scene_index = (scene_index + 1) % len(scenes)
                            gesture_start_time = time.time()

                    prev_gesture = gesture

            # Aplicar overlay de color
            cv2.rectangle(overlay, (0, 0), (w, h), bg_color, -1)
            cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

            # Dibujar objeto controlable
            cv2.circle(frame, (obj_x, obj_y), obj_radius, (0, 200, 255), -1)
            cv2.circle(frame, (obj_x, obj_y), obj_radius, (0, 150, 200), 3)

            # HUD
            cv2.putText(frame, f'Gesto: {gesture}', (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
            cv2.putText(frame, f'Dedos: {finger_count}', (20, 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
            cv2.putText(frame, scenes[scene_index], (20, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
            cv2.putText(frame, 'ESC para salir', (w - 200, h - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

            cv2.imshow('BCI Gestos - MediaPipe', frame)

            if cv2.waitKey(5) & 0xFF == 27:  # ESC
                break

    cap.release()
    cv2.destroyAllWindows()


# ============================================================
# Modo 2: Mini-juego de atrapar objetos
# ============================================================

def run_catch_game():
    """
    Mini-juego donde el jugador usa la palma de la mano para
    atrapar objetos que caen desde la parte superior.

    - La posición X de la palma controla un "receptor"
    - Los objetos caen aleatoriamente
    - Cerrar el puño "atrapa" el objeto si está cerca
    - Puntuación y vidas
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo abrir la webcam")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    # Estado del juego
    score = 0
    lives = 3
    objects = []  # [(x, y, color, speed)]
    spawn_timer = 0
    game_over = False

    rng = np.random.default_rng(42)

    with mp_hands.Hands(
        static_image_mode=False,
        max_num_hands=1,
        min_detection_confidence=0.7,
        min_tracking_confidence=0.5
    ) as hands:

        print("Mini-juego: ¡Atrapa los objetos!")
        print("  - Mueve la mano para posicionar el receptor")
        print("  - Cierra el puño para atrapar")
        print("  - ESC para salir")

        while cap.isOpened() and not game_over:
            success, frame = cap.read()
            if not success:
                break

            frame = cv2.flip(frame, 1)
            h, w = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)

            palm_x = w // 2
            is_grabbing = False

            if results.multi_hand_landmarks:
                for hand_landmarks, hand_info in zip(
                    results.multi_hand_landmarks,
                    results.multi_handedness
                ):
                    handedness = hand_info.classification[0].label
                    palm_x, _ = get_palm_center(hand_landmarks, (h, w))

                    gesture, count, _ = detect_gesture(hand_landmarks, (h, w), handedness)
                    is_grabbing = gesture == 'FIST'

                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Spawn objetos
            spawn_timer += 1
            if spawn_timer > 30:
                spawn_timer = 0
                ox = rng.integers(50, w - 50)
                color = tuple(int(c) for c in rng.integers(100, 255, size=3))
                speed = rng.integers(3, 8)
                objects.append([ox, 0, color, speed])

            # Actualizar objetos
            receptor_y = h - 100
            receptor_width = 80
            new_objects = []

            for obj in objects:
                obj[1] += obj[3]

                # Verificar colisión con receptor
                if (obj[1] >= receptor_y - 20 and obj[1] <= receptor_y + 20 and
                        abs(obj[0] - palm_x) < receptor_width):
                    if is_grabbing:
                        score += 10
                        continue  # Atrapado

                # Verificar si cayó al fondo
                if obj[1] > h:
                    lives -= 1
                    if lives <= 0:
                        game_over = True
                    continue

                new_objects.append(obj)
                cv2.circle(frame, (obj[0], obj[1]), 20, obj[2], -1)
                cv2.circle(frame, (obj[0], obj[1]), 22, (255, 255, 255), 2)

            objects = new_objects

            # Dibujar receptor
            rec_color = (0, 255, 0) if is_grabbing else (0, 200, 255)
            cv2.rectangle(frame,
                          (palm_x - receptor_width, receptor_y - 15),
                          (palm_x + receptor_width, receptor_y + 15),
                          rec_color, -1)
            cv2.rectangle(frame,
                          (palm_x - receptor_width, receptor_y - 15),
                          (palm_x + receptor_width, receptor_y + 15),
                          (255, 255, 255), 2)

            # HUD
            cv2.putText(frame, f'Score: {score}', (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
            cv2.putText(frame, f'Lives: {"♥" * lives}', (20, 90),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            if is_grabbing:
                cv2.putText(frame, 'GRAB!', (palm_x - 30, receptor_y - 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.imshow('Catch Game - MediaPipe', frame)

            if cv2.waitKey(5) & 0xFF == 27:
                break

        # Game Over
        if game_over:
            for _ in range(60):  # Mostrar 2 segundos
                success, frame = cap.read()
                if success:
                    frame = cv2.flip(frame, 1)
                    overlay = frame.copy()
                    cv2.rectangle(overlay, (0, 0), (w, h), (0, 0, 100), -1)
                    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
                    cv2.putText(frame, 'GAME OVER', (w // 2 - 200, h // 2),
                                cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 255), 4)
                    cv2.putText(frame, f'Score: {score}', (w // 2 - 100, h // 2 + 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
                    cv2.imshow('Catch Game - MediaPipe', frame)
                    cv2.waitKey(33)

    cap.release()
    cv2.destroyAllWindows()


# ============================================================
# Entry point
# ============================================================

if __name__ == '__main__':
    if '--game' in sys.argv:
        run_catch_game()
    else:
        run_gesture_detection()
