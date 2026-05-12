"""
Taller Ojos Digitales: Introducción a la Visión Artificial
============================================================

Implementa el pipeline completo de percepción visual artificial:
1. Conversión a escala de grises
2. Filtros convolucionales (blur, sharpening, emboss)
3. Detección de bordes: Sobel X/Y, Laplaciano, Canny
4. Comparación visual entre métodos
5. Análisis de kernels de convolución
6. Combinación de técnicas para detección robusta
"""

import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os

# ============================================================
# Configuración
# ============================================================

MEDIA_DIR = os.path.join(os.path.dirname(__file__), '..', 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)

IMG_PATH = os.path.join(os.path.dirname(__file__), 'input_image.jpg')


def save(fig, name):
    path = os.path.join(MEDIA_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  ✓ {name}")


def load():
    img = cv2.imread(IMG_PATH)
    if img is None:
        raise FileNotFoundError(f"No se encontró: {IMG_PATH}")
    return img


# ============================================================
# 1. CONVERSIÓN A ESCALA DE GRISES
# ============================================================

def grayscale_conversion():
    """
    Convierte la imagen a escala de grises y muestra los componentes
    de luminancia ponderada: Y = 0.299R + 0.587G + 0.114B.
    """
    print("\n[1] Conversión a escala de grises")
    bgr = load()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Grises por canal individual
    gray_r = rgb[..., 0]
    gray_g = rgb[..., 1]
    gray_b = rgb[..., 2]

    # Gris ponderado manual
    gray_weighted = (0.299 * rgb[..., 0] + 0.587 * rgb[..., 1] + 0.114 * rgb[..., 2]).astype(np.uint8)

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle('Conversión a Escala de Grises — Métodos y Canales', fontsize=14, fontweight='bold')

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title('Original (Color)', fontsize=11)

    axes[0, 1].imshow(gray, cmap='gray')
    axes[0, 1].set_title('cv2.cvtColor (BGR2GRAY)', fontsize=11)

    axes[0, 2].imshow(gray_weighted, cmap='gray')
    axes[0, 2].set_title('Manual: 0.299R + 0.587G + 0.114B', fontsize=11)

    axes[1, 0].imshow(gray_r, cmap='gray')
    axes[1, 0].set_title('Solo canal Rojo', fontsize=11)

    axes[1, 1].imshow(gray_g, cmap='gray')
    axes[1, 1].set_title('Solo canal Verde', fontsize=11)

    axes[1, 2].imshow(gray_b, cmap='gray')
    axes[1, 2].set_title('Solo canal Azul', fontsize=11)

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_escala_grises.png')


# ============================================================
# 2. FILTROS CONVOLUCIONALES
# ============================================================

def convolution_filters():
    """
    Aplica filtros convolucionales: blur (box, gaussian, median),
    sharpening y emboss.
    """
    print("\n[2] Filtros convolucionales")
    bgr = load()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # --- Filtros de suavizado ---
    box_blur_3 = cv2.blur(rgb, (3, 3))
    box_blur_7 = cv2.blur(rgb, (7, 7))
    box_blur_15 = cv2.blur(rgb, (15, 15))
    gaussian = cv2.GaussianBlur(rgb, (7, 7), 0)
    median = cv2.medianBlur(rgb, 7)
    bilateral = cv2.bilateralFilter(rgb, 9, 75, 75)

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle('Filtros de Suavizado (Blur)', fontsize=14, fontweight='bold')

    results = [
        (box_blur_3, 'Box Blur 3×3'),
        (box_blur_7, 'Box Blur 7×7'),
        (box_blur_15, 'Box Blur 15×15'),
        (gaussian, 'Gaussian Blur 7×7'),
        (median, 'Median Blur k=7'),
        (bilateral, 'Bilateral Filter d=9'),
    ]

    for ax, (img, title) in zip(axes.flat, results):
        ax.imshow(img)
        ax.set_title(title, fontsize=11)
        ax.axis('off')

    plt.tight_layout()
    save(fig, 'python_filtros_blur.png')

    # --- Sharpening y Emboss ---
    kernel_sharpen = np.array([
        [ 0, -1,  0],
        [-1,  5, -1],
        [ 0, -1,  0]
    ], dtype=np.float32)

    kernel_sharpen_strong = np.array([
        [-1, -1, -1],
        [-1,  9, -1],
        [-1, -1, -1]
    ], dtype=np.float32)

    kernel_emboss = np.array([
        [-2, -1, 0],
        [-1,  1, 1],
        [ 0,  1, 2]
    ], dtype=np.float32)

    kernel_edge_enhance = np.array([
        [ 0,  0,  0],
        [-1,  1,  0],
        [ 0,  0,  0]
    ], dtype=np.float32)

    sharpened = cv2.filter2D(rgb, -1, kernel_sharpen)
    sharpened_strong = cv2.filter2D(rgb, -1, kernel_sharpen_strong)
    embossed = cv2.filter2D(cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY), -1, kernel_emboss)
    edge_enhanced = cv2.filter2D(rgb, -1, kernel_edge_enhance)

    fig2, axes2 = plt.subplots(2, 3, figsize=(17, 10))
    fig2.suptitle('Filtros de Sharpening, Emboss y Realce de Bordes', fontsize=14, fontweight='bold')

    axes2[0, 0].imshow(rgb)
    axes2[0, 0].set_title('Original', fontsize=11)

    axes2[0, 1].imshow(sharpened)
    axes2[0, 1].set_title('Sharpen (Leve)', fontsize=11)

    axes2[0, 2].imshow(sharpened_strong)
    axes2[0, 2].set_title('Sharpen (Fuerte)', fontsize=11)

    axes2[1, 0].imshow(embossed, cmap='gray')
    axes2[1, 0].set_title('Emboss', fontsize=11)

    axes2[1, 1].imshow(np.clip(edge_enhanced, 0, 255).astype(np.uint8))
    axes2[1, 1].set_title('Edge Enhance', fontsize=11)

    # Unsharp mask
    blurred = cv2.GaussianBlur(rgb, (7, 7), 2)
    unsharp = cv2.addWeighted(rgb, 1.5, blurred, -0.5, 0)
    axes2[1, 2].imshow(unsharp)
    axes2[1, 2].set_title('Unsharp Mask (1.5x - 0.5×blur)', fontsize=11)

    for ax in axes2.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig2, 'python_filtros_sharpen.png')


