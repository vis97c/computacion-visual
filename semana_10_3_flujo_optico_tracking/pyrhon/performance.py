"""6. Análisis de Rendimiento.

Mide FPS, compara Lucas-Kanade vs Farnebäck, evalúa precisión del
tracking con diferentes parámetros y genera gráficas comparativas.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List

import cv2
import matplotlib
matplotlib.use("Agg")  # Backend no-interactivo para guardar imágenes
import matplotlib.pyplot as plt
import numpy as np

from utils import FPSCounter, StageMetrics, open_video

# ---------------------------------------------------------------------------
# Configuraciones de parámetros a comparar
# ---------------------------------------------------------------------------

LK_CONFIGS = [
    {"label": "LK win=11 lev=2", "winSize": (11, 11), "maxLevel": 2},
    {"label": "LK win=21 lev=3", "winSize": (21, 21), "maxLevel": 3},
    {"label": "LK win=31 lev=4", "winSize": (31, 31), "maxLevel": 4},
]

FB_CONFIGS = [
    {"label": "FB win=9 lev=2", "winsize": 9, "levels": 2},
    {"label": "FB win=15 lev=3", "winsize": 15, "levels": 3},
    {"label": "FB win=21 lev=5", "winsize": 21, "levels": 5},
]

FEATURE_PARAMS = dict(maxCorners=200, qualityLevel=0.01, minDistance=15, blockSize=7)


def _bench_lucas_kanade(
    source: str | int, config: dict, n_frames: int
) -> Dict[str, float]:
    cap = open_video(source)
    ret, frame = cap.read()
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
    if pts is None:
        pts = np.empty((0, 1, 2), dtype=np.float32)
    initial_count = max(len(pts), 1)

    criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, 0.01)
    lk_params = dict(winSize=config["winSize"], maxLevel=config["maxLevel"], criteria=criteria)

    times: List[float] = []
    tracked_ratios: List[float] = []
    processed = 0

    for _ in range(n_frames):
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if len(pts) == 0:
            pts = cv2.goodFeaturesToTrack(prev_gray, mask=None, **FEATURE_PARAMS)
            if pts is None:
                pts = np.empty((0, 1, 2), dtype=np.float32)
            initial_count = max(len(pts), 1)
            prev_gray = gray.copy()
            continue

        t0 = time.perf_counter()
        next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray, pts, None, **lk_params)
        dt = time.perf_counter() - t0
        times.append(dt)

        if next_pts is not None and status is not None:
            good = next_pts[status.ravel() == 1]
            tracked_ratios.append(len(good) / initial_count)
            pts = good.reshape(-1, 1, 2) if len(good) > 0 else np.empty((0, 1, 2), dtype=np.float32)
        else:
            tracked_ratios.append(0.0)
            pts = np.empty((0, 1, 2), dtype=np.float32)

        prev_gray = gray.copy()
        processed += 1

    cap.release()
    avg_time = np.mean(times) if times else 0
    return {
        "avg_ms": avg_time * 1000,
        "fps": 1.0 / avg_time if avg_time > 0 else 0,
        "avg_tracked_ratio": float(np.mean(tracked_ratios)) if tracked_ratios else 0,
        "frames": processed,
    }


def _bench_farneback(
    source: str | int, config: dict, n_frames: int
) -> Dict[str, float]:
    cap = open_video(source)
    ret, frame = cap.read()
    prev_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    fb_params = dict(
        pyr_scale=0.5, levels=config["levels"], winsize=config["winsize"],
        iterations=3, poly_n=5, poly_sigma=1.2, flags=0,
    )

    times: List[float] = []
    avg_mags: List[float] = []
    processed = 0

    for _ in range(n_frames):
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        t0 = time.perf_counter()
        flow = cv2.calcOpticalFlowFarneback(prev_gray, gray, None, **fb_params)
        dt = time.perf_counter() - t0
        times.append(dt)

        mag = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
        avg_mags.append(float(np.mean(mag)))

        prev_gray = gray.copy()
        processed += 1

    cap.release()
    avg_time = np.mean(times) if times else 0
    return {
        "avg_ms": avg_time * 1000,
        "fps": 1.0 / avg_time if avg_time > 0 else 0,
        "avg_flow_magnitude": float(np.mean(avg_mags)) if avg_mags else 0,
        "frames": processed,
    }


def run_performance_analysis(
    source: str | int,
    output_dir: Path,
    n_frames: int = 120,
) -> StageMetrics:
    """Ejecuta benchmarks comparativos y genera gráficas."""
    output_dir.mkdir(parents=True, exist_ok=True)
    t_start = time.perf_counter()

    results_lk = {}
    results_fb = {}

    print("[BENCH] Evaluando configuraciones de Lucas-Kanade …")
    for cfg in LK_CONFIGS:
        label = cfg["label"]
        print(f"  → {label}")
        results_lk[label] = _bench_lucas_kanade(source, cfg, n_frames)

    print("[BENCH] Evaluando configuraciones de Farnebäck …")
    for cfg in FB_CONFIGS:
        label = cfg["label"]
        print(f"  → {label}")
        results_fb[label] = _bench_farneback(source, cfg, n_frames)

    # ---- Gráfica comparativa de FPS ----
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Análisis de Rendimiento – Flujo Óptico", fontsize=14, fontweight="bold")

    # 1) FPS
    ax = axes[0]
    labels_all = list(results_lk.keys()) + list(results_fb.keys())
    fps_all = [results_lk[k]["fps"] for k in results_lk] + [results_fb[k]["fps"] for k in results_fb]
    colors = ["#4fc3f7"] * len(results_lk) + ["#ff8a65"] * len(results_fb)
    bars = ax.barh(labels_all, fps_all, color=colors)
    ax.set_xlabel("FPS")
    ax.set_title("Velocidad de procesamiento")
    for bar, val in zip(bars, fps_all):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}", va="center", fontsize=9)

    # 2) Tiempo promedio por frame
    ax = axes[1]
    ms_all = [results_lk[k]["avg_ms"] for k in results_lk] + [results_fb[k]["avg_ms"] for k in results_fb]
    bars = ax.barh(labels_all, ms_all, color=colors)
    ax.set_xlabel("ms / frame")
    ax.set_title("Tiempo promedio por frame")
    for bar, val in zip(bars, ms_all):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{val:.2f}", va="center", fontsize=9)

    # 3) Precisión / magnitud
    ax = axes[2]
    precision_lk = [results_lk[k]["avg_tracked_ratio"] * 100 for k in results_lk]
    mag_fb = [results_fb[k]["avg_flow_magnitude"] for k in results_fb]
    # Dos ejes: ratio para LK, magnitud para FB
    x = np.arange(len(results_lk))
    ax.bar(x - 0.2, precision_lk, 0.35, label="LK tracked %", color="#4fc3f7")
    ax2 = ax.twinx()
    x2 = np.arange(len(results_fb))
    ax2.bar(x2 + 0.2, mag_fb, 0.35, label="FB avg mag", color="#ff8a65")
    ax.set_ylabel("Tracked ratio (%)")
    ax2.set_ylabel("Avg flow magnitude (px)")
    ax.set_title("Precisión / Magnitud")
    ax.set_xticks(range(max(len(results_lk), len(results_fb))))
    ax.legend(loc="upper left", fontsize=8)
    ax2.legend(loc="upper right", fontsize=8)

    plt.tight_layout()
    chart_path = output_dir / "performance_comparison.png"
    fig.savefig(str(chart_path), dpi=150)
    plt.close(fig)
    print(f"[OK] Gráfica guardada: {chart_path}")

    elapsed = (time.perf_counter() - t_start) * 1000

    return StageMetrics(
        stage="performance_analysis",
        processing_ms=elapsed,
        extra={
            "lucas_kanade": results_lk,
            "farneback": results_fb,
        },
    )
