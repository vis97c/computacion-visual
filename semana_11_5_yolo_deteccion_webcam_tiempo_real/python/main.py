from __future__ import annotations

import argparse
import time
from collections import Counter, deque
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

COCO_CLASSES = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck', 'boat',
    'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench', 'bird', 'cat',
    'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra', 'giraffe', 'backpack',
    'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee', 'skis', 'snowboard', 'sports ball',
    'kite', 'baseball bat', 'baseball glove', 'skateboard', 'surfboard', 'tennis racket',
    'bottle', 'wine glass', 'cup', 'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple',
    'sandwich', 'orange', 'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair',
    'couch', 'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush',
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Deteccion de objetos en tiempo real con YOLOv8 y webcam.'
    )
    parser.add_argument('--model', default='yolov8n.pt', help='Ruta o nombre del modelo YOLO.')
    parser.add_argument(
        '--source',
        default=0,
        type=lambda value: int(value) if value.isdigit() else value,
        help='Indice de webcam o ruta de video.',
    )
    parser.add_argument('--conf', type=float, default=0.4, help='Umbral de confianza inicial.')
    parser.add_argument('--imgsz', type=int, default=640, help='Tamano de inferencia.')
    parser.add_argument(
        '--classes',
        nargs='*',
        default=['person', 'cell phone'],
        help='Clases COCO a mostrar en el bonus. Si queda vacio, se muestran todas.',
    )
    parser.add_argument(
        '--display-all',
        action='store_true',
        help='Muestra todas las detecciones en lugar de limitar a las clases seleccionadas.',
    )
    parser.add_argument(
        '--history-size',
        type=int,
        default=120,
        help='Cantidad de FPS recientes para el promedio movil.',
    )
    return parser.parse_args()


def load_model(model_name: str) -> YOLO:
    try:
        return YOLO(model_name)
    except Exception as exc:  # pragma: no cover - runtime fallback
        raise RuntimeError(
            f'No se pudo cargar el modelo YOLO "{model_name}". Verifica que el archivo exista '
            'o que el entorno tenga acceso para descargar los pesos.'
        ) from exc


def open_capture(source: str | int) -> cv2.VideoCapture:
    capture = cv2.VideoCapture(source)
    if not capture.isOpened():
        raise RuntimeError('No se pudo abrir la webcam o el archivo de video de entrada.')
    return capture


def map_class_names(selected: list[str]) -> set[str]:
    normalized = {name.strip().lower() for name in selected if name.strip()}
    if not normalized:
        return set()
    return normalized


def draw_hud(frame: np.ndarray, fps: float, avg_latency_ms: float, conf: float, active_classes: set[str], total_count: int, counts: Counter[str]) -> None:
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (frame.shape[1], 105), (18, 18, 24), -1)
    cv2.addWeighted(overlay, 0.72, frame, 0.28, 0, frame)

    title = 'YOLOv8 | Deteccion en tiempo real con webcam'
    subtitle = f'FPS: {fps:5.1f} | Latencia: {avg_latency_ms:5.1f} ms | Confianza: {conf:.2f}'
    if active_classes:
        class_text = 'Bonus visible: ' + ', '.join(sorted(active_classes))
    else:
        class_text = 'Bonus visible: todas las clases'

    cv2.putText(frame, title, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2, cv2.LINE_AA)
    cv2.putText(frame, subtitle, (20, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (130, 220, 130), 2, cv2.LINE_AA)
    cv2.putText(frame, class_text, (20, 84), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

    y = 30
    x = frame.shape[1] - 280
    cv2.rectangle(frame, (x - 10, 15), (frame.shape[1] - 15, 255), (25, 25, 30), -1)
    cv2.putText(frame, f'Total objetos: {total_count}', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    y += 30
    for class_name, value in counts.most_common(6):
        cv2.putText(frame, f'{class_name}: {value}', (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 80), 2, cv2.LINE_AA)
        y += 26


def main() -> None:
    args = parse_args()
    model = load_model(args.model)
    capture = open_capture(args.source)
    selected_classes = map_class_names(args.classes)
    display_all = args.display_all or not selected_classes

    fps_history: deque[float] = deque(maxlen=max(10, args.history_size))
    latency_history: deque[float] = deque(maxlen=max(10, args.history_size))
    confidence = args.conf

    window_name = 'Taller YOLO Webcam'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    try:
        while True:
            frame_start = time.perf_counter()
            ok, frame = capture.read()
            if not ok:
                print('No se pudo leer un frame de la fuente de video.')
                break

            results = model.predict(frame, imgsz=args.imgsz, conf=confidence, verbose=False)
            annotated = frame.copy()
            counts: Counter[str] = Counter()
            total_count = 0

            if results:
                result = results[0]
                boxes = result.boxes
                if boxes is not None and len(boxes) > 0:
                    for box in boxes:
                        class_id = int(box.cls.item())
                        class_name = result.names[class_id]
                        normalized_name = class_name.lower()
                        if not display_all and normalized_name not in selected_classes:
                            continue

                        total_count += 1
                        counts[normalized_name] += 1

                        x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                        score = float(box.conf.item())
                        color = (60, 180, 255) if normalized_name in {'person', 'cell phone'} else (180, 255, 90)
                        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                        label = f'{class_name} {score:.2f}'
                        (text_w, text_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 2)
                        label_y1 = max(0, y1 - text_h - baseline - 6)
                        cv2.rectangle(annotated, (x1, label_y1), (x1 + text_w + 8, y1), color, -1)
                        cv2.putText(
                            annotated,
                            label,
                            (x1 + 4, y1 - baseline - 4),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.55,
                            (0, 0, 0),
                            2,
                            cv2.LINE_AA,
                        )

            frame_end = time.perf_counter()
            latency_ms = (frame_end - frame_start) * 1000.0
            fps = 1.0 / max(frame_end - frame_start, 1e-6)
            fps_history.append(fps)
            latency_history.append(latency_ms)

            avg_fps = sum(fps_history) / len(fps_history)
            avg_latency = sum(latency_history) / len(latency_history)
            draw_hud(annotated, avg_fps, avg_latency, confidence, selected_classes if not display_all else set(), total_count, counts)

            cv2.imshow(window_name, annotated)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q'):
                break
            if key == ord('+'):
                confidence = min(0.8, confidence + 0.05)
            if key == ord('-'):
                confidence = max(0.3, confidence - 0.05)
            if key == ord('a'):
                display_all = not display_all

    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
