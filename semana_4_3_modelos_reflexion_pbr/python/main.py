"""
Taller Modelos de Reflexión: Lambert, Phong y PBR
Implementación en Python con NumPy y Matplotlib

Renderiza esferas con iluminación por píxel usando los modelos:
- Lambert (difuso)
- Phong (especular)
- Blinn-Phong (half vector)
- PBR Cook-Torrance (metalness/roughness)

Genera visualizaciones comparativas y análisis estadístico de intensidades.
"""

import numpy as np
import matplotlib.pyplot as plt
import os

# ============================================================
# Configuración de salida
# ============================================================
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'media')
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# Generación de geometría: esfera paramétrica
# ============================================================

def create_sphere_normals(size=400):
    """
    Genera un mapa de normales para una esfera unitaria proyectada
    ortográficamente sobre un plano 2D.

    Args:
        size: resolución en píxeles (size x size)

    Returns:
        nx, ny, nz: componentes de la normal en cada píxel
        mask: máscara booleana de los píxeles dentro de la esfera
    """
    lin = np.linspace(-1, 1, size)
    x, y = np.meshgrid(lin, -lin)  # y invertido para que arriba sea positivo
    r2 = x**2 + y**2
    mask = r2 <= 1.0

    z = np.zeros_like(r2)
    z[mask] = np.sqrt(1.0 - r2[mask])

    nx = np.zeros_like(r2)
    ny = np.zeros_like(r2)
    nz = np.zeros_like(r2)
    nx[mask] = x[mask]
    ny[mask] = y[mask]
    nz[mask] = z[mask]

    return nx, ny, nz, mask


# ============================================================
# Modelos de iluminación
# ============================================================

def lambert_shading(nx, ny, nz, mask, light_dir, albedo, ambient=0.08):
    """
    Modelo Lambertiano (difuso).
    I_diffuse = I_light * k_d * max(N · L, 0)

    Args:
        nx, ny, nz: componentes de la normal
        mask: máscara de la esfera
        light_dir: dirección de la luz (se normaliza internamente)
        albedo: color difuso [r, g, b] en rango [0, 1]
        ambient: componente ambiente constante

    Returns:
        imagen RGB como array (size, size, 3) en rango [0, 1]
    """
    L = light_dir / np.linalg.norm(light_dir)
    NdotL = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)

    img = np.zeros((*nx.shape, 3))
    for c in range(3):
        img[..., c][mask] = albedo[c] * (ambient + NdotL[mask])

    return np.clip(img, 0, 1)


def phong_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, spec_color, shininess, ambient=0.08):
    """
    Modelo de Phong (difuso + especular).
    I_specular = I_light * k_s * max(R · V, 0)^shininess
    donde R = 2(N·L)N - L

    Args:
        shininess: exponente de brillo (valores típicos: 8-256)
        spec_color: color especular [r, g, b]

    Returns:
        imagen RGB como array (size, size, 3) en rango [0, 1]
    """
    L = light_dir / np.linalg.norm(light_dir)
    V = view_dir / np.linalg.norm(view_dir)

    NdotL = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)

    # Vector de reflexión: R = 2(N·L)N - L
    dot_val = nx * L[0] + ny * L[1] + nz * L[2]
    Rx = 2 * dot_val * nx - L[0]
    Ry = 2 * dot_val * ny - L[1]
    Rz = 2 * dot_val * nz - L[2]

    RdotV = np.clip(Rx * V[0] + Ry * V[1] + Rz * V[2], 0, 1)
    spec = np.power(RdotV, shininess)

    img = np.zeros((*nx.shape, 3))
    for c in range(3):
        diffuse = albedo[c] * NdotL[mask]
        specular = spec_color[c] * spec[mask]
        img[..., c][mask] = ambient * albedo[c] + diffuse + specular

    return np.clip(img, 0, 1)


def blinn_phong_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, spec_color, shininess, ambient=0.08):
    """
    Modelo Blinn-Phong (optimización de Phong con half vector).
    H = normalize(L + V)
    I_specular = I_light * k_s * max(N · H, 0)^shininess

    Más estable en ángulos rasantes y computacionalmente más barato
    que Phong porque evita calcular el vector de reflexión.
    """
    L = light_dir / np.linalg.norm(light_dir)
    V = view_dir / np.linalg.norm(view_dir)
    H = (L + V)
    H = H / np.linalg.norm(H)

    NdotL = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    NdotH = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1)
    spec = np.power(NdotH, shininess)

    img = np.zeros((*nx.shape, 3))
    for c in range(3):
        diffuse = albedo[c] * NdotL[mask]
        specular = spec_color[c] * spec[mask]
        img[..., c][mask] = ambient * albedo[c] + diffuse + specular

    return np.clip(img, 0, 1)