# ============================================================
# 3. VISUALIZACIÓN DE KERNELS
# ============================================================

def visualize_kernels():
    """Visualiza los kernels de convolución utilizados."""
    print("\n[3] Visualización de kernels")

    kernels = {
        'Box Blur 3×3': np.ones((3, 3)) / 9,
        'Gaussian 3×3\n(aprox)': np.array([[1,2,1],[2,4,2],[1,2,1]]) / 16,
        'Sharpen': np.array([[0,-1,0],[-1,5,-1],[0,-1,0]], dtype=float),
        'Sobel X': np.array([[-1,0,1],[-2,0,2],[-1,0,1]], dtype=float),
        'Sobel Y': np.array([[-1,-2,-1],[0,0,0],[1,2,1]], dtype=float),
        'Laplacian': np.array([[0,1,0],[1,-4,1],[0,1,0]], dtype=float),
        'Emboss': np.array([[-2,-1,0],[-1,1,1],[0,1,2]], dtype=float),
        'Edge Detect': np.array([[-1,-1,-1],[-1,8,-1],[-1,-1,-1]], dtype=float),
    }

    fig, axes = plt.subplots(2, 4, figsize=(18, 8))
    fig.suptitle('Kernels de Convolución Utilizados', fontsize=14, fontweight='bold')

    for ax, (name, kernel) in zip(axes.flat, kernels.items()):
        im = ax.imshow(kernel, cmap='RdBu_r', vmin=-5, vmax=5)
        ax.set_title(name, fontsize=10)

        # Anotar valores en cada celda
        for i in range(kernel.shape[0]):
            for j in range(kernel.shape[1]):
                val = kernel[i, j]
                color = 'white' if abs(val) > 2.5 else 'black'
                text = f'{val:.1f}' if val != int(val) else f'{int(val)}'
                ax.text(j, i, text, ha='center', va='center', fontsize=9,
                        color=color, fontweight='bold')
        ax.set_xticks([])
        ax.set_yticks([])

    plt.tight_layout()
    save(fig, 'python_kernels_convolucion.png')


