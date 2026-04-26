"""
Generador de Señales EEG Sintéticas
====================================

Genera señales EEG multicanal con componentes realistas:
- Ondas Delta (0.5-4 Hz): sueño profundo
- Ondas Theta (4-8 Hz): somnolencia, meditación
- Ondas Alpha (8-12 Hz): relajación, ojos cerrados
- Ondas Beta (12-30 Hz): atención activa, concentración
- Ondas Gamma (30-100 Hz): procesamiento cognitivo alto
- Ruido rosa (1/f) característico del EEG real

Exporta los datos como CSV para su análisis posterior.
"""

import numpy as np
import pandas as pd
import os

OUTPUT_DIR = os.path.dirname(__file__)


def pink_noise(n_samples, seed=None):
    """Genera ruido rosa (1/f) mediante filtrado espectral."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n_samples)
    fft = np.fft.rfft(white)
    freqs = np.fft.rfftfreq(n_samples)
    freqs[0] = 1  # evitar división por cero
    fft *= 1.0 / np.sqrt(freqs)
    return np.fft.irfft(fft, n=n_samples)


def generate_eeg_signal(duration=30, fs=256, seed=42):
    """
    Genera una señal EEG sintética de un solo canal con estados
    alternantes de relajación (Alpha alto) y concentración (Beta alto).

    Args:
        duration: duración en segundos
        fs: frecuencia de muestreo (Hz)
        seed: semilla para reproducibilidad

    Returns:
        t: vector de tiempo
        signal: señal EEG compuesta
        states: array con el estado en cada muestra ('relax' o 'focus')
    """
    rng = np.random.default_rng(seed)
    n_samples = int(duration * fs)
    t = np.arange(n_samples) / fs

    # Componentes base de frecuencia
    delta = 20 * np.sin(2 * np.pi * 2 * t + rng.uniform(0, 2 * np.pi))
    theta = 10 * np.sin(2 * np.pi * 6 * t + rng.uniform(0, 2 * np.pi))
    alpha = 15 * np.sin(2 * np.pi * 10 * t + rng.uniform(0, 2 * np.pi))
    beta = 8 * np.sin(2 * np.pi * 20 * t + rng.uniform(0, 2 * np.pi))
    gamma = 3 * np.sin(2 * np.pi * 40 * t + rng.uniform(0, 2 * np.pi))

    # Modular amplitudes según estado mental simulado
    # Alternar entre relajación (Alpha dominante) y concentración (Beta dominante)
    states = np.array(['relax'] * n_samples)
    alpha_mod = np.ones(n_samples)
    beta_mod = np.ones(n_samples)

    # Crear bloques de ~5 segundos con transiciones suaves
    block_duration = 5  # segundos
    n_blocks = int(duration / block_duration)

    for i in range(n_blocks):
        start = int(i * block_duration * fs)
        end = min(int((i + 1) * block_duration * fs), n_samples)
        block_samples = end - start

        if i % 2 == 0:
            # Estado de relajación: Alpha alto, Beta bajo
            alpha_mod[start:end] = 2.5 + 0.5 * np.sin(2 * np.pi * 0.3 * np.arange(block_samples) / fs)
            beta_mod[start:end] = 0.5
            states[start:end] = 'relax'
        else:
            # Estado de concentración: Beta alto, Alpha bajo
            alpha_mod[start:end] = 0.4
            beta_mod[start:end] = 2.8 + 0.3 * np.sin(2 * np.pi * 0.5 * np.arange(block_samples) / fs)
            states[start:end] = 'focus'

    # Transiciones suaves entre bloques (200ms)
    transition_samples = int(0.2 * fs)
    for i in range(1, n_blocks):
        center = int(i * block_duration * fs)
        start = max(center - transition_samples, 0)
        end = min(center + transition_samples, n_samples)
        ramp = np.linspace(0, 1, end - start)
        # Suavizar las modulaciones
        alpha_mod[start:end] = alpha_mod[start] * (1 - ramp) + alpha_mod[end - 1] * ramp
        beta_mod[start:end] = beta_mod[start] * (1 - ramp) + beta_mod[end - 1] * ramp

    # Señal compuesta
    signal = (delta +
              theta +
              alpha * alpha_mod +
              beta * beta_mod +
              gamma +
              5 * pink_noise(n_samples, seed=seed) +
              3 * rng.standard_normal(n_samples))

    # Simular artefactos ocasionales (parpadeo, movimiento)
    n_artifacts = rng.integers(3, 8)
    for _ in range(n_artifacts):
        pos = rng.integers(0, n_samples - fs // 2)
        artifact_len = rng.integers(fs // 10, fs // 3)
        artifact = rng.uniform(80, 150) * np.exp(-np.arange(artifact_len) / (artifact_len / 4))
        if rng.random() > 0.5:
            artifact = -artifact
        signal[pos:pos + artifact_len] += artifact[:min(artifact_len, n_samples - pos)]

    return t, signal, states


def generate_multichannel_eeg(duration=30, fs=256, n_channels=4, seed=42):
    """
    Genera señales EEG multicanal con correlación espacial realista.

    Args:
        n_channels: número de canales (electrodos simulados)

    Returns:
        DataFrame con columnas: time, Fp1, Fp2, C3, C4, state
    """
    channel_names = ['Fp1', 'Fp2', 'C3', 'C4', 'O1', 'O2', 'T3', 'T4'][:n_channels]

    t, base_signal, states = generate_eeg_signal(duration, fs, seed)

    data = {'time': t, 'state': states}

    for i, name in enumerate(channel_names):
        # Cada canal es una variante del base con ruido adicional
        rng = np.random.default_rng(seed + i + 1)
        phase_shift = rng.uniform(-0.5, 0.5)
        amplitude_scale = rng.uniform(0.7, 1.3)
        channel_noise = 5 * rng.standard_normal(len(t))

        # Desfase temporal sutil
        shift_samples = int(phase_shift * fs / 100)
        shifted = np.roll(base_signal, shift_samples)

        data[name] = shifted * amplitude_scale + channel_noise

    df = pd.DataFrame(data)
    return df


def export_csv(duration=30, fs=256, n_channels=4, seed=42):
    """Genera y exporta señales EEG como CSV."""
    df = generate_multichannel_eeg(duration, fs, n_channels, seed)
    output_path = os.path.join(OUTPUT_DIR, 'eeg_synthetic.csv')
    df.to_csv(output_path, index=False)
    print(f"  ✓ EEG sintético exportado: {output_path}")
    print(f"    Duración: {duration}s, Fs: {fs}Hz, Canales: {n_channels}")
    print(f"    Muestras totales: {len(df)}")
    return df


if __name__ == '__main__':
    df = export_csv()
    print(f"\nColumnas: {list(df.columns)}")
    print(f"Primeras filas:\n{df.head()}")