def pbr_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, metalness, roughness, ambient=0.08):
    """
    Modelo PBR (Physically Based Rendering) con Cook-Torrance BRDF.

    Componentes:
    - GGX/Trowbridge-Reitz Normal Distribution Function (NDF)
    - Fresnel-Schlick approximation
    - Schlick-GGX Geometry Function

    Args:
        metalness: 0.0 = dieléctrico, 1.0 = metal
        roughness: 0.0 = espejo perfecto, 1.0 = mate total

    Returns:
        imagen RGB con tone mapping Reinhard aplicado
    """
    L = light_dir / np.linalg.norm(light_dir)
    V = view_dir / np.linalg.norm(view_dir)
    H = (L + V)
    H = H / np.linalg.norm(H)

    NdotL = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    NdotH = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1)
    NdotV = np.clip(nx * V[0] + ny * V[1] + nz * V[2], 0, 1)

    # F0: reflectancia a incidencia normal
    # Dieléctricos: ~0.04, Metales: color del albedo
    f0_dielectric = np.array([0.04, 0.04, 0.04])
    f0 = np.zeros((*nx.shape, 3))
    for c in range(3):
        f0[..., c] = f0_dielectric[c] * (1 - metalness) + albedo[c] * metalness

    # Fresnel-Schlick: F(θ) = F0 + (1 - F0)(1 - cosθ)^5
    cosTheta = NdotV
    fresnel = np.zeros((*nx.shape, 3))
    for c in range(3):
        fresnel[..., c] = f0[..., c] + (1.0 - f0[..., c]) * np.power(
            np.clip(1.0 - cosTheta, 0, 1), 5
        )

    # GGX Normal Distribution Function
    # D(h) = α² / (π * ((N·H)²(α²-1) + 1)²)
    a = roughness * roughness
    a2 = a * a
    denom = NdotH * NdotH * (a2 - 1.0) + 1.0
    D = a2 / (np.pi * denom * denom + 1e-7)

    # Schlick-GGX Geometry Function
    # G(v) = (N·V) / ((N·V)(1-k) + k), donde k = (roughness+1)²/8
    k = (roughness + 1.0) ** 2 / 8.0
    G1_V = NdotV / (NdotV * (1 - k) + k + 1e-7)
    G1_L = NdotL / (NdotL * (1 - k) + k + 1e-7)
    G = G1_V * G1_L

    # Cook-Torrance specular BRDF
    spec_denom = 4.0 * NdotV * NdotL + 1e-7

    img = np.zeros((*nx.shape, 3))
    for c in range(3):
        specular = (D * fresnel[..., c] * G) / spec_denom

        # kd: energía difusa restante después de la reflexión especular
        # Los metales no tienen componente difusa (toda la energía es especular)
        kd = (1.0 - fresnel[..., c]) * (1.0 - metalness)
        diffuse = kd * albedo[c] / np.pi

        result = (diffuse + specular) * NdotL
        img[..., c][mask] = ambient * albedo[c] + result[mask]

    # Tone mapping (Reinhard) para mapear HDR a [0, 1]
    img = img / (img + 1.0)

    return np.clip(img, 0, 1)


# ============================================================
# Visualizaciones
# ============================================================

def plot_model_comparison(output_path):
    """Genera una comparación visual de los 4 modelos sobre la misma esfera."""
    size = 400
    nx, ny, nz, mask = create_sphere_normals(size)

    light_dir = np.array([0.5, 0.65, 1.0])
    view_dir = np.array([0.0, 0.0, 1.0])
    albedo = np.array([0.80, 0.50, 0.25])
    spec_color = np.array([1.0, 1.0, 1.0])

    models = [
        ("Lambert (Difuso)", lambert_shading(nx, ny, nz, mask, light_dir, albedo)),
        ("Phong (shininess=32)", phong_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, spec_color, 32)),
        ("Blinn-Phong (shininess=64)", blinn_phong_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, spec_color, 64)),
        ("PBR (metal=0.3, rough=0.4)", pbr_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, 0.3, 0.4)),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(20, 5))
    fig.suptitle('Comparación de Modelos de Reflexión', fontsize=14, fontweight='bold')

    for ax, (title, img) in zip(axes, models):
        display = img.copy()
        for c in range(3):
            display[..., c][~mask] = 1.0
        ax.imshow(display)
        ax.set_title(title, fontsize=11)
        ax.axis('off')

    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ {output_path}")


