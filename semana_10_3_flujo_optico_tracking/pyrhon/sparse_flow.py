"""1. Flujo Óptico Disperso con Lucas-Kanade.

Detecta puntos buenos para tracking con goodFeaturesToTrack y los rastrea
frame a frame con calcOpticalFlowPyrLK.  Dibuja trayectorias y re-detecta
puntos cuando se pierden.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from utils import FPSCounter, StageMetrics, ensure_image_write, open_video, resize_for_display

# Parámetros de detección de esquinas
FEATURE_PARAMS = dict(
    maxCorners=200,
    qualityLevel=0.01,
    minDistance=15,
    blockSize=7,
)

# Parámetros de Lucas-Kanade
LK_PARAMS = dict(
    winSize=(21, 21),
    maxLevel=3,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)

# Umbral mínimo de puntos antes de re-detectar
MIN_POINTS = 30

# Colores para las trayectorias (paleta cíclica)
COLORS = np.random.default_rng(42).integers(80, 255, (500, 3)).tolist()


def _detect_points(gray: np.ndarray) -> np.ndarray:
    pts = cv2.goodFeaturesToTrack(gray, mask=None, **FEATURE_PARAMS)
    return pts if pts is not None else np.empty((0, 1, 2), dtype=np.float32)


def run_lucas_kanade(
    source: str | int,
    output_dir: Path,
    max_frames: int = 600,
    show: bool = True,
) -> StageMetrics:
    """Ejecuta flujo óptico disperso Lucas-Kanade y guarda resultados."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    prev_pts = _detect_points(prev_gray)

    # Máscara acumulada de trayectorias
    trail_mask = np.zeros_like(first_frame)
    fps_counter = FPSCounter()
    frame_idx = 0
    total_redetections = 0
    snapshot_saved = False
    t_start = time.perf_counter()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

        if len(prev_pts) == 0:
            prev_pts = _detect_points(gray)
            prev_gray = gray.copy()
            total_redetections += 1
            continue

        # Calcular flujo óptico
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            prev_gray, gray, prev_pts, None, **LK_PARAMS
        )

        if next_pts is None or status is None:
            prev_pts = _detect_points(gray)
            prev_gray = gray.copy()
            total_redetections += 1
            continue

        # Filtrar puntos válidos
        good_mask = status.ravel() == 1
        good_new = next_pts[good_mask]
        good_old = prev_pts[good_mask]

        # Dibujar trayectorias y vectores de movimiento
        vis = frame.copy()
        for i, (new, old) in enumerate(zip(good_new, good_old)):
            a, b = new.ravel().astype(int)
            c, d = old.ravel().astype(int)
            color = COLORS[i % len(COLORS)]
            trail_mask = cv2.line(trail_mask, (a, b), (c, d), color, 2)
            vis = cv2.circle(vis, (a, b), 4, color, -1)
            # Vector de movimiento
            cv2.arrowedLine(vis, (c, d), (a, b), (0, 255, 0), 1, tipLength=0.3)

        vis = cv2.add(vis, trail_mask)

        # Info en pantalla
        cv2.putText(vis, f"LK Sparse | Pts: {len(good_new)} | FPS: {fps:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        # Re-detección si se pierden demasiados puntos
        if len(good_new) < MIN_POINTS:
            prev_pts = _detect_points(gray)
            trail_mask = np.zeros_like(first_frame)
            total_redetections += 1
        else:
            prev_pts = good_new.reshape(-1, 1, 2)

        prev_gray = gray.copy()

        # Guardar snapshot a mitad del video
        if not snapshot_saved and frame_idx > max_frames // 3:
            ensure_image_write(output_dir / "lucas_kanade_snapshot.jpg", resize_for_display(vis))
            snapshot_saved = True

        if show:
            cv2.imshow("Lucas-Kanade Sparse Flow", resize_for_display(vis))
            if cv2.waitKey(1) & 0xFF == 27:  # ESC
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Lucas-Kanade Sparse Flow")

    # Guardar frame final
    if frame_idx > 0:
        ensure_image_write(output_dir / "lucas_kanade_final.jpg", resize_for_display(vis))

    return StageMetrics(
        stage="lucas_kanade_sparse",
        processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={
            "frames_processed": frame_idx,
            "redetections": total_redetections,
        },
    )
