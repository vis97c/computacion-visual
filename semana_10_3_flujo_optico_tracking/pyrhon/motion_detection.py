"""5. Detección de Movimiento.

Calcula magnitud del flujo óptico denso, aplica umbral para crear
máscara de movimiento, segmenta objetos en movimiento y los cuenta.
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from utils import FPSCounter, StageMetrics, ensure_image_write, open_video, resize_for_display

FARNEBACK_PARAMS = dict(
    pyr_scale=0.5, levels=3, winsize=15,
    iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
)

MAG_THRESHOLD = 2.5           # Umbral de magnitud para considerar movimiento
MIN_CONTOUR_AREA = 500        # Área mínima de contorno para contar como objeto
MORPH_KERNEL_SIZE = 7         # Tamaño del kernel morfológico


def run_motion_detection(
    source: str | int,
    output_dir: Path,
    max_frames: int = 600,
    show: bool = True,
) -> StageMetrics:
    """Detecta regiones en movimiento y cuenta objetos móviles."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    kernel = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (MORPH_KERNEL_SIZE, MORPH_KERNEL_SIZE)
    )

    fps_counter = FPSCounter()
    frame_idx = 0
    t_start = time.perf_counter()
    max_objects_seen = 0
    snapshot_saved = False
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None, **FARNEBACK_PARAMS,
        )

        mag, _ = cv2.cartToPolar(flow[..., 0], flow[..., 1])

        # Crear máscara de movimiento
        motion_mask = (mag > MAG_THRESHOLD).astype(np.uint8) * 255

        # Operaciones morfológicas para limpiar ruido
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, kernel)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, kernel)
        motion_mask = cv2.dilate(motion_mask, kernel, iterations=1)

        # Encontrar contornos (objetos en movimiento)
        contours, _ = cv2.findContours(
            motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        moving_objects = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= MIN_CONTOUR_AREA:
                moving_objects.append(cnt)

        n_objects = len(moving_objects)
        max_objects_seen = max(max_objects_seen, n_objects)

        # Visualización
        vis = frame.copy()
        # Overlay de máscara de movimiento en rojo semitransparente
        red_overlay = np.zeros_like(frame)
        red_overlay[motion_mask > 0] = (0, 0, 200)
        vis = cv2.addWeighted(vis, 0.7, red_overlay, 0.4, 0)

        # Dibujar bounding boxes de objetos
        for cnt in moving_objects:
            x, y, w, h = cv2.boundingRect(cnt)
            cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)

        info = f"Movimiento | Objetos: {n_objects} | FPS: {fps:.1f}"
        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > max_frames // 3:
            ensure_image_write(output_dir / "motion_detection_snapshot.jpg", resize_for_display(vis))
            # Guardar máscara por separado
            ensure_image_write(output_dir / "motion_mask_snapshot.jpg", motion_mask)
            snapshot_saved = True

        if show:
            cv2.imshow("Motion Detection", resize_for_display(vis))
            cv2.imshow("Motion Mask", resize_for_display(motion_mask))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Motion Detection")
        cv2.destroyWindow("Motion Mask")

    if frame_idx > 0:
        ensure_image_write(output_dir / "motion_detection_final.jpg", resize_for_display(vis))

    return StageMetrics(
        stage="motion_detection",
        processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={
            "frames_processed": frame_idx,
            "max_objects_detected": max_objects_seen,
            "magnitude_threshold": MAG_THRESHOLD,
            "min_contour_area": MIN_CONTOUR_AREA,
        },
    )
