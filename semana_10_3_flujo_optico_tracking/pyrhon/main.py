"""Taller semana 10.3 – Flujo Óptico y Tracking.

Script principal que orquesta todos los módulos del taller:
  1. Flujo Óptico Disperso (Lucas-Kanade)
  2. Flujo Óptico Denso (Farnebäck)
  3. Tracking de Objetos
  4. Estimación de Movimiento de Cámara
  5. Detección de Movimiento
  6. Análisis de Rendimiento
  7. Bonus (estabilización, motion blur, gestos)

Uso:
  python main.py                          # Webcam, todos los módulos
  python main.py --source video.mp4       # Video, todos los módulos
  python main.py --modules 1 2 6          # Solo módulos específicos
  python main.py --no-show                # Sin ventanas (solo guardar)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from utils import save_metrics, StageMetrics

# ---------------------------------------------------------------------------
# Tabla de módulos disponibles
# ---------------------------------------------------------------------------

MODULE_MAP = {
    1: ("Flujo Óptico Disperso (Lucas-Kanade)", "sparse_flow",      "run_lucas_kanade"),
    2: ("Flujo Óptico Denso (Farnebäck)",       "dense_flow",       "run_dense_flow"),
    3: ("Tracking de Objetos",                   "object_tracking",  "run_object_tracking"),
    4: ("Estimación Movimiento Cámara",          "camera_motion",    "run_camera_motion"),
    5: ("Detección de Movimiento",               "motion_detection", "run_motion_detection"),
    6: ("Análisis de Rendimiento",               "performance",      "run_performance_analysis"),
    7: ("Bonus: Estabilización de video",        "bonus",            "run_stabilization"),
    8: ("Bonus: Motion Blur Artístico",          "bonus",            "run_motion_blur"),
    9: ("Bonus: Detección de Gestos",            "bonus",            "run_gesture_detection"),
}


def _import_runner(module_name: str, func_name: str):
    """Importa dinámicamente la función runner de un módulo."""
    mod = __import__(module_name)
    return getattr(mod, func_name)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Taller 10.3: Flujo Óptico y Tracking con OpenCV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--source", default="0",
        help="Fuente de video: ruta a archivo o número de cámara (default: 0 = webcam).",
    )
    parser.add_argument(
        "--modules", nargs="*", type=int, default=None,
        help="Módulos a ejecutar (1-9). Si no se indica, ejecuta todos.",
    )
    parser.add_argument(
        "--max-frames", type=int, default=600,
        help="Máximo de frames a procesar por módulo (default: 600).",
    )
    parser.add_argument(
        "--bench-frames", type=int, default=120,
        help="Frames para benchmark de rendimiento (default: 120).",
    )
    parser.add_argument(
        "--no-show", action="store_true",
        help="No mostrar ventanas de visualización (solo guardar resultados).",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=None,
        help="Carpeta de salida. Default: ../media",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Determinar fuente de video
    source: str | int
    try:
        source = int(args.source)
    except ValueError:
        source = args.source

    output_dir = args.output_dir or (Path(__file__).resolve().parents[1] / "media")
    output_dir.mkdir(parents=True, exist_ok=True)

    modules_to_run = args.modules if args.modules else list(MODULE_MAP.keys())
    show = not args.no_show

    all_metrics: list[StageMetrics] = []

    print("=" * 60)
    print("  TALLER 10.3 – FLUJO ÓPTICO Y TRACKING")
    print("=" * 60)
    print(f"  Fuente     : {source}")
    print(f"  Módulos    : {modules_to_run}")
    print(f"  Max frames : {args.max_frames}")
    print(f"  Salida     : {output_dir}")
    print(f"  Mostrar UI : {show}")
    print("=" * 60)

    for mod_id in modules_to_run:
        if mod_id not in MODULE_MAP:
            print(f"[WARN] Módulo {mod_id} no existe, saltando.")
            continue

        name, module_name, func_name = MODULE_MAP[mod_id]
        print(f"\n{'─' * 50}")
        print(f"  [{mod_id}] {name}")
        print(f"{'─' * 50}")

        try:
            runner = _import_runner(module_name, func_name)

            # El módulo 6 (rendimiento) tiene firma diferente
            if mod_id == 6:
                metrics = runner(source, output_dir, n_frames=args.bench_frames)
            else:
                metrics = runner(source, output_dir, max_frames=args.max_frames, show=show)

            all_metrics.append(metrics)
            print(f"  ✓ Completado en {metrics.processing_ms:.0f} ms")
            if metrics.fps > 0:
                print(f"    FPS promedio: {metrics.fps:.1f}")
            if metrics.extra:
                for k, v in metrics.extra.items():
                    if not isinstance(v, dict):
                        print(f"    {k}: {v}")

        except Exception as e:
            print(f"  ✗ Error: {e}")
            all_metrics.append(
                StageMetrics(stage=f"error_{module_name}", processing_ms=0, note=str(e))
            )

    # Guardar métricas globales
    save_metrics(all_metrics, output_dir / "python_metricas.json")

    print(f"\n{'=' * 60}")
    print(f"  RESULTADOS GUARDADOS EN: {output_dir}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