def plot_intensity_histograms(output_path):
    """Genera histogramas de distribución de intensidad por modelo."""
    size = 400
    nx, ny, nz, mask = create_sphere_normals(size)

    light_dir = np.array([0.5, 0.65, 1.0])
    view_dir = np.array([0.0, 0.0, 1.0])
    albedo = np.array([0.80, 0.50, 0.25])
    spec_color = np.array([1.0, 1.0, 1.0])

    L = light_dir / np.linalg.norm(light_dir)
    V = view_dir / np.linalg.norm(view_dir)
    H = (L + V); H = H / np.linalg.norm(H)

    # Lambert: solo N·L
    NdotL = np.clip(nx * L[0] + ny * L[1] + nz * L[2], 0, 1)
    intensities_lambert = NdotL[mask]

    # Phong: N·L + (R·V)^32
    NdotH = np.clip(nx * H[0] + ny * H[1] + nz * H[2], 0, 1)
    intensities_phong = (NdotL + np.power(NdotH, 32))[mask]

    # PBR
    img_pbr = pbr_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, 0.3, 0.4)
    intensities_pbr = (img_pbr[..., 0] + img_pbr[..., 1] + img_pbr[..., 2])[mask] / 3.0

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    fig.suptitle('Distribución de Intensidades por Modelo de Iluminación',
                 fontsize=13, fontweight='bold')

    axes[0].hist(intensities_lambert, bins=60, color='#3b82f6', alpha=0.85, edgecolor='#2563eb')
    axes[0].set_title('Lambert (Difuso)', fontsize=11)
    axes[0].set_xlabel('Intensidad N·L')
    axes[0].set_ylabel('Frecuencia (píxeles)')
    axes[0].grid(True, alpha=0.3)

    axes[1].hist(intensities_phong, bins=60, color='#f97316', alpha=0.85, edgecolor='#ea580c')
    axes[1].set_title('Phong (Difuso + Especular)', fontsize=11)
    axes[1].set_xlabel('Intensidad total')
    axes[1].grid(True, alpha=0.3)

    axes[2].hist(intensities_pbr, bins=60, color='#22c55e', alpha=0.85, edgecolor='#16a34a')
    axes[2].set_title('PBR (Cook-Torrance)', fontsize=11)
    axes[2].set_xlabel('Luminancia promedio')
    axes[2].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ {output_path}")


def plot_pbr_sweep(output_path):
    """Genera un barrido de parámetros PBR: dieléctrico vs metal × roughness."""
    size = 200
    nx, ny, nz, mask = create_sphere_normals(size)

    light_dir = np.array([0.5, 0.65, 1.0])
    view_dir = np.array([0.0, 0.0, 1.0])
    albedo = np.array([0.80, 0.50, 0.25])

    roughness_values = [0.1, 0.3, 0.5, 0.7, 0.9]

    fig, axes = plt.subplots(2, 5, figsize=(16, 7))
    fig.suptitle('Barrido de Parámetros PBR: Metalness vs Roughness',
                 fontsize=14, fontweight='bold')

    for col, rough in enumerate(roughness_values):
        # Fila superior: dieléctrico (metal=0)
        img = pbr_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, metalness=0.0, roughness=rough)
        for c in range(3):
            img[..., c][~mask] = 1.0
        axes[0, col].imshow(img)
        axes[0, col].set_title(f'rough={rough}', fontsize=9)
        axes[0, col].axis('off')
        if col == 0:
            axes[0, col].set_ylabel('Dieléctrico\n(metal=0)', fontsize=10)

        # Fila inferior: metal (metal=1)
        img = pbr_shading(nx, ny, nz, mask, light_dir, view_dir, albedo, metalness=1.0, roughness=rough)
        for c in range(3):
            img[..., c][~mask] = 1.0
        axes[1, col].imshow(img)
        axes[1, col].set_title(f'rough={rough}', fontsize=9)
        axes[1, col].axis('off')
        if col == 0:
            axes[1, col].set_ylabel('Metal\n(metal=1)', fontsize=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=130, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"  ✓ {output_path}")


# ============================================================
# Main
# ============================================================

if __name__ == '__main__':
    print("Generando visualizaciones...\n")

    plot_model_comparison(os.path.join(OUTPUT_DIR, 'python_comparacion_modelos.png'))
    plot_intensity_histograms(os.path.join(OUTPUT_DIR, 'python_histograma_intensidades.png'))
    plot_pbr_sweep(os.path.join(OUTPUT_DIR, 'python_pbr_sweep.png'))

    print("\n✅ Todas las visualizaciones generadas en media/")
