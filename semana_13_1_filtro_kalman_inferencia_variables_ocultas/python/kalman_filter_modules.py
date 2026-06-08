import numpy as np

class KalmanFilter1D:
    """
    Filtro de Kalman Unidimensional (1D).
    Diseñado para estimar una variable de estado escalar (e.g., posición)
    a partir de observaciones ruidosas.
    """
    def __init__(self, x_init=0.0, P_init=1.0, Q=0.001, R=4.0):
        """
        Inicializa el filtro de Kalman 1D.
        
        Parámetros:
        -----------
        x_init : float
            Estimación inicial de la posición (estado x_hat).
        P_init : float
            Covarianza inicial del error.
        Q : float
            Varianza del ruido del proceso (incertidumbre en la transición de estado).
        R : float
            Varianza del ruido de medición (incertidumbre del sensor).
        """
        self.x_hat = x_init
        self.P = P_init
        self.Q = Q
        self.R = R
        
        # Historial para análisis posterior
        self.x_hat_prior = x_init
        self.P_prior = P_init
        self.K = 0.0

    def predict(self):
        """
        Fase de Predicción:
        Proyecta el estado y la covarianza del error al siguiente paso.
        Para un modelo 1D estático/caminar aleatorio sin entrada de control (u = 0):
        x_hat_k^- = x_hat_{k-1}
        P_k^- = P_{k-1} + Q
        """
        self.x_hat_prior = self.x_hat
        self.P_prior = self.P + self.Q
        return self.x_hat_prior, self.P_prior

    def update(self, z):
        """
        Fase de Corrección/Actualización:
        Refina la estimación utilizando la nueva medición observada z.
        
        Parámetros:
        -----------
        z : float
            Medición observada ruidosa.
        """
        # Calcular Ganancia de Kalman
        self.K = self.P_prior / (self.P_prior + self.R)
        
        # Actualizar estado estimado con la medición
        self.x_hat = self.x_hat_prior + self.K * (z - self.x_hat_prior)
        
        # Actualizar covarianza del error
        self.P = (1.0 - self.K) * self.P_prior
        
        return self.x_hat, self.P, self.K


class KalmanFilter2D:
    """
    Filtro de Kalman Bidimensional (2D).
    Modelo de velocidad constante para el seguimiento de la posición [x, y]
    e inferencia de las velocidades [v_x, v_y] (variables ocultas).
    """
    def __init__(self, x_init=0.0, y_init=0.0, vx_init=0.0, vy_init=0.0, 
                 P_diag=[1.0, 1.0, 10.0, 10.0], dt=1.0, sigma_a=0.1, sigma_z=2.0):
        """
        Inicializa el filtro de Kalman 2D.
        
        Parámetros:
        -----------
        x_init, y_init : float
            Posición inicial estimada.
        vx_init, vy_init : float
            Velocidad inicial estimada.
        P_diag : list o np.ndarray
            Diagonal inicial de la matriz de covarianza de error P (tamaño 4).
        dt : float
            Intervalo de tiempo entre pasos.
        sigma_a : float
            Desviación estándar de la aceleración aleatoria (ruido del proceso).
        sigma_z : float
            Desviación estándar del error del sensor de posición (ruido de medición).
        """
        self.dt = dt
        
        # Estado inicial [x, y, v_x, v_y]^T (4x1)
        self.x = np.array([[x_init], 
                           [y_init], 
                           [vx_init], 
                           [vy_init]], dtype=float)
        
        # Matriz de covarianza del estado P (4x4)
        self.P = np.diag(P_diag).astype(float)
        
        # Matriz de transición de estado F (4x4)
        # x_k = x_{k-1} + vx_{k-1}*dt
        # y_k = y_{k-1} + vy_{k-1}*dt
        # vx_k = vx_{k-1}
        # vy_k = vy_{k-1}
        self.F = np.array([[1.0, 0.0, dt,  0.0],
                           [0.0, 1.0, 0.0, dt ],
                           [0.0, 0.0, 1.0, 0.0],
                           [0.0, 0.0, 0.0, 1.0]], dtype=float)
        
        # Matriz de medición H (2x4) - Solo observamos posición x e y
        self.H = np.array([[1.0, 0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0, 0.0]], dtype=float)
        
        # Matriz de ruido del proceso Q (4x4)
        # Derivada del modelo de ruido de aceleración aleatoria continua (Discrete White Noise Acceleration)
        # G = [0.5*dt^2, 0, dt, 0; 0, 0.5*dt^2, 0, dt]^T
        # Q = G * G^T * sigma_a^2
        dt2 = dt**2
        dt3 = dt**3
        dt4 = dt**4
        self.Q = np.array([[dt4/4.0,   0.0,   dt3/2.0,   0.0],
                           [0.0,     dt4/4.0,   0.0,   dt3/2.0],
                           [dt3/2.0,   0.0,    dt2,      0.0],
                           [0.0,     dt3/2.0,   0.0,     dt2]], dtype=float) * (sigma_a**2)
        
        # Matriz de covarianza de medición R (2x2)
        self.R = np.eye(2, dtype=float) * (sigma_z**2)
        
        # Identidad para actualización de covarianza
        self.I = np.eye(4, dtype=float)
        
        # Variables previas
        self.x_prior = np.copy(self.x)
        self.P_prior = np.copy(self.P)
        self.K = np.zeros((4, 2))

    def predict(self):
        """
        Fase de Predicción:
        Proyecta el estado y la covarianza hacia adelante en el tiempo.
        x_prior = F * x
        P_prior = F * P * F^T + Q
        """
        self.x_prior = np.dot(self.F, self.x)
        self.P_prior = np.dot(np.dot(self.F, self.P), self.F.T) + self.Q
        return self.x_prior, self.P_prior

    def update(self, z):
        """
        Fase de Corrección/Actualización:
        Corrige la predicción usando la observación bidimensional z = [z_x, z_y]^T.
        
        Parámetros:
        -----------
        z : np.ndarray o list
            Medición de posición [x, y] (vector 2x1 o convertible).
        """
        z = np.array(z, dtype=float).reshape(2, 1)
        
        # Innovación de medición (residual)
        y = z - np.dot(self.H, self.x_prior)
        
        # Covarianza de la innovación S
        S = np.dot(np.dot(self.H, self.P_prior), self.H.T) + self.R
        
        # Ganancia de Kalman K
        self.K = np.dot(np.dot(self.P_prior, self.H.T), np.linalg.inv(S))
        
        # Actualización del estado
        self.x = self.x_prior + np.dot(self.K, y)
        
        # Actualización de la covarianza de error (Ecuación de Joseph o estándar)
        # Usamos la versión estándar: P = (I - K*H) * P_prior
        self.P = np.dot((self.I - np.dot(self.K, self.H)), self.P_prior)
        
        return self.x, self.P, self.K
