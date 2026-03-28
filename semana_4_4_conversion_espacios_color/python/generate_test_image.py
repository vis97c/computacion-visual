"""
Genera una imagen de prueba sintética con regiones de color distintas
para utilizar en las demostraciones del taller.
"""

import numpy as np
import cv2
import os

OUTPUT = os.path.join(os.path.dirname(__file__), 'test_image.png')


def generate_test_image(width=640, height=480):
    """
    Crea una imagen con cielo, pasto, flores rojas, flores amarillas,
    un sol y montañas para tener variedad cromática.
    """
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # Cielo: gradiente azul
    for y in range(height // 2):
        t = y / (height // 2)
        b = int(220 - 60 * t)
        g = int(180 - 80 * t)
        r = int(120 - 70 * t)
        img[y, :] = [b, g, r]  # BGR

    # Sol (amarillo)
    cv2.circle(img, (520, 60), 45, (50, 220, 255), -1)
    cv2.circle(img, (520, 60), 50, (80, 240, 255), 3)

    # Montañas (verde oscuro / marrón)
    pts_mountain1 = np.array([[0, 240], [120, 140], [250, 240]], np.int32)
    pts_mountain2 = np.array([[180, 240], [350, 110], [500, 240]], np.int32)
    pts_mountain3 = np.array([[400, 240], [560, 150], [640, 240]], np.int32)
    cv2.fillPoly(img, [pts_mountain1], (45, 80, 55))
    cv2.fillPoly(img, [pts_mountain2], (50, 90, 60))
    cv2.fillPoly(img, [pts_mountain3], (40, 75, 50))

    # Pasto: gradiente verde
    for y in range(height // 2, height):
        t = (y - height // 2) / (height // 2)
        b = int(30 + 20 * t)
        g = int(160 - 50 * t)
        r = int(40 + 30 * t)
        img[y, :] = [b, g, r]

    # Flores rojas (círculos pequeños)
    np.random.seed(42)
    for _ in range(35):
        cx = np.random.randint(20, width - 20)
        cy = np.random.randint(height // 2 + 30, height - 20)
        radius = np.random.randint(5, 12)
        r_val = np.random.randint(180, 255)
        cv2.circle(img, (cx, cy), radius, (30, 30, r_val), -1)

    # Flores amarillas
    for _ in range(20):
        cx = np.random.randint(20, width - 20)
        cy = np.random.randint(height // 2 + 40, height - 15)
        radius = np.random.randint(4, 9)
        cv2.circle(img, (cx, cy), radius, (40, 220, 250), -1)

    # Flores azules/violeta
    for _ in range(15):
        cx = np.random.randint(20, width - 20)
        cy = np.random.randint(height // 2 + 50, height - 10)
        radius = np.random.randint(4, 8)
        cv2.circle(img, (cx, cy), radius, (200, 60, 140), -1)

    # Nubes (blancas semitransparentes)
    overlay = img.copy()
    cv2.ellipse(overlay, (150, 55), (70, 25), 0, 0, 360, (240, 235, 230), -1)
    cv2.ellipse(overlay, (190, 45), (50, 20), 0, 0, 360, (245, 240, 235), -1)
    cv2.ellipse(overlay, (380, 75), (60, 22), 0, 0, 360, (238, 232, 228), -1)
    cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

    # Suavizar ligeramente
    img = cv2.GaussianBlur(img, (3, 3), 0.5)

    return img


if __name__ == '__main__':
    img = generate_test_image()
    cv2.imwrite(OUTPUT, img)
    print(f"Imagen de prueba guardada en: {OUTPUT}")
    print(f"Dimensiones: {img.shape[1]}x{img.shape[0]}, Canales: {img.shape[2]}")
