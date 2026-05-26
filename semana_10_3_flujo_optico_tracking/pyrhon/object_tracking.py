"""3. Tracking de Objetos.

Selección manual de ROI, rastreo con Lucas-Kanade sobre puntos dentro
del bounding box, manejo de oclusiones parciales y detección de pérdida.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np

from utils import FPSCounter, StageMetrics, ensure_image_write, open_video, resize_for_display

FEATURE_PARAMS = dict(maxCorners=150, qualityLevel=0.02, minDistance=10, blockSize=7)
LK_PARAMS = dict(
    winSize=(21, 21),
    maxLevel=3,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)

# Umbrales de tracking
LOST_RATIO = 0.15          # Si queda < 15 % de puntos originales → perdido
OCCLUSION_RATIO = 0.40     # Si queda < 40 % → oclusión parcial
MAX_BOX_GROWTH = 3.0       # Crecimiento máximo permitido del bbox


def _detect_in_roi(gray: np.ndarray, bbox: Tuple[int, int, int, int]) -> np.ndarray:
    x, y, w, h = bbox
    mask = np.zeros(gray.shape, dtype=np.uint8)
    mask[y:y + h, x:x + w] = 255
    pts = cv2.goodFeaturesToTrack(gray, mask=mask, **FEATURE_PARAMS)
    return pts if pts is not None else np.empty((0, 1, 2), dtype=np.float32)


def _bbox_from_points(pts: np.ndarray) -> Tuple[int, int, int, int]:
    x, y, w, h = cv2.boundingRect(pts.reshape(-1, 1, 2).astype(np.float32))
    return int(x), int(y), int(w), int(h)


def run_object_tracking(
    source: str | int,
    output_dir: Path,
    max_frames: int = 600,
    show: bool = True,
) -> StageMetrics:
    """Rastreo de objeto seleccionado manualmente."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")

    display = resize_for_display(first_frame)
    print("[INFO] Selecciona ROI con el mouse y presiona ENTER / ESPACIO.")
    roi = cv2.selectROI("Seleccionar Objeto", display, fromCenter=False, showCrosshair=True)
    cv2.destroyWindow("Seleccionar Objeto")

    if roi[2] == 0 or roi[3] == 0:
        cap.release()
        return StageMetrics(stage="object_tracking", processing_ms=0, note="ROI vacía, cancelado.")

    # Escalar ROI al tamaño original si se redimensionó
    scale_x = first_frame.shape[1] / display.shape[1]
    scale_y = first_frame.shape[0] / display.shape[0]
    bbox = (
        int(roi[0] * scale_x), int(roi[1] * scale_y),
        int(roi[2] * scale_x), int(roi[3] * scale_y),
    )

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    prev_pts = _detect_in_roi(prev_gray, bbox)
    initial_count = max(len(prev_pts), 1)
    initial_area = bbox[2] * bbox[3]

    fps_counter = FPSCounter()
    frame_idx = 0
    lost_count = 0
    occlusion_count = 0
    t_start = time.perf_counter()
    tracking_active = True
    snapshot_saved = False
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()
        vis = frame.copy()

        if not tracking_active or len(prev_pts) == 0:
            cv2.putText(vis, "TRACKING PERDIDO - Presiona 'r' para re-seleccionar",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            if show:
                cv2.imshow("Object Tracking", resize_for_display(vis))
                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break
                if key == ord("r"):
                    display = resize_for_display(frame)
                    roi = cv2.selectROI("Re-seleccionar", display, False, True)
                    cv2.destroyWindow("Re-seleccionar")
                    if roi[2] > 0 and roi[3] > 0:
                        bbox = (
                            int(roi[0] * scale_x), int(roi[1] * scale_y),
                            int(roi[2] * scale_x), int(roi[3] * scale_y),
                        )
                        prev_pts = _detect_in_roi(gray, bbox)
                        initial_count = max(len(prev_pts), 1)
                        initial_area = bbox[2] * bbox[3]
                        tracking_active = True
            prev_gray = gray.copy()
            continue

        # Calcular flujo
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, prev_pts, None, **LK_PARAMS)
        if next_pts is None or status is None:
            tracking_active = False
            lost_count += 1
            prev_gray = gray.copy()
            continue

        good = next_pts[status.ravel() == 1]
        ratio = len(good) / initial_count

        # Evaluar estado
        status_text = "OK"
        color = (0, 255, 0)

        if ratio < LOST_RATIO:
            tracking_active = False
            lost_count += 1
            status_text = "PERDIDO"
            color = (0, 0, 255)
        elif ratio < OCCLUSION_RATIO:
            occlusion_count += 1
            status_text = "OCLUSION PARCIAL"
            color = (0, 165, 255)

        if len(good) >= 2:
            bbox = _bbox_from_points(good)
            # Verificar crecimiento anómalo del bbox
            area = bbox[2] * bbox[3]
            if area > initial_area * MAX_BOX_GROWTH:
                tracking_active = False
                lost_count += 1
                status_text = "PERDIDO (bbox explotó)"
                color = (0, 0, 255)

        # Dibujar
        x, y, w, h = bbox
        cv2.rectangle(vis, (x, y), (x + w, y + h), color, 2)
        for pt in good:
            cx, cy = pt.ravel().astype(int)
            cv2.circle(vis, (cx, cy), 3, (255, 255, 0), -1)

        info = f"Track: {status_text} | Pts: {len(good)}/{initial_count} | FPS: {fps:.1f}"
        cv2.putText(vis, info, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        prev_pts = good.reshape(-1, 1, 2)
        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > 10:
            ensure_image_write(output_dir / "tracking_snapshot.jpg", resize_for_display(vis))
            snapshot_saved = True

        if show:
            cv2.imshow("Object Tracking", resize_for_display(vis))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Object Tracking")

    if frame_idx > 0:
        ensure_image_write(output_dir / "tracking_final.jpg", resize_for_display(vis))

    return StageMetrics(
        stage="object_tracking",
        processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={
            "frames_processed": frame_idx,
            "times_lost": lost_count,
            "occlusion_events": occlusion_count,
        },
    )
