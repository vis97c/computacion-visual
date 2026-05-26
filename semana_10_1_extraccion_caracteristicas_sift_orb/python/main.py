"""
Taller Extracción de Características con SIFT y ORB
=====================================================

1. Detección de esquinas con Harris Corner Detector
2. Implementación de SIFT (keypoints + descriptores)
3. Implementación de ORB (keypoints + descriptores)
4. Comparación cuantitativa de rendimiento
5. Robustez ante rotación, escala e iluminación
6. Bonus: AKAZE y BRISK como alternativas
7. Visualización avanzada y tabla comparativa
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
import os

MEDIA = os.path.join(os.path.dirname(__file__), '..', 'media')
os.makedirs(MEDIA, exist_ok=True)
IMG_PATH = os.path.join(os.path.dirname(__file__), 'input_image.jpg')


def save(fig, name):
    fig.savefig(os.path.join(MEDIA, name), dpi=140, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  ✓ {name}")


def load():
    img = cv2.imread(IMG_PATH)
    if img is None:
        raise FileNotFoundError(IMG_PATH)
    return img


def to_rgb(bgr):
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)


# ============================================================
# 1. HARRIS CORNER DETECTOR
# ============================================================

def harris_corners():
    """Detección de esquinas con Harris variando parámetros."""
    print("\n[1] Harris Corner Detector")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)

    configs = [
        {'blockSize': 2, 'ksize': 3, 'k': 0.04, 'label': 'block=2, k=0.04'},
        {'blockSize': 2, 'ksize': 3, 'k': 0.06, 'label': 'block=2, k=0.06'},
        {'blockSize': 4, 'ksize': 5, 'k': 0.04, 'label': 'block=4, ksize=5'},
        {'blockSize': 7, 'ksize': 7, 'k': 0.04, 'label': 'block=7, ksize=7'},
    ]

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Detección de Esquinas — Harris Corner Detector', fontsize=14, fontweight='bold')

    for ax, cfg in zip(axes.flat, configs):
        dst = cv2.cornerHarris(gray, cfg['blockSize'], cfg['ksize'], cfg['k'])
        dst = cv2.dilate(dst, None)
        vis = to_rgb(bgr.copy())
        threshold = 0.01 * dst.max()
        vis[dst > threshold] = [255, 0, 0]
        n_corners = np.sum(dst > threshold)

        ax.imshow(vis)
        ax.set_title(f"{cfg['label']}\n{n_corners:,} esquinas", fontsize=10)
        ax.axis('off')

    plt.tight_layout()
    save(fig, 'python_harris_corners.png')


# ============================================================
# 2. SIFT
# ============================================================

def sift_detection():
    """Detección de keypoints y descriptores con SIFT."""
    print("\n[2] SIFT — Detección y visualización")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    kp, des = sift.detectAndCompute(gray, None)

    # Keypoints simples
    vis_simple = cv2.drawKeypoints(to_rgb(bgr), kp, None,
                                    color=(0, 255, 0), flags=0)

    # Keypoints ricos (escala + orientación)
    vis_rich = cv2.drawKeypoints(to_rgb(bgr), kp, None,
                                  color=(0, 255, 0),
                                  flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(f'SIFT — {len(kp):,} Keypoints Detectados', fontsize=14, fontweight='bold')

    axes[0].imshow(vis_simple)
    axes[0].set_title('Keypoints (posición)', fontsize=11)
    axes[0].axis('off')

    axes[1].imshow(vis_rich)
    axes[1].set_title('Rich Keypoints (posición + escala + orientación)', fontsize=11)
    axes[1].axis('off')

    plt.tight_layout()
    save(fig, 'python_sift_keypoints.png')

    # --- Análisis de propiedades ---
    sizes = [k.size for k in kp]
    angles = [k.angle for k in kp]
    responses = [k.response for k in kp]
    octaves = [k.octave & 0xFF for k in kp]

    fig2, axes2 = plt.subplots(2, 2, figsize=(14, 9))
    fig2.suptitle('SIFT — Análisis de Propiedades de Keypoints', fontsize=14, fontweight='bold')

    axes2[0, 0].hist(sizes, bins=50, color='#3b82f6', alpha=0.8, edgecolor='#2563eb')
    axes2[0, 0].set_title('Distribución de Escala (size)')
    axes2[0, 0].set_xlabel('Escala (px)')
    axes2[0, 0].set_ylabel('Frecuencia')
    axes2[0, 0].grid(True, alpha=0.3)

    axes2[0, 1].hist(angles, bins=72, color='#f97316', alpha=0.8, edgecolor='#ea580c')
    axes2[0, 1].set_title('Distribución de Orientación')
    axes2[0, 1].set_xlabel('Ángulo (°)')
    axes2[0, 1].grid(True, alpha=0.3)

    axes2[1, 0].hist(responses, bins=50, color='#22c55e', alpha=0.8, edgecolor='#16a34a')
    axes2[1, 0].set_title('Distribución de Respuesta (strength)')
    axes2[1, 0].set_xlabel('Respuesta')
    axes2[1, 0].grid(True, alpha=0.3)

    axes2[1, 1].hist(octaves, bins=range(max(octaves) + 2), color='#8b5cf6',
                      alpha=0.8, edgecolor='#7c3aed', align='left')
    axes2[1, 1].set_title('Distribución por Octava')
    axes2[1, 1].set_xlabel('Octava')
    axes2[1, 1].grid(True, alpha=0.3)

    plt.tight_layout()
    save(fig2, 'python_sift_propiedades.png')

    return len(kp), des.shape if des is not None else (0, 0)


# ============================================================
# 3. ORB
# ============================================================

def orb_detection():
    """Detección de keypoints y descriptores con ORB."""
    print("\n[3] ORB — Detección y visualización")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    orb = cv2.ORB_create(nfeatures=2000)
    kp, des = orb.detectAndCompute(gray, None)

    vis_simple = cv2.drawKeypoints(to_rgb(bgr), kp, None, color=(255, 50, 50), flags=0)
    vis_rich = cv2.drawKeypoints(to_rgb(bgr), kp, None, color=(255, 50, 50),
                                  flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle(f'ORB — {len(kp):,} Keypoints Detectados (nfeatures=2000)',
                 fontsize=14, fontweight='bold')

    axes[0].imshow(vis_simple)
    axes[0].set_title('Keypoints (posición)', fontsize=11)
    axes[0].axis('off')

    axes[1].imshow(vis_rich)
    axes[1].set_title('Rich Keypoints (posición + escala + orientación)', fontsize=11)
    axes[1].axis('off')

    plt.tight_layout()
    save(fig, 'python_orb_keypoints.png')

    return len(kp), des.shape if des is not None else (0, 0)


# ============================================================
# 4. COMPARACIÓN SIFT vs ORB
# ============================================================

def side_by_side_comparison():
    """Comparación visual directa SIFT vs ORB."""
    print("\n[4] Comparación lado a lado SIFT vs ORB")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    sift = cv2.SIFT_create()
    kp_s, des_s = sift.detectAndCompute(gray, None)

    orb = cv2.ORB_create(nfeatures=2000)
    kp_o, des_o = orb.detectAndCompute(gray, None)

    vis_s = cv2.drawKeypoints(to_rgb(bgr), kp_s, None, color=(0, 255, 0),
                               flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
    vis_o = cv2.drawKeypoints(to_rgb(bgr), kp_o, None, color=(255, 50, 50),
                               flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))
    fig.suptitle('Comparación Visual: SIFT vs ORB', fontsize=14, fontweight='bold')

    axes[0].imshow(vis_s)
    axes[0].set_title(f'SIFT — {len(kp_s):,} keypoints\nDescriptor: 128-D float32',
                       fontsize=11, color='green')
    axes[0].axis('off')

    axes[1].imshow(vis_o)
    axes[1].set_title(f'ORB — {len(kp_o):,} keypoints\nDescriptor: 32-D uint8 (binario)',
                       fontsize=11, color='red')
    axes[1].axis('off')

    plt.tight_layout()
    save(fig, 'python_sift_vs_orb.png')


# ============================================================
# 5. RENDIMIENTO (TIEMPO)
# ============================================================

def performance_benchmark():
    """Mide tiempo de ejecución de cada algoritmo."""
    print("\n[5] Benchmark de rendimiento")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    algorithms = {
        'SIFT': cv2.SIFT_create(),
        'ORB (500)': cv2.ORB_create(nfeatures=500),
        'ORB (2000)': cv2.ORB_create(nfeatures=2000),
        'AKAZE': cv2.AKAZE_create(),
        'BRISK': cv2.BRISK_create(),
    }

    results = {}
    n_runs = 10

    for name, detector in algorithms.items():
        times = []
        kp_count = 0
        des_size = 0
        for _ in range(n_runs):
            t0 = time.perf_counter()
            kp, des = detector.detectAndCompute(gray, None)
            t1 = time.perf_counter()
            times.append((t1 - t0) * 1000)
            kp_count = len(kp)
            if des is not None:
                des_size = des.shape[1]

        avg_time = np.mean(times)
        results[name] = {
            'time_ms': avg_time,
            'keypoints': kp_count,
            'desc_dim': des_size,
            'desc_type': 'float32' if des is not None and des.dtype == np.float32 else 'uint8',
        }

    # --- Gráfico de barras ---
    fig, axes = plt.subplots(1, 3, figsize=(18, 5.5))
    fig.suptitle('Benchmark de Rendimiento — Comparación de Algoritmos', fontsize=14, fontweight='bold')

    names = list(results.keys())
    colors = ['#3b82f6', '#f97316', '#ef4444', '#22c55e', '#8b5cf6']

    # Tiempo
    times_ms = [results[n]['time_ms'] for n in names]
    bars = axes[0].bar(names, times_ms, color=colors, alpha=0.85, edgecolor='white')
    axes[0].set_title('Tiempo de Ejecución (ms)', fontsize=11)
    axes[0].set_ylabel('Milisegundos')
    for bar, val in zip(bars, times_ms):
        axes[0].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                     f'{val:.1f}', ha='center', fontsize=9)
    axes[0].grid(True, alpha=0.2, axis='y')
    axes[0].tick_params(axis='x', rotation=20)

    # Keypoints
    kps = [results[n]['keypoints'] for n in names]
    bars2 = axes[1].bar(names, kps, color=colors, alpha=0.85, edgecolor='white')
    axes[1].set_title('Keypoints Detectados', fontsize=11)
    axes[1].set_ylabel('Cantidad')
    for bar, val in zip(bars2, kps):
        axes[1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                     f'{val:,}', ha='center', fontsize=9)
    axes[1].grid(True, alpha=0.2, axis='y')
    axes[1].tick_params(axis='x', rotation=20)

    # Dimensión del descriptor
    dims = [results[n]['desc_dim'] for n in names]
    bars3 = axes[2].bar(names, dims, color=colors, alpha=0.85, edgecolor='white')
    axes[2].set_title('Dimensión del Descriptor', fontsize=11)
    axes[2].set_ylabel('Dimensiones')
    for bar, val in zip(bars3, dims):
        axes[2].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                     str(val), ha='center', fontsize=9)
    axes[2].grid(True, alpha=0.2, axis='y')
    axes[2].tick_params(axis='x', rotation=20)

    plt.tight_layout()
    save(fig, 'python_benchmark_rendimiento.png')

    return results


# ============================================================
# 6. ROBUSTEZ (ROTACIÓN, ESCALA, ILUMINACIÓN)
# ============================================================

def robustness_test():
    """Evalúa robustez ante rotación, escala y cambios de iluminación."""
    print("\n[6] Robustez ante transformaciones")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    # Generar variantes
    def rotate_img(img, angle):
        M = cv2.getRotationMatrix2D((w//2, h//2), angle, 1.0)
        return cv2.warpAffine(img, M, (w, h))

    def scale_img(img, factor):
        new_w, new_h = int(w*factor), int(h*factor)
        scaled = cv2.resize(img, (new_w, new_h))
        canvas = np.zeros_like(img)
        oy, ox = (h-new_h)//2, (w-new_w)//2
        if factor <= 1:
            canvas[oy:oy+new_h, ox:ox+new_w] = scaled
        else:
            canvas = scaled[(-oy if oy<0 else 0):(-oy if oy<0 else 0)+h,
                            (-ox if ox<0 else 0):(-ox if ox<0 else 0)+w]
        return canvas

    def adjust_brightness(img, delta):
        return np.clip(img.astype(int) + delta, 0, 255).astype(np.uint8)

    transforms = {
        'Original':      gray,
        'Rotación 15°':  rotate_img(gray, 15),
        'Rotación 45°':  rotate_img(gray, 45),
        'Escala 0.5×':   scale_img(gray, 0.5),
        'Escala 1.5×':   scale_img(gray, 1.5),
        'Brillo -60':    adjust_brightness(gray, -60),
        'Brillo +60':    adjust_brightness(gray, +60),
        'Blur 11×11':    cv2.GaussianBlur(gray, (11, 11), 3),
    }

    sift = cv2.SIFT_create()
    orb = cv2.ORB_create(nfeatures=2000)

    sift_counts = []
    orb_counts = []
    labels = []

    fig, axes = plt.subplots(2, 4, figsize=(20, 9))
    fig.suptitle('Robustez: Keypoints Detectados ante Transformaciones', fontsize=14, fontweight='bold')

    for ax, (name, img) in zip(axes.flat, transforms.items()):
        kp_s, _ = sift.detectAndCompute(img, None)
        kp_o, _ = orb.detectAndCompute(img, None)

        vis = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        vis_s = cv2.drawKeypoints(vis.copy(), kp_s[:200], None, color=(0, 255, 0), flags=0)
        vis_o = cv2.drawKeypoints(vis_s, kp_o[:200], None, color=(255, 50, 50), flags=0)

        ax.imshow(vis_o)
        ax.set_title(f'{name}\nSIFT:{len(kp_s)} | ORB:{len(kp_o)}', fontsize=9)
        ax.axis('off')

        sift_counts.append(len(kp_s))
        orb_counts.append(len(kp_o))
        labels.append(name.replace(' ', '\n'))

    plt.tight_layout()
    save(fig, 'python_robustez_transformaciones.png')

    # --- Gráfico comparativo ---
    fig2, ax = plt.subplots(figsize=(14, 5.5))
    x = np.arange(len(labels))
    width = 0.35

    bars1 = ax.bar(x - width/2, sift_counts, width, label='SIFT', color='#3b82f6', alpha=0.85)
    bars2 = ax.bar(x + width/2, orb_counts, width, label='ORB', color='#ef4444', alpha=0.85)

    ax.set_title('Keypoints Detectados por Transformación — SIFT vs ORB', fontsize=13, fontweight='bold')
    ax.set_ylabel('Keypoints')
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8)
    ax.legend()
    ax.grid(True, alpha=0.2, axis='y')

    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'{int(bar.get_height())}', ha='center', fontsize=7)
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 15,
                f'{int(bar.get_height())}', ha='center', fontsize=7)

    plt.tight_layout()
    save(fig2, 'python_robustez_grafico.png')


# ============================================================
# 7. BONUS: AKAZE y BRISK
# ============================================================

def alternative_detectors():
    """Comparación con AKAZE y BRISK."""
    print("\n[7] Algoritmos alternativos: AKAZE y BRISK")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    detectors = {
        'SIFT':  (cv2.SIFT_create(), (0, 255, 0)),
        'ORB':   (cv2.ORB_create(nfeatures=2000), (255, 50, 50)),
        'AKAZE': (cv2.AKAZE_create(), (50, 150, 255)),
        'BRISK': (cv2.BRISK_create(), (255, 200, 50)),
    }

    fig, axes = plt.subplots(2, 2, figsize=(18, 12))
    fig.suptitle('Comparación de 4 Detectores de Características', fontsize=14, fontweight='bold')

    for ax, (name, (det, color)) in zip(axes.flat, detectors.items()):
        kp, des = det.detectAndCompute(gray, None)
        vis = cv2.drawKeypoints(to_rgb(bgr), kp, None, color=color,
                                 flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
        desc_info = f'{des.shape[1]}-D {des.dtype}' if des is not None else 'N/A'
        ax.imshow(vis)
        ax.set_title(f'{name} — {len(kp):,} keypoints\nDescriptor: {desc_info}', fontsize=11)
        ax.axis('off')

    plt.tight_layout()
    save(fig, 'python_comparacion_4_algoritmos.png')


# ============================================================
# 8. TABLA COMPARATIVA
# ============================================================

def summary_table(results):
    """Genera tabla comparativa como imagen."""
    print("\n[8] Tabla comparativa")

    fig, ax = plt.subplots(figsize=(12, 4))
    ax.axis('off')
    ax.set_title('Tabla Comparativa de Algoritmos de Detección de Características',
                 fontsize=13, fontweight='bold', pad=20)

    headers = ['Algoritmo', 'Tiempo (ms)', 'Keypoints', 'Descriptor', 'Tipo', 'Patentado']
    cell_data = []
    for name, r in results.items():
        cell_data.append([
            name,
            f"{r['time_ms']:.1f}",
            f"{r['keypoints']:,}",
            f"{r['desc_dim']}-D",
            r['desc_type'],
            'Sí (exp.)' if 'SIFT' in name else 'No',
        ])

    table = ax.table(cellText=cell_data, colLabels=headers, loc='center',
                     cellLoc='center', colColours=['#e2e8f0'] * len(headers))
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.6)

    # Estilizar
    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_facecolor('#475569')
            cell.set_text_props(color='white', fontweight='bold')
        elif row % 2 == 0:
            cell.set_facecolor('#f8fafc')
        cell.set_edgecolor('#cbd5e1')

    plt.tight_layout()
    save(fig, 'python_tabla_comparativa.png')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Taller: Extracción de Características SIFT y ORB")
    print("=" * 60)

    harris_corners()
    sift_info = sift_detection()
    orb_info = orb_detection()
    side_by_side_comparison()
    results = performance_benchmark()
    robustness_test()
    alternative_detectors()
    summary_table(results)

    print("\n" + "=" * 60)
    n = len([f for f in os.listdir(MEDIA) if f.startswith('python_')])
    print(f"✅ {n} visualizaciones generadas en media/")
    print("=" * 60)
