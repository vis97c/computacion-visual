"""7. Bonus – Estabilización de video, motion blur artístico y detección de gestos.

- Estabilización: compensa movimiento global de cámara frame a frame.
- Motion blur artístico: acumula flujo denso para efecto de estelas.
- Gestos: analiza trayectorias de puntos para detectar swipes.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import List

import cv2
import numpy as np

from utils import FPSCounter, StageMetrics, ensure_image_write, open_video, resize_for_display

FEATURE_PARAMS = dict(maxCorners=300, qualityLevel=0.01, minDistance=20, blockSize=7)
LK_PARAMS = dict(
    winSize=(21, 21), maxLevel=3,
    criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01),
)
FARNEBACK_PARAMS = dict(
    pyr_scale=0.5, levels=3, winsize=15,
    iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
)


# ===================================================================
# A) Estabilización de video
# ===================================================================

def run_stabilization(
    source: str | int,
    output_dir: Path,
    max_frames: int = 300,
    show: bool = True,
) -> StageMetrics:
    """Estabiliza video compensando movimiento global con transformaciones afines."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")

    h, w = first_frame.shape[:2]
    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)

    # Acumular transformación
    cum_dx, cum_dy, cum_da = 0.0, 0.0, 0.0
    smooth_dx, smooth_dy, smooth_da = 0.0, 0.0, 0.0
    alpha = 0.85  # Factor de suavizado

    fps_counter = FPSCounter()
    frame_idx = 0
    t_start = time.perf_counter()
    snapshot_saved = False
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

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

        if len(good_old) < 4:
            prev_gray = gray.copy()
            continue

        mat, _ = cv2.estimateAffinePartial2D(good_old, good_new)
        if mat is None:
            prev_gray = gray.copy()
            continue

        dx = mat[0, 2]
        dy = mat[1, 2]
        da = np.arctan2(mat[1, 0], mat[0, 0])

        cum_dx += dx
        cum_dy += dy
        cum_da += da

        # Suavizado exponencial
        smooth_dx = alpha * smooth_dx + (1 - alpha) * cum_dx
        smooth_dy = alpha * smooth_dy + (1 - alpha) * cum_dy
        smooth_da = alpha * smooth_da + (1 - alpha) * cum_da

        # Corrección
        diff_dx = smooth_dx - cum_dx
        diff_dy = smooth_dy - cum_dy
        diff_da = smooth_da - cum_da

        cos_a = np.cos(diff_da)
        sin_a = np.sin(diff_da)
        correction = np.float64([
            [cos_a, -sin_a, diff_dx],
            [sin_a,  cos_a, diff_dy],
        ])

        stabilized = cv2.warpAffine(frame, correction, (w, h))

        # Lado a lado
        vis = np.hstack([frame, stabilized])
        cv2.putText(vis, "Original", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(vis, f"Estabilizado | FPS: {fps:.1f}", (w + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > 10:
            ensure_image_write(output_dir / "stabilization_snapshot.jpg", resize_for_display(vis, 1280))
            snapshot_saved = True

        if show:
            cv2.imshow("Video Stabilization", resize_for_display(vis, 1280))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Video Stabilization")

    if frame_idx > 0:
        ensure_image_write(output_dir / "stabilization_final.jpg", resize_for_display(vis, 1280))

    return StageMetrics(
        stage="bonus_stabilization", processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={"frames_processed": frame_idx},
    )


# ===================================================================
# B) Motion blur artístico
# ===================================================================

def run_motion_blur(
    source: str | int,
    output_dir: Path,
    max_frames: int = 300,
    show: bool = True,
) -> StageMetrics:
    """Crea efecto de motion blur artístico acumulando flujo denso."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    accum = np.zeros(first_frame.shape, dtype=np.float64)
    decay = 0.92

    fps_counter = FPSCounter()
    frame_idx = 0
    t_start = time.perf_counter()
    snapshot_saved = False
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, **FARNEBACK_PARAMS)
        mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        motion_mask = (mag > 1.5).astype(np.float64)

        # Acumular solo zonas con movimiento
        accum = accum * decay + frame.astype(np.float64) * motion_mask[..., None] * (1 - decay)

        vis = cv2.addWeighted(frame, 0.6, np.clip(accum, 0, 255).astype(np.uint8), 0.6, 0)
        cv2.putText(vis, f"Motion Blur Art | FPS: {fps:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > max_frames // 3:
            ensure_image_write(output_dir / "motion_blur_snapshot.jpg", resize_for_display(vis))
            snapshot_saved = True

        if show:
            cv2.imshow("Motion Blur Art", resize_for_display(vis))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Motion Blur Art")

    if frame_idx > 0:
        ensure_image_write(output_dir / "motion_blur_final.jpg", resize_for_display(vis))

    return StageMetrics(
        stage="bonus_motion_blur", processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={"frames_processed": frame_idx},
    )


# ===================================================================
# C) Detección de gestos
# ===================================================================

GESTURE_NAMES = {
    "right": "→ Swipe Derecha",
    "left": "← Swipe Izquierda",
    "up": "↑ Swipe Arriba",
    "down": "↓ Swipe Abajo",
}


def _classify_gesture(trajectory: np.ndarray, min_displacement: float = 60.0) -> str:
    """Clasifica un gesto a partir de la trayectoria acumulada de un punto."""
    if len(trajectory) < 5:
        return ""
    start = trajectory[0]
    end = trajectory[-1]
    delta = end - start
    dist = np.linalg.norm(delta)
    if dist < min_displacement:
        return ""
    if abs(delta[0]) > abs(delta[1]):
        return "right" if delta[0] > 0 else "left"
    return "down" if delta[1] > 0 else "up"


def run_gesture_detection(
    source: str | int,
    output_dir: Path,
    max_frames: int = 600,
    show: bool = True,
) -> StageMetrics:
    """Detecta gestos (swipes) usando trayectorias de flujo óptico."""
    cap = open_video(source)
    output_dir.mkdir(parents=True, exist_ok=True)

    ret, first_frame = cap.read()
    if not ret:
        raise RuntimeError("No se pudo leer el primer frame.")

    prev_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
    pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
    if pts is None:
        pts = np.empty((0, 1, 2), dtype=np.float32)

    # Guardar trayectorias por punto
    trajectories: List[List[np.ndarray]] = [[p.ravel().copy()] for p in pts]
    TRAIL_LEN = 30

    fps_counter = FPSCounter()
    frame_idx = 0
    t_start = time.perf_counter()
    detected_gestures: List[str] = []
    current_gesture = ""
    gesture_cooldown = 0
    snapshot_saved = False
    vis = first_frame.copy()

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        fps = fps_counter.tick()

        if len(pts) == 0:
            pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
            if pts is None:
                pts = np.empty((0, 1, 2), dtype=np.float32)
            trajectories = [[p.ravel().copy()] for p in pts]
            prev_gray = gray.copy()
            continue

        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **LK_PARAMS)
        if next_pts is None or status is None:
            prev_gray = gray.copy()
            continue

        mask = status.ravel() == 1
        good_new = next_pts[mask]

        # Actualizar trayectorias
        new_trajectories: List[List[np.ndarray]] = []
        idx = 0
        for i, m in enumerate(mask):
            if m:
                if idx < len(trajectories):
                    traj = trajectories[idx]
                else:
                    traj = []
                traj.append(good_new[idx - (idx - idx)].ravel().copy())  # fix below
                idx_for_new = sum(mask[:i+1]) - 1
                if i < len(trajectories):
                    traj = trajectories[i]
                    traj.append(good_new[idx_for_new].ravel().copy())
                    if len(traj) > TRAIL_LEN:
                        traj.pop(0)
                    new_trajectories.append(traj)

        # Simplificar: reconstruir trayectorias
        new_trajectories = []
        j = 0
        for i in range(len(mask)):
            if mask[i]:
                if i < len(trajectories):
                    traj = trajectories[i]
                else:
                    traj = [pts[i].ravel().copy()]
                traj.append(good_new[j].ravel().copy())
                if len(traj) > TRAIL_LEN:
                    traj.pop(0)
                new_trajectories.append(traj)
                j += 1

        trajectories = new_trajectories

        # Analizar trayectorias para gestos
        if gesture_cooldown > 0:
            gesture_cooldown -= 1
        else:
            gesture_votes: dict = {}
            for traj in trajectories:
                arr = np.array(traj)
                g = _classify_gesture(arr, min_displacement=50.0)
                if g:
                    gesture_votes[g] = gesture_votes.get(g, 0) + 1

            if gesture_votes:
                dominant = max(gesture_votes, key=gesture_votes.get)  # type: ignore[arg-type]
                # Requiere que al menos 20% de los puntos voten igual
                if gesture_votes[dominant] >= max(5, len(trajectories) * 0.2):
                    current_gesture = GESTURE_NAMES.get(dominant, dominant)
                    detected_gestures.append(dominant)
                    gesture_cooldown = 20  # Esperar 20 frames antes de siguiente detección
                    # Reset trayectorias
                    pts_new = cv2.goodFeaturesToTrack(gray, mask=None, **FEATURE_PARAMS)
                    if pts_new is not None:
                        pts = pts_new
                        trajectories = [[p.ravel().copy()] for p in pts]
                    prev_gray = gray.copy()
                    # No continuar procesando este frame
                    vis = frame.copy()
                    cv2.putText(vis, f"GESTO: {current_gesture}", (10, 70),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                    cv2.putText(vis, f"FPS: {fps:.1f}", (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
                    if show:
                        cv2.imshow("Gesture Detection", resize_for_display(vis))
                        cv2.waitKey(1)
                    continue

        # Dibujar trayectorias
        vis = frame.copy()
        for traj in trajectories:
            if len(traj) >= 2:
                pts_draw = np.array(traj, dtype=np.int32)
                cv2.polylines(vis, [pts_draw], False, (0, 255, 0), 2)
                cv2.circle(vis, tuple(pts_draw[-1]), 4, (0, 0, 255), -1)

        if current_gesture and gesture_cooldown > 0:
            cv2.putText(vis, f"GESTO: {current_gesture}", (10, 70),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)

        cv2.putText(vis, f"Gestos | Pts: {len(trajectories)} | FPS: {fps:.1f}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        pts = good_new.reshape(-1, 1, 2)

        # Re-detectar si pocos puntos
        if len(pts) < 30:
            pts_new = cv2.goodFeaturesToTrack(gray, mask=None, **FEATURE_PARAMS)
            if pts_new is not None:
                pts = pts_new
                trajectories = [[p.ravel().copy()] for p in pts]

        prev_gray = gray.copy()

        if not snapshot_saved and frame_idx > max_frames // 4:
            ensure_image_write(output_dir / "gesture_snapshot.jpg", resize_for_display(vis))
            snapshot_saved = True

        if show:
            cv2.imshow("Gesture Detection", resize_for_display(vis))
            if cv2.waitKey(1) & 0xFF == 27:
                break

    elapsed = (time.perf_counter() - t_start) * 1000
    cap.release()
    if show:
        cv2.destroyWindow("Gesture Detection")

    if frame_idx > 0:
        ensure_image_write(output_dir / "gesture_final.jpg", resize_for_display(vis))

    gesture_summary = {}
    for g in detected_gestures:
        gesture_summary[g] = gesture_summary.get(g, 0) + 1

    return StageMetrics(
        stage="bonus_gesture_detection", processing_ms=elapsed,
        fps=frame_idx / (elapsed / 1000) if elapsed > 0 else 0,
        extra={
            "frames_processed": frame_idx,
            "total_gestures": len(detected_gestures),
            "gesture_counts": gesture_summary,
        },
    )
