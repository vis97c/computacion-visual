"""
Módulo de Detección de Gestos con MediaPipe
=============================================

Utilidades para:
- Detección de landmarks de manos
- Conteo de dedos extendidos
- Medición de distancia entre dedos
- Reconocimiento de gestos (puño, palma, pinch, peace, etc.)
"""

import cv2
import numpy as np
import mediapipe as mp

# ============================================================
# Inicialización de MediaPipe
# ============================================================

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

# Índices de los tips de cada dedo en el modelo MediaPipe
FINGER_TIPS = {
    'thumb':  4,
    'index':  8,
    'middle': 12,
    'ring':   16,
    'pinky':  20,
}

# Índices de las articulaciones PIP (segunda falange)
FINGER_PIPS = {
    'thumb':  3,
    'index':  6,
    'middle': 10,
    'ring':   14,
    'pinky':  18,
}

# Índices de las articulaciones MCP (nudillos)
FINGER_MCPS = {
    'thumb':  2,
    'index':  5,
    'middle': 9,
    'ring':   13,
    'pinky':  17,
}


def get_landmark_coords(hand_landmarks, img_shape):
    """
    Extrae coordenadas (x, y) de todos los landmarks en píxeles.

    Args:
        hand_landmarks: resultado de MediaPipe Hands
        img_shape: (height, width) de la imagen

    Returns:
        dict con id → (x, y) para los 21 landmarks
    """
    h, w = img_shape[:2]
    coords = {}
    for idx, lm in enumerate(hand_landmarks.landmark):
        coords[idx] = (int(lm.x * w), int(lm.y * h))
    return coords


def count_fingers(hand_landmarks, img_shape, handedness='Right'):
    """
    Cuenta el número de dedos extendidos.

    Lógica:
    - Pulgar: compara posición X del tip vs articulación IP
      (invertido para mano izquierda)
    - Otros dedos: compara posición Y del tip vs articulación PIP
      (tip más arriba = dedo extendido)

    Args:
        hand_landmarks: landmarks de MediaPipe
        img_shape: dimensiones de la imagen
        handedness: 'Right' o 'Left'

    Returns:
        count: número de dedos extendidos (0-5)
        fingers: dict con estado de cada dedo (True/False)
    """
    coords = get_landmark_coords(hand_landmarks, img_shape)
    fingers = {}

    # Pulgar: comparar en eje X
    # Para mano derecha: tip a la izquierda del IP = cerrado
    # Para mano izquierda: invertido
    thumb_tip = coords[FINGER_TIPS['thumb']]
    thumb_ip = coords[FINGER_PIPS['thumb']]

    if handedness == 'Right':
        fingers['thumb'] = thumb_tip[0] < thumb_ip[0]
    else:
        fingers['thumb'] = thumb_tip[0] > thumb_ip[0]

    # Otros dedos: comparar en eje Y (menor Y = más arriba)
    for finger in ['index', 'middle', 'ring', 'pinky']:
        tip = coords[FINGER_TIPS[finger]]
        pip = coords[FINGER_PIPS[finger]]
        fingers[finger] = tip[1] < pip[1]

    count = sum(fingers.values())
    return count, fingers


def finger_distance(hand_landmarks, img_shape, finger_a='thumb', finger_b='index'):
    """
    Calcula la distancia en píxeles entre las puntas de dos dedos.

    Args:
        finger_a, finger_b: nombres de dedos ('thumb', 'index', etc.)

    Returns:
        distance: distancia euclidiana en píxeles
        point_a, point_b: coordenadas de las puntas
    """
    coords = get_landmark_coords(hand_landmarks, img_shape)
    pa = coords[FINGER_TIPS[finger_a]]
    pb = coords[FINGER_TIPS[finger_b]]
    dist = np.sqrt((pa[0] - pb[0]) ** 2 + (pa[1] - pb[1]) ** 2)
    return dist, pa, pb


def detect_gesture(hand_landmarks, img_shape, handedness='Right'):
    """
    Reconoce gestos predefinidos basándose en los dedos extendidos
    y la distancia entre ellos.

    Returns:
        gesture_name: nombre del gesto detectado
        count: número de dedos extendidos
        fingers: estado de cada dedo
    """
    count, fingers = count_fingers(hand_landmarks, img_shape, handedness)
    dist_thumb_index, _, _ = finger_distance(hand_landmarks, img_shape, 'thumb', 'index')

    # Clasificación de gestos
    if count == 0:
        gesture = 'FIST'
    elif count == 5:
        gesture = 'OPEN_PALM'
    elif count == 1 and fingers['index']:
        gesture = 'POINTING'
    elif count == 2 and fingers['index'] and fingers['middle']:
        gesture = 'PEACE'
    elif count == 3 and fingers['index'] and fingers['middle'] and fingers['ring']:
        gesture = 'THREE'
    elif count == 1 and fingers['thumb']:
        gesture = 'THUMBS_UP'
    elif dist_thumb_index < 40:
        gesture = 'PINCH'
    else:
        gesture = f'{count}_FINGERS'

    return gesture, count, fingers


def get_palm_center(hand_landmarks, img_shape):
    """
    Calcula el centro de la palma como promedio de los landmarks
    de la base de los dedos (MCPs).

    Returns:
        (cx, cy): centro de la palma en píxeles
    """
    coords = get_landmark_coords(hand_landmarks, img_shape)
    mcp_ids = [0, 5, 9, 13, 17]  # wrist + MCPs
    cx = int(np.mean([coords[i][0] for i in mcp_ids]))
    cy = int(np.mean([coords[i][1] for i in mcp_ids]))
    return cx, cy


def draw_hand_info(frame, hand_landmarks, gesture, count, handedness='Right'):
    """
    Dibuja landmarks, conexiones y texto informativo sobre el frame.
    """
    h, w = frame.shape[:2]

    # Dibujar landmarks y conexiones de MediaPipe
    mp_drawing.draw_landmarks(
        frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
        mp_styles.get_default_hand_landmarks_style(),
        mp_styles.get_default_hand_connections_style()
    )

    # Texto informativo
    coords = get_landmark_coords(hand_landmarks, (h, w))
    wrist = coords[0]

    cv2.putText(frame, f'{gesture}', (wrist[0] - 30, wrist[1] + 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    cv2.putText(frame, f'Dedos: {count}', (wrist[0] - 30, wrist[1] + 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame
