"""4. Estimación de Movimiento de Cámara.

Analiza flujo global vs local para detectar movimientos de cámara:
pan, tilt, zoom.  Calcula velocidad angular y traslación estimada.
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np

from utils import FPSCounter, StageMetrics, ensure_image_write, open_video, resize_for_display

FEATURE_PARAMS = dict(maxCorners=300, qualityLevel=0.01, minDistance=20, blockSize=7)
LK_PARAMS = dict(
    winSize=(21, 21),
    maxLevel=3,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)


def _classify_motion(
    dx_mean: float, dy_mean: float, scale: float, threshold: float = 1.5
) -> str:
    """Clasifica el tipo de movimiento de cámara."""
    labels = []
    if abs(dx_mean) > threshold:
        labels.append("PAN " + ("→" if dx_mean > 0 else "←"))
    if abs(dy_mean) > threshold:
        labels.append("TILT " + ("↓" if dy_mean > 0 else "↑"))
    if abs(scale - 1.0) > 0.01:
        labels.append("ZOOM " + ("IN" if scale > 1.0 else "OUT"))
    return " + ".join(labels) if labels else "ESTATICO"


def run_camera_motion(
    source: str | int,
    output_dir: Path,
    max_frames: int = 600,
    show: bool = True,
) -> StageMetrics:
    """Estima movimiento de cámara analizando flujo óptico global."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    h, w = prev_gray.shape
    # FOV estimado (grados) – asumimos ~60° horizontal
    fov_h = 60.0
    px_per_deg = w / fov_h

    fps_counter = FPSCounter()
    frame_idx = 0
    t_start = time.perf_counter()
    motion_log = []
    snapshot_saved = False
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

        # Detectar puntos en frame anterior
        pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
        if pts is None or len(pts) < 10:
            prev_gray = gray.copy()
            continue

        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **LK_PARAMS)
        if next_pts is None:
            prev_gray = gray.copy()
            continue

        good_old = pts[status.ravel() == 1]
        good_new = next_pts[status.ravel() == 1]

        if len(good_old) < 6:
            prev_gray = gray.copy()
            continue

        # Flujo global (mediana robusta)
        flow_vectors = good_new.reshape(-1, 2) - good_old.reshape(-1, 2)
        dx_mean = float(np.median(flow_vectors[:, 0]))
        dy_mean = float(np.median(flow_vectors[:, 1]))

        # Estimación de zoom con transformación afín
        try:
            mat, inliers = cv2.estimateAffinePartial2D(good_old, good_new)
            if mat is not None:
                scale = float(np.sqrt(mat[0, 0] ** 2 + mat[1, 0] ** 2))
                rotation_rad = float(np.arctan2(mat[1, 0], mat[0, 0]))
            else:
                scale, rotation_rad = 1.0, 0.0
        except cv2.error:
            scale, rotation_rad = 1.0, 0.0

        # Velocidad angular (°/frame)
        angular_vel_x = dx_mean / px_per_deg
        angular_vel_y = dy_mean / px_per_deg

        motion_type = _classify_motion(dx_mean, dy_mean, scale)
        motion_log.append(motion_type)

        # Visualización
        vis = frame.copy()
        center = (w // 2, h // 2)

        # Dibujar vector global de movimiento
        end_pt = (int(center[0] + dx_mean * 5), int(center[1] + dy_mean * 5))
        cv2.arrowedLine(vis, center, end_pt, (0, 255, 0), 3, tipLength=0.3)
        cv2.circle(vis, center, 6, (0, 255, 0), -1)

        # Dibujar flujo de cada punto
        for old, new in zip(good_old, good_new):
            a, b = new.ravel().astype(int)
            c, d = old.ravel().astype(int)
            cv2.arrowedLine(vis, (c, d), (a, b), (100, 100, 255), 1, tipLength=0.3)

        # Panel de información
        info_lines = [
            f"Camara: {motion_type}",
            f"Pan: {dx_mean:+.1f}px  Tilt: {dy_mean:+.1f}px",
            f"Zoom: {scale:.3f}  Rot: {np.degrees(rotation_rad):+.2f} deg",
            f"Vel angular: X={angular_vel_x:+.2f} Y={angular_vel_y:+.2f} deg/f",
            f"FPS: {fps:.1f}",
        ]
        for i, line in enumerate(info_lines):
            cv2.putText(vis, line, (10, 30 + i * 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)

        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > max_frames // 3:
            ensure_image_write(output_dir / "camera_motion_snapshot.jpg", resize_for_display(vis))
            snapshot_saved = True

        if show:
            cv2.imshow("Camera Motion Estimation", resize_for_display(vis))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Camera Motion Estimation")

    if frame_idx > 0:
        ensure_image_write(output_dir / "camera_motion_final.jpg", resize_for_display(vis))

    return StageMetrics(
        stage="camera_motion_estimation",
        processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={
            "frames_processed": frame_idx,
            "motion_summary": dict(
                zip(*np.unique(motion_log, return_counts=True))
            ) if motion_log else {},
        },
    )
