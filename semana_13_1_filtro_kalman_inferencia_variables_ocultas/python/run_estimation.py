import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from kalman_filter_modules import KalmanFilter1D, KalmanFilter2D

def compute_metrics(real, predicted):
    """
    Calcula el Error Cuadrático Medio (MSE) y la Raíz del Error Cuadrático Medio (RMSE).
    """
    mse = np.mean((real - predicted) ** 2)
    rmse = np.sqrt(mse)
    return mse, rmse

def run_1d_estimation(data_path, media_dir):
    """
    Ejecuta el filtro de Kalman 1D, calcula métricas de error y guarda los gráficos.
    """
    # Leer datos
    df = pd.read_csv(data_path)
    observed = df['observed_x'].values
    real = df['real_x'].values
    
    # Parámetros del filtro óptimo
    Q_optimal = 0.25
    R_optimal = 4.0
    
    # 1. Ejecución óptima
    kf = KalmanFilter1D(x_init=observed[0], P_init=1.0, Q=Q_optimal, R=R_optimal)
    estimates = []
    covariances = []
    gains = []
    
    for z in observed:
        kf.predict()
        x_hat, P, K = kf.update(z)
        estimates.append(x_hat)
        covariances.append(P)
        gains.append(K)
        
    estimates = np.array(estimates)
    
    # Calcular métricas de error
    mse_obs, rmse_obs = compute_metrics(real, observed)
    mse_est, rmse_est = compute_metrics(real, estimates)
    improvement = (rmse_obs - rmse_est) / rmse_obs * 100
    
    print("=== METRICAS CASO 1D ===")
    print(f"Observación vs Real: MSE = {mse_obs:.4f}, RMSE = {rmse_obs:.4f}")
    print(f"Estimación Kalman vs Real: MSE = {mse_est:.4f}, RMSE = {rmse_est:.4f}")
    print(f"Reducción del error (RMSE): {improvement:.2f}%")
    print("========================\n")
    
    df['estimated_x'] = estimates
    df['p_variance'] = covariances
    df['kalman_gain'] = gains
    df.to_csv(data_path, index=False)
    
    # Configurar estilo de gráficos
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    # Gráfico 1: Posición Real vs Medida vs Estimada
    plt.figure(figsize=(12, 6))
    plt.plot(df['step'], real, label='Posición Real (Variable Oculta)', color='#2c3e50', linestyle='--', linewidth=2.0)
    plt.scatter(df['step'], observed, label='Mediciones Ruidosas (Sensor)', color='#e74c3c', alpha=0.5, s=20)
    plt.plot(df['step'], estimates, label='Estimación Filtro de Kalman (Óptimo)', color='#2ecc71', linewidth=2.5)
    
    plt.title('Filtro de Kalman 1D - Inferencia de Posición Oculta', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Paso de Tiempo (k)', fontsize=12)
    plt.ylabel('Posición (x)', fontsize=12)
    
    info_text = (f"Parámetros óptimos:\n"
                 f"  Q = {Q_optimal}\n"
                 f"  R = {R_optimal}\n\n"
                 f"RMSE:\n"
                 f"  Sensor: {rmse_obs:.3f}\n"
                 f"  Kalman: {rmse_est:.3f}\n"
                 f"  Mejora: {improvement:.1f}%")
    
    props = dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#bdc3c7', alpha=0.9)
    plt.text(0.02, 0.05, info_text, transform=plt.gca().transAxes, fontsize=10, bbox=props)
    plt.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#bdc3c7')
    plt.tight_layout()
    
    fig1_path = os.path.join(media_dir, 'grafico_resultado_1d.png')
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"Gráfico 1D principal guardado en: {fig1_path}")
    
    # Gráfico 2: Experimento de Sensibilidad Q/R
    # Caso A: Q muy pequeño (alta inercia / confía en predicción)
    kf_smooth = KalmanFilter1D(x_init=observed[0], Q=0.001, R=4.0)
    # Caso B: Q muy grande (confía en medición / sigue el ruido)
    kf_noisy = KalmanFilter1D(x_init=observed[0], Q=2.0, R=4.0)
    
    est_smooth = []
    est_noisy = []
    
    for z in observed:
        kf_smooth.predict()
        xs, _, _ = kf_smooth.update(z)
        est_smooth.append(xs)
        
        kf_noisy.predict()
        xn, _, _ = kf_noisy.update(z)
        est_noisy.append(xn)
        
    plt.figure(figsize=(12, 6))
    plt.plot(df['step'], real, 'k--', label='Posición Real (Oculta)', alpha=0.6, linewidth=1.5)
    plt.scatter(df['step'], observed, color='#e74c3c', alpha=0.15, s=15, label='Mediciones (Sensor)')
    plt.plot(df['step'], est_smooth, color='#9b59b6', label='Q = 0.001 (Confía en predicción - Lento)', linewidth=2.0)
    plt.plot(df['step'], estimates, color='#2ecc71', label='Q = 0.25 (Óptimo Tuned)', linewidth=2.0)
    plt.plot(df['step'], est_noisy, color='#f1c40f', label='Q = 2.0 (Confía en medición - Ruidoso)', linewidth=1.5)
    
    plt.title('Análisis de Sensibilidad 1D - Efecto de la Relación Q/R', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Paso de Tiempo (k)', fontsize=12)
    plt.ylabel('Posición (x)', fontsize=12)
    plt.legend(loc='upper left', frameon=True, facecolor='white', edgecolor='#bdc3c7')
    plt.tight_layout()
    
    fig2_path = os.path.join(media_dir, 'grafico_sensibilidad_1d.png')
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"Gráfico de sensibilidad 1D guardado en: {fig2_path}")