# ============================================================
# 4. DETECCIÓN DE BORDES: SOBEL
# ============================================================

def edge_detection_sobel():
    """
    Detección de bordes con filtro de Sobel en X e Y,
    y combinación de ambos con magnitud del gradiente.
    """
    print("\n[4] Detección de bordes — Sobel")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # Preprocesamiento: suavizado para reducir ruido
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # Sobel en X (bordes verticales)
    sobel_x = cv2.Sobel(gray_blur, cv2.CV_64F, 1, 0, ksize=3)
    sobel_x_abs = cv2.convertScaleAbs(sobel_x)

    # Sobel en Y (bordes horizontales)
    sobel_y = cv2.Sobel(gray_blur, cv2.CV_64F, 0, 1, ksize=3)
    sobel_y_abs = cv2.convertScaleAbs(sobel_y)

    # Magnitud del gradiente: sqrt(Gx² + Gy²)
    magnitude = cv2.magnitude(sobel_x, sobel_y)
    magnitude_norm = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Dirección del gradiente
    direction = np.arctan2(sobel_y, sobel_x)
    direction_norm = ((direction + np.pi) / (2 * np.pi) * 255).astype(np.uint8)

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle('Detección de Bordes — Filtro de Sobel', fontsize=14, fontweight='bold')

    axes[0, 0].imshow(gray, cmap='gray')
    axes[0, 0].set_title('Escala de Grises (entrada)', fontsize=11)

    axes[0, 1].imshow(sobel_x_abs, cmap='gray')
    axes[0, 1].set_title('Sobel X (bordes verticales)', fontsize=11)

    axes[0, 2].imshow(sobel_y_abs, cmap='gray')
    axes[0, 2].set_title('Sobel Y (bordes horizontales)', fontsize=11)

    axes[1, 0].imshow(magnitude_norm, cmap='gray')
    axes[1, 0].set_title('Magnitud: √(Gx² + Gy²)', fontsize=11)

    axes[1, 1].imshow(magnitude_norm, cmap='hot')
    axes[1, 1].set_title('Magnitud (mapa de calor)', fontsize=11)

    axes[1, 2].imshow(direction_norm, cmap='hsv')
    axes[1, 2].set_title('Dirección del gradiente', fontsize=11)

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_bordes_sobel.png')


# ============================================================
# 5. DETECCIÓN DE BORDES: LAPLACIANO
# ============================================================

def edge_detection_laplacian():
    """
    Detección de bordes con filtro Laplaciano.
    Compara diferentes tamaños de kernel.
    """
    print("\n[5] Detección de bordes — Laplaciano")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # Laplaciano con diferentes kernels
    lap_1 = cv2.Laplacian(gray_blur, cv2.CV_64F, ksize=1)
    lap_3 = cv2.Laplacian(gray_blur, cv2.CV_64F, ksize=3)
    lap_5 = cv2.Laplacian(gray_blur, cv2.CV_64F, ksize=5)

    lap_1_abs = cv2.convertScaleAbs(lap_1)
    lap_3_abs = cv2.convertScaleAbs(lap_3)
    lap_5_abs = cv2.convertScaleAbs(lap_5)

    # LoG (Laplacian of Gaussian)
    gray_heavy_blur = cv2.GaussianBlur(gray, (7, 7), 2)
    log = cv2.Laplacian(gray_heavy_blur, cv2.CV_64F, ksize=3)
    log_abs = cv2.convertScaleAbs(log)

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle('Detección de Bordes — Filtro Laplaciano', fontsize=14, fontweight='bold')

    axes[0, 0].imshow(gray, cmap='gray')
    axes[0, 0].set_title('Escala de Grises (entrada)', fontsize=11)

    axes[0, 1].imshow(lap_1_abs, cmap='gray')
    axes[0, 1].set_title('Laplaciano ksize=1', fontsize=11)

    axes[0, 2].imshow(lap_3_abs, cmap='gray')
    axes[0, 2].set_title('Laplaciano ksize=3', fontsize=11)

    axes[1, 0].imshow(lap_5_abs, cmap='gray')
    axes[1, 0].set_title('Laplaciano ksize=5', fontsize=11)

    axes[1, 1].imshow(log_abs, cmap='gray')
    axes[1, 1].set_title('LoG (Laplacian of Gaussian)', fontsize=11)

    axes[1, 2].imshow(lap_3_abs, cmap='inferno')
    axes[1, 2].set_title('Laplaciano k=3 (mapa de calor)', fontsize=11)

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_bordes_laplaciano.png')


