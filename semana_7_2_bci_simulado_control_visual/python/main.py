"""
Taller BCI Simulado: Señales Mentales Artificiales para Control Visual
=======================================================================

Módulo principal que implementa:
1. Carga y visualización de señales EEG (amplitud vs tiempo)
2. Filtrado pasa banda: Alpha (8-12 Hz) y Beta (12-30 Hz)
3. Análisis espectral (PSD) y espectrograma
4. Detección de nivel de atención (potencia Alpha vs umbral)
5. Simulación de control visual BCI (cambio de color, movimiento)
6. Dashboard integrado de monitoreo BCI en tiempo real
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Circle, FancyBboxPatch
from matplotlib.collections import LineCollection
from scipy import signal
import os
import imageio

# ============================================================
# Configuración
# ============================================================

MEDIA_DIR = os.path.join(os.path.dirname(__file__), '..', 'media')
os.makedirs(MEDIA_DIR, exist_ok=True)

FS = 256  # Frecuencia de muestreo (Hz)

# Bandas de frecuencia EEG
BANDS = {
    'Delta':  (0.5, 4),
    'Theta':  (4, 8),
    'Alpha':  (8, 12),
    'Beta':   (12, 30),
    'Gamma':  (30, 50),
}

BAND_COLORS = {
    'Delta':  '#6366f1',
    'Theta':  '#8b5cf6',
    'Alpha':  '#06b6d4',
    'Beta':   '#f97316',
    'Gamma':  '#ef4444',
}


def save(fig, name):
    path = os.path.join(MEDIA_DIR, name)
    fig.savefig(path, dpi=140, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"  ✓ {name}")


def load_eeg():
    """Carga el CSV de señales EEG."""
    csv_path = os.path.join(os.path.dirname(__file__), 'eeg_synthetic.csv')
    if not os.path.exists(csv_path):
        from generate_eeg import export_csv
        export_csv()
    return pd.read_csv(csv_path)


def bandpass_filter(data, lowcut, highcut, fs=FS, order=4):
    """
    Filtro Butterworth pasa banda.

    Args:
        data: señal de entrada
        lowcut, highcut: frecuencias de corte (Hz)
        fs: frecuencia de muestreo
        order: orden del filtro

    Returns:
        señal filtrada
    """
    nyq = 0.5 * fs
    low = lowcut / nyq
    high = highcut / nyq
    b, a = signal.butter(order, [low, high], btype='band')
    return signal.filtfilt(b, a, data)


def compute_band_power(data, lowcut, highcut, fs=FS, window_sec=1.0):
    """
    Calcula la potencia en una banda de frecuencia usando ventanas deslizantes.

    Returns:
        power: array con la potencia por ventana
        times: centros temporales de cada ventana
    """
    filtered = bandpass_filter(data, lowcut, highcut, fs)
    window_samples = int(window_sec * fs)
    hop = window_samples // 2  # 50% overlap

    powers = []
    times = []

    for start in range(0, len(filtered) - window_samples, hop):
        segment = filtered[start:start + window_samples]
        power = np.mean(segment ** 2)
        powers.append(power)
        times.append((start + window_samples / 2) / fs)

    return np.array(powers), np.array(times)


# ============================================================
# 1. VISUALIZACIÓN DE SEÑALES CRUDAS
# ============================================================

def plot_raw_signals():
    """Visualiza las señales EEG crudas multicanal."""
    print("\n[1] Visualización de señales EEG crudas")
    df = load_eeg()
    t = df['time'].values
    channels = [c for c in df.columns if c not in ['time', 'state']]

    fig, axes = plt.subplots(len(channels), 1, figsize=(16, 2.5 * len(channels)), sharex=True)
    fig.suptitle('Señales EEG Sintéticas — Multicanal (30 segundos)', fontsize=14, fontweight='bold')

    # Color de fondo por estado
    states = df['state'].values
    for ax, ch in zip(axes, channels):
        ax.plot(t, df[ch].values, color='#1e293b', linewidth=0.4, alpha=0.9)
        ax.set_ylabel(f'{ch}\n(μV)', fontsize=10)
        ax.grid(True, alpha=0.2)
        ax.set_xlim(t[0], t[-1])

        # Sombrear estados
        in_focus = False
        start_focus = 0
        for i in range(1, len(states)):
            if states[i] == 'focus' and not in_focus:
                start_focus = t[i]
                in_focus = True
            elif states[i] != 'focus' and in_focus:
                ax.axvspan(start_focus, t[i], alpha=0.08, color='#f97316')
                in_focus = False
        if in_focus:
            ax.axvspan(start_focus, t[-1], alpha=0.08, color='#f97316')

    axes[-1].set_xlabel('Tiempo (s)', fontsize=11)

    # Leyenda de estados
    axes[0].text(0.01, 0.95, '■ Fondo naranja = Estado Focus (Beta alto)',
                 transform=axes[0].transAxes, fontsize=8, color='#f97316', va='top')
    axes[0].text(0.01, 0.82, '■ Fondo blanco = Estado Relax (Alpha alto)',
                 transform=axes[0].transAxes, fontsize=8, color='#06b6d4', va='top')

    plt.tight_layout()
    save(fig, 'python_señales_crudas.png')

    # --- Zoom de 3 segundos ---
    fig2, ax2 = plt.subplots(figsize=(14, 4))
    zoom_start, zoom_end = 4.5, 7.5
    mask = (t >= zoom_start) & (t <= zoom_end)
    ax2.plot(t[mask], df['Fp1'].values[mask], color='#1e293b', linewidth=0.8)
    ax2.set_title(f'Zoom: Canal Fp1 ({zoom_start}–{zoom_end}s) — Estado Relax → Focus',
                  fontsize=13, fontweight='bold')
    ax2.set_xlabel('Tiempo (s)')
    ax2.set_ylabel('Amplitud (μV)')
    ax2.grid(True, alpha=0.3)
    ax2.axvline(5.0, color='#f97316', linestyle='--', alpha=0.7, label='Transición a Focus')
    ax2.legend()
    save(fig2, 'python_zoom_señal.png')


# ============================================================
# 2. FILTRADO PASA BANDA
# ============================================================

def plot_filtered_signals():
    """Aplica y visualiza filtros pasa banda para Alpha y Beta."""
    print("\n[2] Filtrado pasa banda Alpha y Beta")
    df = load_eeg()
    t = df['time'].values
    raw = df['Fp1'].values

    alpha_filtered = bandpass_filter(raw, 8, 12, FS)
    beta_filtered = bandpass_filter(raw, 12, 30, FS)

    fig, axes = plt.subplots(3, 1, figsize=(16, 9), sharex=True)
    fig.suptitle('Filtrado Pasa Banda — Canal Fp1', fontsize=14, fontweight='bold')

    # Señal cruda
    axes[0].plot(t, raw, color='#475569', linewidth=0.4)
    axes[0].set_ylabel('Cruda (μV)')
    axes[0].set_title('Señal EEG sin filtrar', fontsize=11)
    axes[0].grid(True, alpha=0.2)

    # Alpha filtrado
    axes[1].plot(t, alpha_filtered, color='#06b6d4', linewidth=0.6)
    axes[1].set_ylabel('Alpha (μV)')
    axes[1].set_title('Banda Alpha (8–12 Hz) — Relajación', fontsize=11)
    axes[1].grid(True, alpha=0.2)

    # Beta filtrado
    axes[2].plot(t, beta_filtered, color='#f97316', linewidth=0.6)
    axes[2].set_ylabel('Beta (μV)')
    axes[2].set_title('Banda Beta (12–30 Hz) — Concentración', fontsize=11)
    axes[2].grid(True, alpha=0.2)

    axes[-1].set_xlabel('Tiempo (s)')
    axes[0].set_xlim(t[0], t[-1])

    # Sombrear estados
    states = df['state'].values
    for ax in axes:
        in_focus = False
        start = 0
        for i in range(1, len(states)):
            if states[i] == 'focus' and not in_focus:
                start = t[i]
                in_focus = True
            elif states[i] != 'focus' and in_focus:
                ax.axvspan(start, t[i], alpha=0.06, color='#f97316')
                in_focus = False
        if in_focus:
            ax.axvspan(start, t[-1], alpha=0.06, color='#f97316')

    plt.tight_layout()
    save(fig, 'python_filtrado_bandas.png')

    # --- Respuesta en frecuencia del filtro ---
    fig2, ax = plt.subplots(figsize=(10, 5))
    ax.set_title('Respuesta en Frecuencia de los Filtros Butterworth (Orden 4)', fontsize=13, fontweight='bold')

    for band_name, (low, high), color in [('Alpha', (8, 12), '#06b6d4'), ('Beta', (12, 30), '#f97316')]:
        b, a = signal.butter(4, [low / (FS / 2), high / (FS / 2)], btype='band')
        w, h = signal.freqz(b, a, worN=2048, fs=FS)
        ax.plot(w, 20 * np.log10(np.abs(h) + 1e-10), color=color, linewidth=2, label=f'{band_name} ({low}–{high} Hz)')

    ax.set_xlabel('Frecuencia (Hz)')
    ax.set_ylabel('Magnitud (dB)')
    ax.set_xlim(0, 50)
    ax.set_ylim(-60, 5)
    ax.axhline(-3, color='gray', linestyle='--', alpha=0.5, label='-3 dB')
    ax.legend()
    ax.grid(True, alpha=0.3)
    save(fig2, 'python_respuesta_filtros.png')


# ============================================================
# 3. ANÁLISIS ESPECTRAL
# ============================================================

def plot_spectral_analysis():
    """PSD y espectrograma de la señal EEG."""
    print("\n[3] Análisis espectral (PSD y Espectrograma)")
    df = load_eeg()
    raw = df['Fp1'].values

    # --- PSD (Welch) ---
    freqs, psd = signal.welch(raw, fs=FS, nperseg=FS * 2, noverlap=FS)

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    fig.suptitle('Análisis Espectral — Canal Fp1', fontsize=14, fontweight='bold')

    ax = axes[0]
    ax.semilogy(freqs, psd, color='#1e293b', linewidth=1.2)
    ax.set_title('Densidad Espectral de Potencia (Welch)', fontsize=11)
    ax.set_xlabel('Frecuencia (Hz)')
    ax.set_ylabel('PSD (μV²/Hz)')
    ax.set_xlim(0, 50)
    ax.grid(True, alpha=0.3)

    # Sombrear bandas
    for name, (low, high) in BANDS.items():
        ax.axvspan(low, high, alpha=0.15, color=BAND_COLORS[name], label=name)
    ax.legend(fontsize=8, loc='upper right')

    # --- Espectrograma ---
    ax2 = axes[1]
    f, t_spec, Sxx = signal.spectrogram(raw, fs=FS, nperseg=FS, noverlap=FS * 3 // 4)
    mask_f = f <= 50
    im = ax2.pcolormesh(t_spec, f[mask_f], 10 * np.log10(Sxx[mask_f] + 1e-10),
                        shading='gouraud', cmap='inferno')
    ax2.set_title('Espectrograma', fontsize=11)
    ax2.set_xlabel('Tiempo (s)')
    ax2.set_ylabel('Frecuencia (Hz)')
    plt.colorbar(im, ax=ax2, label='Potencia (dB)')

    plt.tight_layout()
    save(fig, 'python_analisis_espectral.png')


# ============================================================
# 4. DETECCIÓN DE NIVEL DE ATENCIÓN
# ============================================================

def plot_attention_detection():
    """Detecta nivel de atención basado en potencia Alpha vs Beta."""
    print("\n[4] Detección de nivel de atención")
    df = load_eeg()
    raw = df['Fp1'].values

    # Calcular potencia por banda en ventanas deslizantes
    alpha_power, t_alpha = compute_band_power(raw, 8, 12, FS, window_sec=0.5)
    beta_power, t_beta = compute_band_power(raw, 12, 30, FS, window_sec=0.5)

    # Ratio Beta/Alpha como indicador de atención
    # Alto ratio = más concentración, bajo ratio = más relajación
    attention_ratio = beta_power / (alpha_power + 1e-6)

    # Normalizar a 0-1
    attention_norm = (attention_ratio - attention_ratio.min()) / (attention_ratio.max() - attention_ratio.min() + 1e-6)

    # Umbral de atención
    threshold = 0.45

    fig, axes = plt.subplots(3, 1, figsize=(16, 10), sharex=True)
    fig.suptitle('Detección de Nivel de Atención — Ratio Beta/Alpha', fontsize=14, fontweight='bold')

    # Potencia Alpha
    axes[0].fill_between(t_alpha, alpha_power, alpha=0.3, color='#06b6d4')
    axes[0].plot(t_alpha, alpha_power, color='#06b6d4', linewidth=1.2)
    axes[0].set_ylabel('Potencia Alpha\n(μV²)', fontsize=10)
    axes[0].set_title('Potencia en Banda Alpha (8–12 Hz) — Indicador de Relajación', fontsize=11)
    axes[0].grid(True, alpha=0.2)

    # Potencia Beta
    axes[1].fill_between(t_beta, beta_power, alpha=0.3, color='#f97316')
    axes[1].plot(t_beta, beta_power, color='#f97316', linewidth=1.2)
    axes[1].set_ylabel('Potencia Beta\n(μV²)', fontsize=10)
    axes[1].set_title('Potencia en Banda Beta (12–30 Hz) — Indicador de Concentración', fontsize=11)
    axes[1].grid(True, alpha=0.2)

    # Nivel de atención
    colors = ['#ef4444' if v < threshold else '#22c55e' for v in attention_norm]
    axes[2].bar(t_alpha, attention_norm, width=0.25, color=colors, alpha=0.8)
    axes[2].axhline(threshold, color='#1e293b', linestyle='--', linewidth=1.5, label=f'Umbral = {threshold}')
    axes[2].set_ylabel('Nivel de\nAtención', fontsize=10)
    axes[2].set_title('Índice de Atención Normalizado (Beta/Alpha)', fontsize=11)
    axes[2].set_xlabel('Tiempo (s)')
    axes[2].set_ylim(0, 1.1)
    axes[2].legend(fontsize=10)
    axes[2].grid(True, alpha=0.2)

    # Etiquetas de estado
    axes[2].text(2.5, 0.15, 'RELAJADO', ha='center', fontsize=12, color='#ef4444', fontweight='bold')
    axes[2].text(7.5, 0.85, 'CONCENTRADO', ha='center', fontsize=12, color='#22c55e', fontweight='bold')

    plt.tight_layout()
    save(fig, 'python_deteccion_atencion.png')

    return t_alpha, attention_norm, threshold


# ============================================================
# 5. SIMULACIÓN DE CONTROL VISUAL BCI
# ============================================================

def plot_visual_control():
    """Simula control visual basado en la señal de atención."""
    print("\n[5] Simulación de control visual BCI")
    df = load_eeg()
    raw = df['Fp1'].values

    alpha_power, t_pw = compute_band_power(raw, 8, 12, FS, window_sec=0.5)
    beta_power, _ = compute_band_power(raw, 12, 30, FS, window_sec=0.5)
    ratio = beta_power / (alpha_power + 1e-6)
    attention = (ratio - ratio.min()) / (ratio.max() - ratio.min() + 1e-6)
    threshold = 0.45

    # --- Figura: Indicador de control tipo semáforo ---
    fig, axes = plt.subplots(2, 5, figsize=(20, 8))
    fig.suptitle('Simulación de Control Visual BCI — Cambio de Color por Nivel de Atención',
                 fontsize=14, fontweight='bold')

    # Seleccionar 5 momentos representativos
    sample_indices = np.linspace(5, len(attention) - 5, 5).astype(int)

    for col, idx in enumerate(sample_indices):
        time_val = t_pw[idx]
        att_val = attention[idx]
        is_focus = att_val >= threshold

        # Fila superior: señal en ese instante
        window = 2  # segundos alrededor
        t_all = df['time'].values
        sig_all = df['Fp1'].values
        mask = (t_all >= time_val - window) & (t_all <= time_val + window)

        axes[0, col].plot(t_all[mask], sig_all[mask], color='#475569', linewidth=0.5)
        axes[0, col].axvline(time_val, color='#ef4444' if not is_focus else '#22c55e',
                             linestyle='--', linewidth=1.5)
        axes[0, col].set_title(f't = {time_val:.1f}s', fontsize=10)
        axes[0, col].set_xlabel('Tiempo (s)', fontsize=8)
        if col == 0:
            axes[0, col].set_ylabel('EEG (μV)', fontsize=9)
        axes[0, col].grid(True, alpha=0.2)

        # Fila inferior: indicador visual
        ax = axes[1, col]
        ax.set_xlim(-1, 1)
        ax.set_ylim(-1, 1)
        ax.set_aspect('equal')
        ax.axis('off')

        # Fondo del indicador
        bg_color = '#dcfce7' if is_focus else '#fee2e2'
        bg = FancyBboxPatch((-0.9, -0.9), 1.8, 1.8, boxstyle="round,pad=0.1",
                            facecolor=bg_color, edgecolor='#94a3b8', linewidth=2)
        ax.add_patch(bg)

        # Círculo indicador
        circle_color = '#22c55e' if is_focus else '#ef4444'
        circ = Circle((0, 0.1), 0.45, facecolor=circle_color, edgecolor='#1e293b', linewidth=2)
        ax.add_patch(circ)

        # Texto
        state_text = 'FOCUS' if is_focus else 'RELAX'
        ax.text(0, -0.6, state_text, ha='center', fontsize=14, fontweight='bold',
                color=circle_color)
        ax.text(0, -0.82, f'Atención: {att_val:.2f}', ha='center', fontsize=9, color='#64748b')

    plt.tight_layout()
    save(fig, 'python_control_visual_color.png')


def generate_movement_gif():
    """Genera un GIF que simula el movimiento de un objeto controlado por BCI."""
    print("\n[6] GIF de control de movimiento BCI")
    df = load_eeg()
    raw = df['Fp1'].values

    alpha_power, t_pw = compute_band_power(raw, 8, 12, FS, window_sec=0.5)
    beta_power, _ = compute_band_power(raw, 12, 30, FS, window_sec=0.5)
    ratio = beta_power / (alpha_power + 1e-6)
    attention = (ratio - ratio.min()) / (ratio.max() - ratio.min() + 1e-6)
    threshold = 0.45

    # El objeto se mueve a la derecha cuando hay concentración
    position_x = 0.1  # posición inicial
    velocity = 0.0
    positions = []

    for att in attention:
        if att >= threshold:
            velocity = min(velocity + 0.008, 0.04)
        else:
            velocity = max(velocity - 0.005, 0.0)
        position_x = np.clip(position_x + velocity, 0.05, 0.95)
        positions.append(position_x)

    # Generar frames (submuestrear para GIF razonable)
    frames = []
    step = max(1, len(attention) // 50)

    for i in range(0, len(attention), step):
        fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 6),
                                              gridspec_kw={'height_ratios': [1, 1.5]})

        # Panel superior: señal de atención
        ax_top.plot(t_pw[:i + 1], attention[:i + 1], color='#1e293b', linewidth=1.5)
        ax_top.axhline(threshold, color='gray', linestyle='--', alpha=0.5)
        ax_top.fill_between(t_pw[:i + 1], attention[:i + 1], threshold,
                            where=attention[:i + 1] >= threshold,
                            color='#22c55e', alpha=0.3)
        ax_top.fill_between(t_pw[:i + 1], attention[:i + 1], threshold,
                            where=attention[:i + 1] < threshold,
                            color='#ef4444', alpha=0.3)
        ax_top.set_xlim(t_pw[0], t_pw[-1])
        ax_top.set_ylim(0, 1.1)
        ax_top.set_ylabel('Nivel de Atención')
        ax_top.set_title('Señal BCI — Control de Movimiento', fontsize=12, fontweight='bold')
        ax_top.grid(True, alpha=0.2)

        # Panel inferior: objeto en movimiento
        ax_bot.set_xlim(0, 1)
        ax_bot.set_ylim(0, 1)
        ax_bot.set_aspect('equal')

        # Pista
        ax_bot.add_patch(FancyBboxPatch((0.02, 0.35), 0.96, 0.3,
                         boxstyle="round,pad=0.02", facecolor='#f1f5f9', edgecolor='#94a3b8'))

        # Meta
        ax_bot.axvline(0.9, ymin=0.3, ymax=0.7, color='#22c55e', linewidth=4, alpha=0.6)
        ax_bot.text(0.92, 0.5, 'META', ha='left', va='center', fontsize=10,
                    color='#22c55e', fontweight='bold')

        # Objeto (círculo)
        att_val = attention[i]
        obj_color = '#22c55e' if att_val >= threshold else '#ef4444'
        circ = Circle((positions[i], 0.5), 0.06, facecolor=obj_color, edgecolor='#1e293b', linewidth=2)
        ax_bot.add_patch(circ)

        ax_bot.text(positions[i], 0.18, f'Pos: {positions[i]:.2f}', ha='center', fontsize=9, color='#64748b')
        ax_bot.axis('off')
        ax_bot.set_title(f't = {t_pw[i]:.1f}s | Atención: {att_val:.2f}', fontsize=10)

        plt.tight_layout()
        fig.canvas.draw()
        w, h = fig.canvas.get_width_height()
        buf = np.frombuffer(fig.canvas.tostring_argb(), dtype=np.uint8).reshape(h, w, 4)
        rgb = np.zeros((h, w, 3), dtype=np.uint8)
        rgb[..., 0] = buf[..., 1]
        rgb[..., 1] = buf[..., 2]
        rgb[..., 2] = buf[..., 3]
        frames.append(rgb)
        plt.close()

    gif_path = os.path.join(MEDIA_DIR, 'python_control_movimiento.gif')
    imageio.mimsave(gif_path, frames, duration=0.15, loop=0)
    print(f"  ✓ python_control_movimiento.gif ({len(frames)} frames)")


# ============================================================
# 6. DASHBOARD BCI
# ============================================================

def plot_bci_dashboard():
    """Genera un dashboard completo de monitoreo BCI."""
    print("\n[7] Dashboard BCI integrado")
    df = load_eeg()
    t = df['time'].values
    raw = df['Fp1'].values

    alpha_f = bandpass_filter(raw, 8, 12, FS)
    beta_f = bandpass_filter(raw, 12, 30, FS)

    alpha_power, t_pw = compute_band_power(raw, 8, 12, FS, window_sec=0.5)
    beta_power, _ = compute_band_power(raw, 12, 30, FS, window_sec=0.5)
    theta_power, _ = compute_band_power(raw, 4, 8, FS, window_sec=0.5)
    delta_power, _ = compute_band_power(raw, 0.5, 4, FS, window_sec=0.5)
    gamma_power, _ = compute_band_power(raw, 30, 50, FS, window_sec=0.5)

    ratio = beta_power / (alpha_power + 1e-6)
    attention = (ratio - ratio.min()) / (ratio.max() - ratio.min() + 1e-6)

    fig = plt.figure(figsize=(20, 12))
    fig.suptitle('Dashboard BCI — Monitoreo de Señales Cerebrales en Tiempo Real',
                 fontsize=16, fontweight='bold', y=0.98)

    gs = gridspec.GridSpec(3, 3, hspace=0.35, wspace=0.3)

    # 1. Señal cruda
    ax1 = fig.add_subplot(gs[0, :2])
    ax1.plot(t, raw, color='#475569', linewidth=0.3)
    ax1.set_title('Señal EEG Cruda — Fp1', fontsize=11, fontweight='bold')
    ax1.set_ylabel('μV')
    ax1.set_xlim(t[0], t[-1])
    ax1.grid(True, alpha=0.2)

    # 2. Distribución de potencia por banda (donut)
    ax2 = fig.add_subplot(gs[0, 2])
    avg_powers = [delta_power.mean(), theta_power.mean(), alpha_power.mean(),
                  beta_power.mean(), gamma_power.mean()]
    band_names = list(BANDS.keys())
    colors = [BAND_COLORS[n] for n in band_names]
    wedges, texts, autotexts = ax2.pie(avg_powers, labels=band_names, colors=colors,
                                        autopct='%1.1f%%', pctdistance=0.75,
                                        wedgeprops=dict(width=0.4))
    for t_text in autotexts:
        t_text.set_fontsize(8)
    ax2.set_title('Distribución de Potencia\npor Banda', fontsize=11, fontweight='bold')

    # 3. Bandas Alpha y Beta filtradas
    ax3 = fig.add_subplot(gs[1, :2])
    ax3.plot(t, alpha_f, color='#06b6d4', linewidth=0.5, alpha=0.7, label='Alpha (8-12 Hz)')
    ax3.plot(t, beta_f, color='#f97316', linewidth=0.5, alpha=0.7, label='Beta (12-30 Hz)')
    ax3.set_title('Señales Filtradas: Alpha vs Beta', fontsize=11, fontweight='bold')
    ax3.set_ylabel('μV')
    ax3.legend(fontsize=9)
    ax3.set_xlim(t[0], t[-1])
    ax3.grid(True, alpha=0.2)

    # 4. Espectrograma
    ax4 = fig.add_subplot(gs[1, 2])
    f, t_spec, Sxx = signal.spectrogram(raw, fs=FS, nperseg=FS, noverlap=FS * 3 // 4)
    mask_f = f <= 45
    ax4.pcolormesh(t_spec, f[mask_f], 10 * np.log10(Sxx[mask_f] + 1e-10),
                   shading='gouraud', cmap='inferno')
    ax4.set_title('Espectrograma', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Freq (Hz)')
    ax4.set_xlabel('Tiempo (s)')

    # 5. Nivel de atención
    ax5 = fig.add_subplot(gs[2, :2])
    colors_att = ['#22c55e' if v >= 0.45 else '#ef4444' for v in attention]
    ax5.bar(t_pw, attention, width=0.25, color=colors_att, alpha=0.8)
    ax5.axhline(0.45, color='#1e293b', linestyle='--', linewidth=1.5)
    ax5.set_title('Índice de Atención (Beta/Alpha) — Umbral: 0.45', fontsize=11, fontweight='bold')
    ax5.set_xlabel('Tiempo (s)')
    ax5.set_ylabel('Atención')
    ax5.set_ylim(0, 1.1)
    ax5.set_xlim(t_pw[0], t_pw[-1])
    ax5.grid(True, alpha=0.2)

    # 6. Resumen estadístico
    ax6 = fig.add_subplot(gs[2, 2])
    ax6.axis('off')
    focus_pct = np.mean(attention >= 0.45) * 100
    avg_att = np.mean(attention)
    max_att = np.max(attention)

    stats_text = (
        f"━━━ Resumen de Sesión ━━━\n\n"
        f"Duración:  30 segundos\n"
        f"Canal:  Fp1\n"
        f"Fs:  {FS} Hz\n\n"
        f"Atención promedio:  {avg_att:.3f}\n"
        f"Atención máxima:  {max_att:.3f}\n"
        f"Tiempo en Focus:  {focus_pct:.1f}%\n"
        f"Tiempo en Relax:  {100 - focus_pct:.1f}%\n\n"
        f"Alpha promedio:  {alpha_power.mean():.1f} μV²\n"
        f"Beta promedio:  {beta_power.mean():.1f} μV²\n"
    )
    ax6.text(0.1, 0.95, stats_text, transform=ax6.transAxes, fontsize=10,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8fafc', edgecolor='#cbd5e1'))

    save(fig, 'python_dashboard_bci.png')


# ============================================================
# 7. POTENCIA POR BANDA (BARRAS TEMPORALES)
# ============================================================

def plot_band_power_timeline():
    """Visualiza la potencia de todas las bandas a lo largo del tiempo."""
    print("\n[8] Timeline de potencia por banda")
    df = load_eeg()
    raw = df['Fp1'].values

    fig, ax = plt.subplots(figsize=(16, 5))
    fig.suptitle('Evolución Temporal de Potencia por Banda EEG', fontsize=14, fontweight='bold')

    for name, (low, high) in BANDS.items():
        power, t_pw = compute_band_power(raw, low, high, FS, window_sec=0.5)
        # Normalizar para comparar
        power_norm = power / power.max()
        ax.plot(t_pw, power_norm, color=BAND_COLORS[name], linewidth=1.5, label=f'{name} ({low}-{high} Hz)', alpha=0.8)

    ax.set_xlabel('Tiempo (s)')
    ax.set_ylabel('Potencia normalizada')
    ax.legend(loc='upper right', fontsize=9)
    ax.grid(True, alpha=0.2)
    ax.set_xlim(t_pw[0], t_pw[-1])

    # Sombrear estados
    states = df['state'].values
    t_all = df['time'].values
    in_focus = False
    start = 0
    for i in range(1, len(states)):
        if states[i] == 'focus' and not in_focus:
            start = t_all[i]
            in_focus = True
        elif states[i] != 'focus' and in_focus:
            ax.axvspan(start, t_all[i], alpha=0.06, color='#f97316')
            in_focus = False

    plt.tight_layout()
    save(fig, 'python_potencia_bandas.png')


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("=" * 60)
    print("Taller BCI Simulado: Control Visual con Señales EEG")
    print("=" * 60)

    # Generar datos si no existen
    csv_path = os.path.join(os.path.dirname(__file__), 'eeg_synthetic.csv')
    if not os.path.exists(csv_path):
        from generate_eeg import export_csv
        print("\nGenerando señales EEG sintéticas...")
        export_csv()

    plot_raw_signals()
    plot_filtered_signals()
    plot_spectral_analysis()
    plot_attention_detection()
    plot_visual_control()
    generate_movement_gif()
    plot_bci_dashboard()
    plot_band_power_timeline()

    print("\n" + "=" * 60)
    n_files = len([f for f in os.listdir(MEDIA_DIR) if f.startswith('python_')])
    print(f"✅ Todas las visualizaciones generadas en media/")
    print(f"   Total de archivos: {n_files}")
    print("=" * 60)