def run_2d_estimation(data_path, media_dir):
    """
    Ejecuta el filtro de Kalman 2D, calcula métricas de error y guarda los gráficos.
    """
    # Leer datos
    df = pd.read_csv(data_path)
    real_x = df['real_x'].values
    real_y = df['real_y'].values
    real_vx = df['real_vx'].values
    real_vy = df['real_vy'].values
    observed_x = df['observed_x'].values
    observed_y = df['observed_y'].values
    
    dt = 0.5
    sigma_a = 0.3
    sigma_z = 2.5
    
    # Inicializar filtro 2D
    kf = KalmanFilter2D(
        x_init=observed_x[0],
        y_init=observed_y[0],
        vx_init=2.0,
        vy_init=1.5,
        P_diag=[10.0, 10.0, 10.0, 10.0],
        dt=dt,
        sigma_a=sigma_a,
        sigma_z=sigma_z
    )
    
    est_x, est_y, est_vx, est_vy = [], [], [], []
    
    for ox, oy in zip(observed_x, observed_y):
        kf.predict()
        z = [ox, oy]
        x_state, _, _ = kf.update(z)
        
        est_x.append(x_state[0, 0])
        est_y.append(x_state[1, 0])
        est_vx.append(x_state[2, 0])
        est_vy.append(x_state[3, 0])
        
    est_x = np.array(est_x)
    est_y = np.array(est_y)
    est_vx = np.array(est_vx)
    est_vy = np.array(est_vy)
    
    # Calcular métricas de error
    errors_obs = np.sqrt((real_x - observed_x)**2 + (real_y - observed_y)**2)
    errors_est = np.sqrt((real_x - est_x)**2 + (real_y - est_y)**2)
    rmse_obs = np.sqrt(np.mean(errors_obs**2))
    rmse_est = np.sqrt(np.mean(errors_est**2))
    improvement = (rmse_obs - rmse_est) / rmse_obs * 100
    
    rmse_vx = np.sqrt(np.mean((real_vx - est_vx)**2))
    rmse_vy = np.sqrt(np.mean((real_vy - est_vy)**2))
    
    print("=== METRICAS CASO 2D (Trayectoria) ===")
    print(f"Observación de Posición vs Real: RMSE = {rmse_obs:.4f}")
    print(f"Estimación Kalman de Posición vs Real: RMSE = {rmse_est:.4f}")
    print(f"Reducción del error de posición (RMSE): {improvement:.2f}%")
    print(f"Estimación Velocidad Vx vs Real: RMSE = {rmse_vx:.4f}")
    print(f"Estimación Velocidad Vy vs Real: RMSE = {rmse_vy:.4f}")
    print("======================================\n")
    
    df['estimated_x'] = est_x
    df['estimated_y'] = est_y
    df['estimated_vx'] = est_vx
    df['estimated_vy'] = est_vy
    df.to_csv(data_path, index=False)
    
    # Gráfico 1: Trayectoria 2D (Plano X-Y)
    plt.figure(figsize=(10, 8))
    plt.plot(real_x, real_y, label='Trayectoria Real (Oculta)', color='#34495e', linestyle='--', linewidth=2.0)
    plt.scatter(observed_x, observed_y, label='Mediciones de Posición (Sensor)', color='#e74c3c', alpha=0.4, s=25)
    plt.plot(est_x, est_y, label='Trayectoria Estimada (Kalman)', color='#3498db', linewidth=2.5)
    
    plt.scatter(real_x[0], real_y[0], color='black', s=80, zorder=5, label='Inicio')
    plt.scatter(real_x[-1], real_y[-1], color='purple', marker='X', s=100, zorder=5, label='Fin')
    
    plt.title('Filtro de Kalman 2D - Seguimiento de Posición en Plano X-Y', fontsize=14, fontweight='bold', pad=15)
    plt.xlabel('Posición X', fontsize=12)
    plt.ylabel('Posición Y', fontsize=12)
    
    info_text = (f"Parámetros:\n"
                 f"  dt = {dt}s\n"
                 f"  sigma_a = {sigma_a}\n"
                 f"  sigma_z = {sigma_z}\n\n"
                 f"RMSE Posición 2D:\n"
                 f"  Sensor: {rmse_obs:.3f}\n"
                 f"  Kalman: {rmse_est:.3f}\n"
                 f"  Mejora: {improvement:.1f}%")
    
    props = dict(boxstyle='round,pad=0.5', facecolor='#f8f9fa', edgecolor='#bdc3c7', alpha=0.9)
    plt.text(0.02, 0.98, info_text, transform=plt.gca().transAxes, fontsize=10,
             verticalalignment='top', bbox=props)
    plt.legend(loc='lower right', frameon=True, facecolor='white', edgecolor='#bdc3c7')
    plt.axis('equal')
    plt.tight_layout()
    
    fig1_path = os.path.join(media_dir, 'grafico_resultado_2d.png')
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"Gráfico de trayectoria 2D guardado en: {fig1_path}")
    
    # Gráfico 2: Inferencia de Velocidades Ocultas (Vx y Vy vs tiempo)
    plt.figure(figsize=(14, 6))
    
    # Vx
    plt.subplot(1, 2, 1)
    plt.plot(df['step'], real_vx, label='Velocidad Vx Real', color='#2c3e50', linestyle='--', linewidth=2.0)
    plt.plot(df['step'], est_vx, label='Vx Estimada por Kalman', color='#e67e22', linewidth=2.5)
    plt.title('Inferencia de Velocidad Oculta Vx', fontsize=12, fontweight='bold')
    plt.xlabel('Paso de Tiempo (k)', fontsize=11)
    plt.ylabel('Velocidad Vx (u/s)', fontsize=11)
    plt.legend(loc='upper right', frameon=True, facecolor='white')
    
    # Vy
    plt.subplot(1, 2, 2)
    plt.plot(df['step'], real_vy, label='Velocidad Vy Real', color='#2c3e50', linestyle='--', linewidth=2.0)
    plt.plot(df['step'], est_vy, label='Vy Estimada por Kalman', color='#9b59b6', linewidth=2.5)
    plt.title('Inferencia de Velocidad Oculta Vy', fontsize=12, fontweight='bold')
    plt.xlabel('Paso de Tiempo (k)', fontsize=11)
    plt.ylabel('Velocidad Vy (u/s)', fontsize=11)
    plt.legend(loc='upper right', frameon=True, facecolor='white')
    
    plt.suptitle('Estimación de Variables Ocultas (Velocidades) por Kalman 2D', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    fig2_path = os.path.join(media_dir, 'grafico_velocidades_2d.png')
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"Gráfico de velocidades inferidas 2D guardado en: {fig2_path}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    
    media_dir = os.path.join(project_root, 'media')
    os.makedirs(media_dir, exist_ok=True)
    
    data_1d_path = os.path.join(current_dir, 'datos_1d.csv')
    data_2d_path = os.path.join(current_dir, 'datos_2d.csv')
    
    run_1d_estimation(data_1d_path, media_dir)
    run_2d_estimation(data_2d_path, media_dir)