# ============================================================
# 6. CANNY EDGE DETECTION
# ============================================================

def edge_detection_canny():
    """Detección de bordes con Canny variando umbrales."""
    print("\n[6] Detección de bordes — Canny")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (5, 5), 1)

    thresholds = [
        (30, 80, 'Bajo (30/80)'),
        (50, 150, 'Medio (50/150)'),
        (100, 200, 'Alto (100/200)'),
        (150, 250, 'Muy alto (150/250)'),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    fig.suptitle('Detección de Bordes — Canny con Diferentes Umbrales', fontsize=14, fontweight='bold')

    for ax, (low, high, label) in zip(axes, thresholds):
        edges = cv2.Canny(gray_blur, low, high)
        ax.imshow(edges, cmap='gray')
        ax.set_title(f'Canny {label}', fontsize=11)
        ax.axis('off')

    plt.tight_layout()
    save(fig, 'python_bordes_canny.png')


# ============================================================
# 7. COMPARACIÓN ENTRE MÉTODOS
# ============================================================

def comparison():
    """Comparación visual directa entre Sobel, Laplaciano y Canny."""
    print("\n[7] Comparación entre métodos de detección de bordes")
    bgr = load()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.GaussianBlur(gray, (3, 3), 0)

    # Sobel combinado
    sobel_x = cv2.Sobel(gray_blur, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(gray_blur, cv2.CV_64F, 0, 1, ksize=3)
    sobel = cv2.normalize(cv2.magnitude(sobel_x, sobel_y), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    # Laplaciano
    lap = cv2.convertScaleAbs(cv2.Laplacian(gray_blur, cv2.CV_64F, ksize=3))

    # Canny
    canny = cv2.Canny(gray_blur, 50, 150)

    # Overlay de bordes sobre la imagen original
    overlay = rgb.copy()
    overlay[canny > 0] = [0, 255, 0]

    fig, axes = plt.subplots(2, 3, figsize=(17, 10))
    fig.suptitle('Comparación de Métodos de Detección de Bordes', fontsize=14, fontweight='bold')

    axes[0, 0].imshow(rgb)
    axes[0, 0].set_title('Original', fontsize=11)

    axes[0, 1].imshow(gray, cmap='gray')
    axes[0, 1].set_title('Escala de Grises', fontsize=11)

    axes[0, 2].imshow(sobel, cmap='gray')
    axes[0, 2].set_title('Sobel (Magnitud)', fontsize=11)

    axes[1, 0].imshow(lap, cmap='gray')
    axes[1, 0].set_title('Laplaciano', fontsize=11)

    axes[1, 1].imshow(canny, cmap='gray')
    axes[1, 1].set_title('Canny (50/150)', fontsize=11)

    axes[1, 2].imshow(overlay)
    axes[1, 2].set_title('Canny superpuesto (verde)', fontsize=11)

    for ax in axes.flat:
        ax.axis('off')
    plt.tight_layout()
    save(fig, 'python_comparacion_bordes.png')


# ============================================================
# 8. PIPELINE COMPLETO
# ============================================================

def full_pipeline():
    """Pipeline de visión: original → gris → blur → bordes → overlay."""
    print("\n[8] Pipeline completo de visión artificial")
    bgr = load()
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 1)
    canny = cv2.Canny(blur, 50, 150)

    # Dilatar bordes para visualización
    kernel = np.ones((2, 2), np.uint8)
    canny_thick = cv2.dilate(canny, kernel, iterations=1)

    overlay = rgb.copy()
    overlay[canny_thick > 0] = [50, 255, 50]

    fig, axes = plt.subplots(1, 5, figsize=(22, 4.5))
    fig.suptitle('Pipeline de Visión Artificial: De Imagen a Bordes', fontsize=14, fontweight='bold')

    steps = [
        (rgb, 'gray', '1. Original', None),
        (gray, 'gray', '2. Escala de Grises', 'gray'),
        (blur, 'gray', '3. Gaussian Blur', 'gray'),
        (canny, 'gray', '4. Canny Edges', 'gray'),
        (overlay, None, '5. Overlay', None),
    ]

    for ax, (img, _, title, cmap) in zip(axes, steps):
        if cmap:
            ax.imshow(img, cmap=cmap)
        else:
            ax.imshow(img)
        ax.set_title(title, fontsize=10)
        ax.axis('off')

    # Flechas entre pasos
    for i in range(4):
        fig.text(0.19 + i * 0.19, 0.02, '→', fontsize=20, ha='center', color='#64748b')

    plt.tight_layout(rect=[0, 0.05, 1, 0.95])
    save(fig, 'python_pipeline_completo.png')


# ============================================================
# 9. ANÁLISIS DE HISTOGRAMA DE BORDES
# ============================================================

def edge_histogram():
    """Histograma de intensidades de bordes por método."""
    print("\n[9] Histograma de intensidades de bordes")
    bgr = load()
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (3, 3), 0)

    sobel_x = cv2.Sobel(blur, cv2.CV_64F, 1, 0, ksize=3)
    sobel_y = cv2.Sobel(blur, cv2.CV_64F, 0, 1, ksize=3)
    sobel_mag = cv2.normalize(cv2.magnitude(sobel_x, sobel_y), None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    lap = cv2.convertScaleAbs(cv2.Laplacian(blur, cv2.CV_64F, ksize=3))
    canny = cv2.Canny(blur, 50, 150)

    fig, axes = plt.subplots(1, 3, figsize=(16, 4.5))
    fig.suptitle('Distribución de Intensidades de Bordes por Método', fontsize=13, fontweight='bold')

    axes[0].hist(sobel_mag.ravel(), bins=80, color='#3b82f6', alpha=0.8, edgecolor='#2563eb')
    axes[0].set_title('Sobel (Magnitud)', fontsize=11)
    axes[0].set_xlabel('Intensidad')
    axes[0].set_ylabel('Frecuencia')
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(lap.ravel(), bins=80, color='#f97316', alpha=0.8, edgecolor='#ea580c')
    axes[1].set_title('Laplaciano', fontsize=11)
    axes[1].set_xlabel('Intensidad')
    axes[1].grid(True, alpha=0.3)

    axes[2].hist(canny.ravel(), bins=3, color='#22c55e', alpha=0.8, edgecolor='#16a34a')
    axes[2].set_title('Canny (binario: 0 o 255)', fontsize=11)
    axes[2].set_xlabel('Intensidad')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    save(fig, 'python_histograma_bordes.png')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Taller: Ojos Digitales — Visión Artificial con OpenCV")
    print("=" * 60)

    grayscale_conversion()
    convolution_filters()
    visualize_kernels()
    edge_detection_sobel()
    edge_detection_laplacian()
    edge_detection_canny()
    comparison()
    full_pipeline()
    edge_histogram()

    print("\n" + "=" * 60)
    n = len([f for f in os.listdir(MEDIA_DIR) if f.startswith('python_')])
    print(f"✅ {n} visualizaciones generadas en media/")
    print("=" * 60)
