import numpy as np
import pandas as pd
import os

def generate_1d_data(n_steps=100, x_start=0.0, q_std=0.5, r_std=2.0, seed=42):
    """
    Genera una trayectoria 1D mediante un caminar aleatorio y mediciones ruidosas.
    """
    np.random.seed(seed)
    
    real = np.zeros(n_steps)
    observed = np.zeros(n_steps)
    
    current_pos = x_start
    for t in range(n_steps):
        # Ruido de proceso (caminar aleatorio)
        process_noise = np.random.normal(0, q_std)
        if t > 0:
            current_pos = real[t-1] + process_noise
        else:
            current_pos = x_start + process_noise
            
        real[t] = current_pos
        
        # Ruido de medición
        measurement_noise = np.random.normal(0, r_std)
        observed[t] = current_pos + measurement_noise
        
    df = pd.DataFrame({
        'step': np.arange(n_steps),
        'real_x': real,
        'observed_x': observed
    })
    return df

def generate_2d_data(n_steps=100, dt=0.5, x_start=0.0, y_start=0.0, 
                     vx_start=2.0, vy_start=1.5, sigma_a=0.2, sigma_z=3.0, seed=42):
    """
    Genera una trayectoria 2D basada en cinemática con velocidad constante
    y perturbaciones de aceleración aleatorias, junto con mediciones de posición ruidosas.
    """
    np.random.seed(seed)
    
    real_x = np.zeros(n_steps)
    real_y = np.zeros(n_steps)
    real_vx = np.zeros(n_steps)
    real_vy = np.zeros(n_steps)
    
    observed_x = np.zeros(n_steps)
    observed_y = np.zeros(n_steps)
    
    # Inicialización del estado
    x = x_start
    y = y_start
    vx = vx_start
    vy = vy_start
    
    for t in range(n_steps):
        # Guardar estado real actual
        real_x[t] = x
        real_y[t] = y
        real_vx[t] = vx
        real_vy[t] = vy
        
        # Mediciones observadas con ruido gaussiano
        observed_x[t] = x + np.random.normal(0, sigma_z)
        observed_y[t] = y + np.random.normal(0, sigma_z)
        
        # Transición de estado para el siguiente paso
        ax = np.random.normal(0, sigma_a)
        ay = np.random.normal(0, sigma_a)
        
        # Ecuaciones de movimiento con aceleración aleatoria (ruido de proceso)
        x = x + vx * dt + 0.5 * ax * (dt**2)
        y = y + vy * dt + 0.5 * ay * (dt**2)
        vx = vx + ax * dt
        vy = vy + ay * dt
        
    df = pd.DataFrame({
        'step': np.arange(n_steps),
        'real_x': real_x,
        'real_y': real_y,
        'real_vx': real_vx,
        'real_vy': real_vy,
        'observed_x': observed_x,
        'observed_y': observed_y
    })
    return df

if __name__ == "__main__":
    # Carpeta de salida
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Generar y guardar datos 1D
    df_1d = generate_1d_data(n_steps=100, q_std=0.5, r_std=2.0, seed=42)
    path_1d = os.path.join(output_dir, 'datos_1d.csv')
    df_1d.to_csv(path_1d, index=False)
    print(f"Datos 1D guardados en: {path_1d}")
    
    # Generar y guardar datos 2D
    df_2d = generate_2d_data(n_steps=100, dt=0.5, sigma_a=0.3, sigma_z=2.5, seed=42)
    path_2d = os.path.join(output_dir, 'datos_2d.csv')
    df_2d.to_csv(path_2d, index=False)
    print(f"Datos 2D guardados en: {path_2d}")
