"""Utilidades compartidas para el taller de flujo óptico y tracking."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Dataclasses para métricas
# ---------------------------------------------------------------------------

@dataclass
class StageMetrics:
    stage: str
    processing_ms: float
    fps: float = 0.0
    extra: Dict[str, Any] = field(default_factory=dict)
    note: str = ""


# ---------------------------------------------------------------------------
# Helpers de video / imagen
# ---------------------------------------------------------------------------

def open_video(source: str | int) -> cv2.VideoCapture:
    """Abre video desde archivo o cámara web (0, 1, …)."""
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"No se pudo abrir la fuente de video: {source}")
    return cap


def ensure_image_write(path: Path, image: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ok = cv2.imwrite(str(path), image)
    if not ok:
        raise RuntimeError(f"No se pudo guardar la imagen: {path}")


class _NumpyEncoder(json.JSONEncoder):
    """Encoder que convierte tipos numpy a tipos nativos de Python."""

    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.str_):
            return str(obj)
        return super().default(obj)


def save_metrics(metrics: List[StageMetrics], path: Path) -> None:
    payload = [asdict(m) for m in metrics]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, cls=_NumpyEncoder),
        encoding="utf-8",
    )
    print(f"[OK] Métricas guardadas en: {path}")


def resize_for_display(frame: np.ndarray, max_w: int = 960) -> np.ndarray:
    h, w = frame.shape[:2]
    if w <= max_w:
        return frame
    scale = max_w / w
    return cv2.resize(frame, (max_w, int(h * scale)))


class FPSCounter:
    """Contador de FPS con media móvil."""

    def __init__(self, window: int = 30):
        self._times: List[float] = []
        self._window = window

    def tick(self) -> float:
        now = time.perf_counter()
        self._times.append(now)
        if len(self._times) > self._window:
            self._times.pop(0)
        if len(self._times) < 2:
            return 0.0
        return (len(self._times) - 1) / (self._times[-1] - self._times[0])
