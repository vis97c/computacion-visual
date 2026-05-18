"""2. Flujo Óptico Denso con Farnebäck.

Calcula flujo denso frame a frame y lo visualiza con codificación HSV:
  - Matiz (Hue)  → dirección del flujo
  - Valor (Value) → magnitud del flujo
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from utils import FPSCounter, StageMetrics, ensure_image_write, open_video, resize_for_display

# Parámetros de Farnebäck
FARNEBACK_PARAMS = dict(
    pyr_scale=0.5,
    levels=3,
    winsize=15,
    iterations=3,
    poly_n=5,
    poly_sigma=1.2,
    flags=0,
)


def flow_to_hsv(flow: np.ndarray) -> np.ndarray:
    """Convierte mapa de flujo (H×W×2) a imagen BGR con codificación HSV."""
    mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
    hsv = np.zeros((*flow.shape[:2], 3), dtype=np.uint8)
    hsv[..., 0] = ang * 180 / np.pi / 2          # Hue: dirección
    hsv[..., 1] = 255                              # Saturación máxima
    hsv[..., 2] = cv2.normalize(mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)  # Value: magnitud
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)


def run_dense_flow(
    source: str | int,
    output_dir: Path,
    max_frames: int = 600,
    show: bool = True,
) -> StageMetrics:
    """Ejecuta flujo óptico denso Farnebäck y guarda resultados."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

    fps_counter = FPSCounter()
    frame_idx = 0
    snapshot_saved = False
    t_start = time.perf_counter()
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

        flow = cv2.calcOpticalFlowFarneback(
            prev_gray, gray, None,
            **FARNEBACK_PARAMS,
        )

        flow_bgr = flow_to_hsv(flow)

        # Composición: frame original + flujo superpuesto
        vis = cv2.addWeighted(frame, 0.5, flow_bgr, 0.7, 0)
        cv2.putText(vis, f"Farneback Dense | FPS: {fps:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > max_frames // 3:
            ensure_image_write(output_dir / "dense_flow_snapshot.jpg", resize_for_display(vis))
            ensure_image_write(output_dir / "dense_flow_hsv.jpg", resize_for_display(flow_bgr))
            snapshot_saved = True

        if show:
            cv2.imshow("Farneback Dense Flow", resize_for_display(vis))
            cv2.imshow("Flow HSV", resize_for_display(flow_bgr))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Farneback Dense Flow")
        cv2.destroyWindow("Flow HSV")

    if frame_idx > 0:
        ensure_image_write(output_dir / "dense_flow_final.jpg", resize_for_display(vis))

    return StageMetrics(
        stage="farneback_dense",
        processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={"frames_processed": frame_idx},
    )
