"""
Taller - Conversión y Manipulación de Espacios de Color
========================================================

Módulo principal que implementa:
1. Conversión entre espacios de color (RGB, HSV, HSL, LAB, YCrCb)
2. Visualización 3D de espacios de color
3. Segmentación por color en HSV
4. Manipulación de color (saturación, matiz, luminosidad)
5. Color grading y efectos cinematográficos
6. Extracción de paletas con K-means
7. Análisis y ecualización de histogramas
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import gridspec
from mpl_toolkits.mplot3d import Axes3D
from sklearn.cluster import KMeans
from skimage import color as skcolor
import os

# ============================================================
# Configuración
# ============================================================

MEDIA_DIR = os.path.join(os.path.dirname(__file__), '..', 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)

# Generar imagen de prueba si no existe
TEST_IMG_PATH = os.path.join(os.path.dirname(__file__), 'test_image.png')
if not os.path.exists(TEST_IMG_PATH):
    from generate_test_image import generate_test_image
    cv2.imwrite(TEST_IMG_PATH, generate_test_image())


def load_image():
    """Carga la imagen de prueba en BGR (formato OpenCV)."""
    img = cv2.imread(TEST_IMG_PATH)
    if img is None:
        raise FileNotFoundError(f"No se encontró: {TEST_IMG_PATH}")
    return img


def save(fig, name):
    """Guarda figura en media/ y cierra."""
    path = os.path.join(MEDIA_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  ✓ {name}")
    return path


# ============================================================
# 1. CONVERSIÓN ENTRE ESPACIOS DE COLOR
# ============================================================

def conversion_espacios_color():
    """
    Convierte una imagen RGB a múltiples espacios de color
    y visualiza cada canal por separado.
    """
    print("\n[1] Conversión entre espacios de color")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    conversions = {
        'HSV':    cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV),
        'HLS':    cv2.cvtColor(bgr, cv2.COLOR_BGR2HLS),
        'LAB':    cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB),
        'YCrCb':  cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb),
        'Gray':   cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY),
    }

    # Rangos de valores por espacio
    ranges = {
        'HSV':   ['H: 0-179', 'S: 0-255', 'V: 0-255'],
        'HLS':   ['H: 0-179', 'L: 0-255', 'S: 0-255'],
        'LAB':   ['L: 0-255', 'A: 0-255', 'B: 0-255'],
        'YCrCb': ['Y: 0-255', 'Cr: 0-255', 'Cb: 0-255'],
    }

    # --- Figura 1: Canales RGB ---
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8))
    fig.suptitle('Descomposición de Canales RGB', fontsize=13, fontweight='bold')

    axes[0].imshow(rgb)
    axes[0].set_title('Original (RGB)', fontsize=10)

    channel_names = ['Red', 'Green', 'Blue']
    cmaps = ['Reds', 'Greens', 'Blues']
    for i in range(3):
        axes[i + 1].imshow(rgb[..., i], cmap=cmaps[i])
        axes[i + 1].set_title(f'Canal {channel_names[i]}', fontsize=10)

    for ax in axes:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_canales_rgb.png')

    # --- Figura 2: Canales HSV ---
    hsv = conversions['HSV']
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8))
    fig.suptitle('Espacio HSV — Canales H, S, V', fontsize=13, fontweight='bold')

    axes[0].imshow(rgb)
    axes[0].set_title('Original (RGB)', fontsize=10)

    hsv_names = ['Hue (0-179)', 'Saturation (0-255)', 'Value (0-255)']
    hsv_cmaps = ['hsv', 'gray', 'gray']
    for i in range(3):
        axes[i + 1].imshow(hsv[..., i], cmap=hsv_cmaps[i])
        axes[i + 1].set_title(hsv_names[i], fontsize=10)

    for ax in axes:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_canales_hsv.png')

    # --- Figura 3: Canales LAB ---
    lab = conversions['LAB']
    fig, axes = plt.subplots(1, 4, figsize=(16, 3.8))
    fig.suptitle('Espacio CIELAB — Canales L*, a*, b*', fontsize=13, fontweight='bold')

    axes[0].imshow(rgb)
    axes[0].set_title('Original (RGB)', fontsize=10)

    lab_names = ['L* (Luminosidad)', 'a* (Verde↔Rojo)', 'b* (Azul↔Amarillo)']
    for i in range(3):
        axes[i + 1].imshow(lab[..., i], cmap='gray' if i == 0 else 'RdYlGn_r' if i == 1 else 'RdYlBu_r')
        axes[i + 1].set_title(lab_names[i], fontsize=10)

    for ax in axes:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_canales_lab.png')

    # --- Figura 4: Comparación de todos los espacios ---
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    fig.suptitle('Comparación de Espacios de Color', fontsize=14, fontweight='bold')

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title('RGB (Original)', fontsize=11)

    axes[0, 1].imshow(conversions['HSV'][..., 0], cmap='hsv')
    axes[0, 1].set_title('HSV — Hue', fontsize=11)

    axes[0, 2].imshow(conversions['HLS'][..., 1], cmap='gray')
    axes[0, 2].set_title('HLS — Lightness', fontsize=11)

    axes[1, 0].imshow(conversions['LAB'][..., 0], cmap='gray')
    axes[1, 0].set_title('LAB — L* (Luminosidad)', fontsize=11)

    axes[1, 1].imshow(conversions['YCrCb'][..., 0], cmap='gray')
    axes[1, 1].set_title('YCrCb — Y (Luma)', fontsize=11)

    axes[1, 2].imshow(conversions['Gray'], cmap='gray')
    axes[1, 2].set_title('Grayscale', fontsize=11)

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_comparacion_espacios.png')


# ============================================================
# 2. VISUALIZACIÓN 3D DE ESPACIOS DE COLOR
# ============================================================

def visualizacion_3d_espacios():
    """
    Crea visualizaciones 3D del espacio RGB y cilíndrica de HSV
    mostrando la distribución de los píxeles de la imagen.
    """
    print("\n[2] Visualización 3D de espacios de color")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Submuestreo para performance
    step = 8
    rgb_sub = rgb[::step, ::step].reshape(-1, 3)
    hsv_sub = hsv[::step, ::step].reshape(-1, 3)
    colors_norm = rgb_sub / 255.0

    # --- Figura: Espacio RGB 3D ---
    fig = plt.figure(figsize=(14, 6))
    fig.suptitle('Distribución de Píxeles en Espacios de Color', fontsize=14, fontweight='bold')

    ax1 = fig.add_subplot(121, projection='3d')
    ax1.scatter(rgb_sub[:, 0], rgb_sub[:, 1], rgb_sub[:, 2],
                c=colors_norm, s=2, alpha=0.6)
    ax1.set_xlabel('Red')
    ax1.set_ylabel('Green')
    ax1.set_zlabel('Blue')
    ax1.set_title('Espacio RGB', fontsize=11)
    ax1.set_xlim(0, 255)
    ax1.set_ylim(0, 255)
    ax1.set_zlim(0, 255)

    # --- Espacio HSV como cilindro ---
    ax2 = fig.add_subplot(122, projection='3d')
    h = hsv_sub[:, 0].astype(float) / 179.0 * 2 * np.pi  # hue → ángulo
    s = hsv_sub[:, 1].astype(float) / 255.0                # saturación → radio
    v = hsv_sub[:, 2].astype(float) / 255.0                # value → altura

    x_cyl = s * np.cos(h)
    y_cyl = s * np.sin(h)

    ax2.scatter(x_cyl, y_cyl, v, c=colors_norm, s=2, alpha=0.6)
    ax2.set_xlabel('S·cos(H)')
    ax2.set_ylabel('S·sin(H)')
    ax2.set_zlabel('Value')
    ax2.set_title('Espacio HSV (Cilíndrico)', fontsize=11)

    plt.tight_layout()
    save(fig, 'python_visualizacion_3d.png')


# ============================================================
# 3. SEGMENTACIÓN POR COLOR
# ============================================================

def segmentacion_por_color():
    """
    Segmenta colores específicos (rojo, amarillo, azul/violeta, verde)
    usando rangos en espacio HSV y aplica operaciones morfológicas.
    """
    print("\n[3] Segmentación por color en HSV")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)

    # Definir rangos HSV para cada color
    color_ranges = {
        'Rojo': {
            'lower1': np.array([0, 80, 80]),
            'upper1': np.array([10, 255, 255]),
            'lower2': np.array([170, 80, 80]),
            'upper2': np.array([179, 255, 255]),
        },
        'Amarillo': {
            'lower1': np.array([15, 80, 80]),
            'upper1': np.array([35, 255, 255]),
        },
        'Verde': {
            'lower1': np.array([35, 40, 40]),
            'upper1': np.array([85, 255, 255]),
        },
        'Azul/Violeta': {
            'lower1': np.array([85, 40, 40]),
            'upper1': np.array([145, 255, 255]),
        },
    }

    fig, axes = plt.subplots(2, 4, figsize=(18, 8.5))
    fig.suptitle('Segmentación por Color en Espacio HSV', fontsize=14, fontweight='bold')

    for col, (name, ranges) in enumerate(color_ranges.items()):
        # Crear máscara
        mask = cv2.inRange(hsv, ranges['lower1'], ranges['upper1'])
        if 'lower2' in ranges:
            mask2 = cv2.inRange(hsv, ranges['lower2'], ranges['upper2'])
            mask = cv2.bitwise_or(mask, mask2)

        # Limpieza morfológica
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask_clean = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask_clean = cv2.morphologyEx(mask_clean, cv2.MORPH_OPEN, kernel)

        # Aplicar máscara
        result = cv2.bitwise_and(rgb, rgb, mask=mask_clean)

        # Mostrar máscara y resultado
        axes[0, col].imshow(mask_clean, cmap='gray')
        axes[0, col].set_title(f'Máscara: {name}', fontsize=10)

        axes[1, col].imshow(result)
        axes[1, col].set_title(f'Segmentado: {name}', fontsize=10)

    for ax in axes.flat:
        ax.axis('off')

    axes[0, 0].set_ylabel('Máscara binaria', fontsize=10)
    axes[1, 0].set_ylabel('Color extraído', fontsize=10)

    plt.tight_layout()
    save(fig, 'python_segmentacion_color.png')


# ============================================================
# 4. MANIPULACIÓN DE COLOR
# ============================================================

def manipulacion_color():
    """
    Demuestra ajustes de saturación, rotación de matiz,
    modificación de luminosidad en LAB, y ecualización.
    """
    print("\n[4] Manipulación de color")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)

    # --- Saturación ---
    def adjust_saturation(hsv_img, factor):
        result = hsv_img.copy()
        result[..., 1] = np.clip(result[..., 1] * factor, 0, 255)
        bgr_out = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_HSV2BGR)
        return cv2.cvtColor(bgr_out, cv2.COLOR_BGR2RGB)

    # --- Rotación de matiz ---
    def rotate_hue(hsv_img, degrees):
        result = hsv_img.copy()
        result[..., 0] = (result[..., 0] + degrees / 2) % 180
        bgr_out = cv2.cvtColor(result.astype(np.uint8), cv2.COLOR_HSV2BGR)
        return cv2.cvtColor(bgr_out, cv2.COLOR_BGR2RGB)

    # --- Luminosidad en LAB ---
    def adjust_lab_luminosity(bgr_img, offset):
        lab = cv2.cvtColor(bgr_img, cv2.COLOR_BGR2LAB).astype(np.float32)
        lab[..., 0] = np.clip(lab[..., 0] + offset, 0, 255)
        bgr_out = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2BGR)
        return cv2.cvtColor(bgr_out, cv2.COLOR_BGR2RGB)

    fig, axes = plt.subplots(3, 4, figsize=(18, 12))
    fig.suptitle('Manipulación de Color: Saturación, Matiz y Luminosidad', fontsize=14, fontweight='bold')

    # Fila 1: Saturación
    sat_factors = [0.3, 0.7, 1.0, 2.0]
    for i, f in enumerate(sat_factors):
        axes[0, i].imshow(adjust_saturation(hsv, f))
        axes[0, i].set_title(f'Saturación ×{f}', fontsize=10)

    # Fila 2: Rotación de matiz
    hue_offsets = [0, 60, 120, 180]
    for i, deg in enumerate(hue_offsets):
        axes[1, i].imshow(rotate_hue(hsv, deg))
        axes[1, i].set_title(f'Hue +{deg}°', fontsize=10)

    # Fila 3: Luminosidad LAB
    lum_offsets = [-60, -30, 0, 50]
    for i, offset in enumerate(lum_offsets):
        axes[2, i].imshow(adjust_lab_luminosity(bgr, offset))
        label = f'L* {"" if offset >= 0 else ""}{offset:+d}'
        axes[2, i].set_title(label, fontsize=10)

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_manipulacion_color.png')


# ============================================================
# 5. COLOR GRADING
# ============================================================

def color_grading():
    """
    Aplica efectos cinematográficos: warm tones, cool tones,
    efecto vintage, alto contraste y estilo Instagram.
    """
    print("\n[5] Color grading y efectos cinematográficos")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    def apply_lut_curve(img, lut_r, lut_g, lut_b):
        """Aplica curvas de color independientes por canal."""
        result = img.copy()
        result[..., 0] = lut_r[result[..., 0]]
        result[..., 1] = lut_g[result[..., 1]]
        result[..., 2] = lut_b[result[..., 2]]
        return result

    # LUT identidad
    identity = np.arange(256, dtype=np.uint8)

    # Warm tones: boost rojo, reducir azul
    lut_warm_r = np.clip(np.arange(256) * 1.15, 0, 255).astype(np.uint8)
    lut_warm_g = np.clip(np.arange(256) * 1.05, 0, 255).astype(np.uint8)
    lut_warm_b = np.clip(np.arange(256) * 0.85, 0, 255).astype(np.uint8)
    warm = apply_lut_curve(rgb, lut_warm_r, lut_warm_g, lut_warm_b)

    # Cool tones: boost azul, reducir rojo
    lut_cool_r = np.clip(np.arange(256) * 0.85, 0, 255).astype(np.uint8)
    lut_cool_g = np.clip(np.arange(256) * 1.0, 0, 255).astype(np.uint8)
    lut_cool_b = np.clip(np.arange(256) * 1.2, 0, 255).astype(np.uint8)
    cool = apply_lut_curve(rgb, lut_cool_r, lut_cool_g, lut_cool_b)

    # Vintage: desaturar + tint sepia
    hsv_temp = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv_temp[..., 1] *= 0.5
    desat = cv2.cvtColor(hsv_temp.astype(np.uint8), cv2.COLOR_HSV2BGR)
    desat_rgb = cv2.cvtColor(desat, cv2.COLOR_BGR2RGB).astype(np.float32)
    sepia_tint = np.array([1.1, 0.95, 0.75])
    vintage = np.clip(desat_rgb * sepia_tint, 0, 255).astype(np.uint8)

    # Alto contraste: curva S
    x = np.arange(256)
    s_curve = (255 * (1 / (1 + np.exp(-0.03 * (x - 128))))).astype(np.uint8)
    contrast = apply_lut_curve(rgb, s_curve, s_curve, s_curve)

    # Estilo "Instagram" (alto contraste + warm + viñeta)
    insta = apply_lut_curve(rgb, lut_warm_r, lut_warm_g, lut_warm_b)
    insta = apply_lut_curve(insta, s_curve, s_curve, s_curve)
    # Viñeta
    rows, cols = insta.shape[:2]
    Y, X = np.ogrid[:rows, :cols]
    center = (cols / 2, rows / 2)
    dist = np.sqrt((X - center[0]) ** 2 + (Y - center[1]) ** 2)
    max_dist = np.sqrt(center[0] ** 2 + center[1] ** 2)
    vignette = 1 - 0.5 * (dist / max_dist) ** 2
    insta = (insta * vignette[..., np.newaxis]).astype(np.uint8)

    fig, axes = plt.subplots(2, 3, figsize=(16, 9.5))
    fig.suptitle('Color Grading — Efectos Cinematográficos', fontsize=14, fontweight='bold')

    results = [
        (rgb, 'Original'),
        (warm, 'Warm Tones'),
        (cool, 'Cool Tones'),
        (vintage, 'Vintage / Sepia'),
        (contrast, 'Alto Contraste (Curva S)'),
        (insta, 'Instagram (Warm + Contraste + Viñeta)'),
    ]

    for ax, (img, title) in zip(axes.flat, results):
        ax.imshow(img)
        ax.set_title(title, fontsize=11)
        ax.axis('off')

    plt.tight_layout()
    save(fig, 'python_color_grading.png')

    # --- Curvas de color usadas ---
    fig2, ax = plt.subplots(figsize=(8, 5))
    ax.set_title('Curvas de Color (LUTs) Aplicadas', fontsize=13, fontweight='bold')
    ax.plot(identity, identity, 'k--', alpha=0.3, label='Identidad')
    ax.plot(identity, lut_warm_r, 'r-', label='Warm - R (×1.15)')
    ax.plot(identity, lut_warm_b, 'b-', label='Warm - B (×0.85)')
    ax.plot(identity, lut_cool_r, 'r--', label='Cool - R (×0.85)')
    ax.plot(identity, lut_cool_b, 'b--', label='Cool - B (×1.2)')
    ax.plot(identity, s_curve, 'g-', linewidth=2, label='Curva S (Contraste)')
    ax.set_xlabel('Valor de entrada')
    ax.set_ylabel('Valor de salida')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 255)
    ax.set_ylim(0, 270)
    save(fig2, 'python_curvas_lut.png')


# ============================================================
# 6. PALETAS DE COLORES
# ============================================================

def paletas_colores():
    """
    Extrae colores dominantes con K-means, genera paleta
    y crea armonías cromáticas (complementarios, análogos, triádicos).
    """
    print("\n[6] Paletas de colores con K-means")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # Redimensionar para K-means
    small = cv2.resize(rgb, (100, 75))
    pixels = small.reshape(-1, 3).astype(np.float32)

    # K-means con 8 clusters
    n_colors = 8
    kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
    kmeans.fit(pixels)
    centers = kmeans.cluster_centers_.astype(np.uint8)
    labels = kmeans.labels_

    # Ordenar por frecuencia
    counts = np.bincount(labels)
    sorted_idx = np.argsort(-counts)
    centers = centers[sorted_idx]
    counts = counts[sorted_idx]

    # --- Figura: Paleta extraída ---
    fig = plt.figure(figsize=(16, 7))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1, 0.8], width_ratios=[1.2, 1])

    # Imagen original
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(rgb)
    ax1.set_title('Imagen Original', fontsize=11)
    ax1.axis('off')

    # Imagen cuantizada
    quantized = centers[kmeans.labels_[np.argsort(-counts)[np.searchsorted(np.argsort(-counts), kmeans.labels_)]] if False else kmeans.labels_]
    q_img = centers[np.argsort(-counts)][0]  # placeholder
    # Reconstruir imagen cuantizada
    label_remap = np.zeros(n_colors, dtype=int)
    for new_i, old_i in enumerate(sorted_idx):
        label_remap[old_i] = new_i
    remapped = label_remap[kmeans.labels_]
    q_pixels = centers[remapped]
    q_img = q_pixels.reshape(75, 100, 3)
    q_img_full = cv2.resize(q_img, (rgb.shape[1], rgb.shape[0]), interpolation=cv2.INTER_NEAREST)

    ax2 = fig.add_subplot(gs[0, 1])
    ax2.imshow(q_img_full)
    ax2.set_title(f'Cuantizada a {n_colors} colores', fontsize=11)
    ax2.axis('off')

    # Paleta de colores
    ax3 = fig.add_subplot(gs[1, :])
    palette = np.zeros((60, n_colors * 80, 3), dtype=np.uint8)
    for i, c in enumerate(centers):
        palette[:, i * 80:(i + 1) * 80] = c
    ax3.imshow(palette)
    ax3.set_title('Paleta de Colores Dominantes (K-means, k=8)', fontsize=11)
    ax3.axis('off')

    # Agregar texto con valores hex
    for i, c in enumerate(centers):
        hex_color = '#{:02x}{:02x}{:02x}'.format(c[0], c[1], c[2])
        pct = counts[i] / counts.sum() * 100
        ax3.text(i * 80 + 40, 30, f'{hex_color}\n{pct:.1f}%',
                ha='center', va='center', fontsize=8, fontweight='bold',
                color='white' if np.mean(c) < 128 else 'black')

    fig.suptitle('Extracción de Paleta con K-means', fontsize=14, fontweight='bold')
    plt.tight_layout()
    save(fig, 'python_paleta_colores.png')

    # --- Armonías cromáticas ---
    dominant = centers[0]
    dominant_hsv = cv2.cvtColor(np.uint8([[dominant]]), cv2.COLOR_RGB2HSV)[0, 0]
    h, s, v = dominant_hsv

    def hsv_to_rgb_single(h, s, v):
        c = cv2.cvtColor(np.uint8([[[h, s, v]]]), cv2.COLOR_HSV2RGB)[0, 0]
        return c

    harmonies = {
        'Complementario': [h, (h + 90) % 180],
        'Análogos': [(h - 15) % 180, h, (h + 15) % 180],
        'Triádico': [h, (h + 60) % 180, (h + 120) % 180],
        'Split-Complementario': [h, (h + 75) % 180, (h + 105) % 180],
    }

    fig2, axes = plt.subplots(1, 4, figsize=(18, 3))
    fig2.suptitle('Armonías Cromáticas a partir del Color Dominante', fontsize=13, fontweight='bold')

    for ax, (name, hues) in zip(axes, harmonies.items()):
        palette_h = np.zeros((60, len(hues) * 80, 3), dtype=np.uint8)
        for i, hue in enumerate(hues):
            color = hsv_to_rgb_single(hue, s, v)
            palette_h[:, i * 80:(i + 1) * 80] = color
        ax.imshow(palette_h)
        ax.set_title(name, fontsize=10)
        ax.axis('off')

    plt.tight_layout()
    save(fig2, 'python_armonias_cromaticas.png')


# ============================================================
# 7. HISTOGRAMAS Y ECUALIZACIÓN
# ============================================================

def analisis_histogramas():
    """
    Genera histogramas RGB y HSV, aplica ecualización
    estándar y CLAHE (adaptativa), y compara resultados.
    """
    print("\n[7] Análisis de histogramas y ecualización")
    bgr = load_image()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # --- Histograma RGB ---
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.5))
    fig.suptitle('Histogramas de Color', fontsize=13, fontweight='bold')

    axes[0].set_title('Histograma RGB', fontsize=11)
    for i, (color, label) in enumerate(zip(['red', 'green', 'blue'], ['R', 'G', 'B'])):
        hist = cv2.calcHist([rgb], [i], None, [256], [0, 256])
        axes[0].plot(hist, color=color, alpha=0.7, label=label)
    axes[0].set_xlim(0, 255)
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    axes[0].set_xlabel('Valor')
    axes[0].set_ylabel('Frecuencia')

    # Histograma HSV
    hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)
    axes[1].set_title('Histograma HSV', fontsize=11)
    for i, (color, label) in enumerate(zip(['orange', 'cyan', 'gray'], ['H', 'S', 'V'])):
        hist = cv2.calcHist([hsv], [i], None, [256], [0, 256])
        axes[1].plot(hist, color=color, alpha=0.7, label=label)
    axes[1].set_xlim(0, 255)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)
    axes[1].set_xlabel('Valor')

    plt.tight_layout()
    save(fig, 'python_histogramas.png')

    # --- Ecualización ---
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Ecualización estándar
    eq_standard = cv2.equalizeHist(gray)

    # CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    eq_clahe = clahe.apply(gray)

    # Ecualización en LAB (solo canal L)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    lab_clahe = lab.copy()
    lab_clahe[..., 0] = clahe.apply(lab[..., 0])
    eq_lab_bgr = cv2.cvtColor(lab_clahe, cv2.COLOR_LAB2BGR)
    eq_lab_rgb = cv2.cvtColor(eq_lab_bgr, cv2.COLOR_BGR2RGB)

    fig2, axes2 = plt.subplots(2, 4, figsize=(18, 8))
    fig2.suptitle('Ecualización de Histograma: Estándar vs CLAHE', fontsize=14, fontweight='bold')

    imgs = [gray, eq_standard, eq_clahe, eq_lab_rgb]
    titles = ['Original (Gray)', 'Ecualización Estándar', 'CLAHE (Adaptativa)', 'CLAHE en LAB (Color)']

    for i, (img, title) in enumerate(zip(imgs, titles)):
        cmap = 'gray' if i < 3 else None
        axes2[0, i].imshow(img, cmap=cmap)
        axes2[0, i].set_title(title, fontsize=10)
        axes2[0, i].axis('off')

        # Histograma debajo
        if i < 3:
            hist = cv2.calcHist([img], [0], None, [256], [0, 256])
        else:
            gray_eq = cv2.cvtColor(eq_lab_bgr, cv2.COLOR_BGR2GRAY)
            hist = cv2.calcHist([gray_eq], [0], None, [256], [0, 256])
        axes2[1, i].fill_between(range(256), hist.flatten(), alpha=0.6,
                                  color='steelblue' if i == 0 else 'coral' if i == 1 else 'seagreen' if i == 2 else 'mediumpurple')
        axes2[1, i].set_xlim(0, 255)
        axes2[1, i].grid(True, alpha=0.3)
        axes2[1, i].set_xlabel('Intensidad')
        if i == 0:
            axes2[1, i].set_ylabel('Frecuencia')

    plt.tight_layout()
    save(fig2, 'python_ecualizacion.png')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Taller: Conversión y Manipulación de Espacios de Color")
    print("=" * 60)

    conversion_espacios_color()
    visualizacion_3d_espacios()
    segmentacion_por_color()
    manipulacion_color()
    color_grading()
    paletas_colores()
    analisis_histogramas()

    print("\n" + "=" * 60)
    print(f"✅ Todas las visualizaciones generadas en media/")
    n_files = len([f for f in os.listdir(MEDIA_DIR) if f.startswith('python_')])
    print(f"   Total de archivos: {n_files}")
    print("=" * 60)
