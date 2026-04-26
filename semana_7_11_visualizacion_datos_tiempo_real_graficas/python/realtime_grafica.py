from __future__ import annotations

import argparse
import csv
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


@dataclass
class Muestra:
    timestamp_iso: str
    elapsed_s: float
    temperatura_c: float


def simular_temperatura(elapsed_s: float) -> float:
    base = 24.0
    amplitud = 3.0
    ruido = random.uniform(-0.35, 0.35)
    onda = amplitud * math.sin((2.0 * math.pi * elapsed_s) / 10.0)
    return base + onda + ruido


def exportar_resultados(muestras: list[Muestra], media_dir: Path) -> tuple[Path, Path]:
    media_dir.mkdir(parents=True, exist_ok=True)
    csv_path = media_dir / "temperatura_tiempo_real.csv"
    png_path = media_dir / "grafica_final_temperatura.png"

    with csv_path.open("w", newline="", encoding="utf-8") as archivo_csv:
        writer = csv.writer(archivo_csv)
        writer.writerow(["timestamp_iso", "elapsed_s", "temperatura_c"])
        for fila in muestras:
            writer.writerow([fila.timestamp_iso, f"{fila.elapsed_s:.4f}", f"{fila.temperatura_c:.4f}"])

    x = np.array([m.elapsed_s for m in muestras], dtype=float)
    y = np.array([m.temperatura_c for m in muestras], dtype=float)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(x, y, color="#1f77b4", linewidth=2)
    ax.set_title("Temperatura simulada en tiempo real")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Temperatura (°C)")
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(png_path, dpi=160)
    plt.close(fig)

    return csv_path, png_path


def ejecutar_headless(duration_s: float, interval_ms: int, media_dir: Path) -> None:
    inicio = time.perf_counter()
    muestras: list[Muestra] = []

    while True:
        elapsed = time.perf_counter() - inicio
        if elapsed > duration_s:
            break
        muestras.append(
            Muestra(
                timestamp_iso=datetime.now().isoformat(timespec="milliseconds"),
                elapsed_s=elapsed,
                temperatura_c=simular_temperatura(elapsed),
            )
        )
        time.sleep(interval_ms / 1000.0)

    if not muestras:
        raise RuntimeError("No se generaron muestras.")

    csv_path, png_path = exportar_resultados(muestras, media_dir)
    y = np.array([m.temperatura_c for m in muestras], dtype=float)
    fps = len(muestras) / max(duration_s, 1e-6)
    print(f"Muestras: {len(muestras)}")
    print(f"FPS promedio (aprox): {fps:.2f}")
    print(f"Temperatura promedio: {y.mean():.2f} °C")
    print(f"CSV exportado: {csv_path}")
    print(f"PNG exportado: {png_path}")


def ejecutar_interactivo(duration_s: float | None, interval_ms: int, media_dir: Path) -> None:
    inicio = time.perf_counter()
    muestras: list[Muestra] = []
    fps_historial: list[float] = []
    ultimo_frame: float | None = None

    fig, ax = plt.subplots(figsize=(10, 4))
    (linea,) = ax.plot([], [], color="#1f77b4", linewidth=2)
    texto_estado = ax.text(0.01, 0.96, "", transform=ax.transAxes, va="top")
    ax.set_title("Temperatura simulada en tiempo real")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Temperatura (°C)")
    ax.set_xlim(0, 20)
    ax.set_ylim(19, 29)
    ax.grid(True, alpha=0.25)

    def actualizar(_frame: int):
        nonlocal ultimo_frame
        ahora = time.perf_counter()
        elapsed = ahora - inicio
        temperatura = simular_temperatura(elapsed)

        muestras.append(
            Muestra(
                timestamp_iso=datetime.now().isoformat(timespec="milliseconds"),
                elapsed_s=elapsed,
                temperatura_c=temperatura,
            )
        )

        x = np.array([m.elapsed_s for m in muestras], dtype=float)
        y = np.array([m.temperatura_c for m in muestras], dtype=float)
        linea.set_data(x, y)

        if elapsed > 18:
            ax.set_xlim(max(0.0, elapsed - 18.0), elapsed + 2.0)
        ax.set_ylim(float(y.min()) - 0.8, float(y.max()) + 0.8)

        if ultimo_frame is not None:
            dt = ahora - ultimo_frame
            if dt > 0:
                fps_historial.append(1.0 / dt)
                if len(fps_historial) > 120:
                    fps_historial.pop(0)
        ultimo_frame = ahora

        fps_actual = float(np.mean(fps_historial)) if fps_historial else 0.0
        promedio_temp = float(np.mean(y))
        texto_estado.set_text(
            f"Temp actual: {temperatura:.2f} °C\n"
            f"Promedio: {promedio_temp:.2f} °C\n"
            f"FPS aprox: {fps_actual:.2f}"
        )

        if duration_s is not None and elapsed >= duration_s:
            plt.close(fig)

        return (linea, texto_estado)

    _anim = FuncAnimation(fig, actualizar, interval=interval_ms, blit=False, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

    if not muestras:
        raise RuntimeError("No se registraron muestras en la sesión interactiva.")

    elapsed_total = muestras[-1].elapsed_s
    csv_path, png_path = exportar_resultados(muestras, media_dir)
    y = np.array([m.temperatura_c for m in muestras], dtype=float)
    fps = len(muestras) / max(elapsed_total, 1e-6)
    print(f"Muestras: {len(muestras)}")
    print(f"FPS promedio (aprox): {fps:.2f}")
    print(f"Temperatura promedio: {y.mean():.2f} °C")
    print(f"CSV exportado: {csv_path}")
    print(f"PNG exportado: {png_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualizacion de datos en tiempo real con Matplotlib (temperatura simulada)."
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=20.0,
        help="Duracion en segundos. Usa 0 para ejecucion manual hasta cerrar la ventana.",
    )
    parser.add_argument(
        "--interval-ms",
        type=int,
        default=120,
        help="Intervalo entre actualizaciones del grafico en milisegundos.",
    )
    parser.add_argument(
        "--media-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "media",
        help="Directorio de salida para CSV y PNG.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecuta sin abrir ventana y exporta resultados automaticamente.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.interval_ms <= 0:
        raise ValueError("--interval-ms debe ser mayor que 0.")
    if args.duration < 0:
        raise ValueError("--duration no puede ser negativa.")

    duracion = None if args.duration == 0 else float(args.duration)
    if args.headless:
        if duracion is None:
            raise ValueError("En modo --headless debes especificar --duration mayor a 0.")
        ejecutar_headless(duracion, args.interval_ms, args.media_dir)
        return

    ejecutar_interactivo(duracion, args.interval_ms, args.media_dir)


if __name__ == "__main__":
    main()
