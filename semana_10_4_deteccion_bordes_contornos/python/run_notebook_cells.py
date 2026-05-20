import cv2
import numpy as np
import matplotlib.pyplot as plt
from skimage import filters
import os

media_dir = os.path.join("..", "media")
natural_path = os.path.join(media_dir, "natural.png")
shapes_path = os.path.join(media_dir, "shapes.png")

print("Notebook Runner: Executing Step 1 (Edge Operators)...")
img_natural = cv2.imread(natural_path, cv2.IMREAD_GRAYSCALE)
sobelx = cv2.Sobel(img_natural, cv2.CV_64F, 1, 0, ksize=3)
sobely = cv2.Sobel(img_natural, cv2.CV_64F, 0, 1, ksize=3)
sobel_mag = np.sqrt(sobelx**2 + sobely**2)
scharrx = cv2.Scharr(img_natural, cv2.CV_64F, 1, 0)
scharry = cv2.Scharr(img_natural, cv2.CV_64F, 0, 1)
scharr_mag = np.sqrt(scharrx**2 + scharry**2)
img_normalized = img_natural.astype(np.float64) / 255.0
prewitt_mag = filters.prewitt(img_normalized)
laplacian = cv2.Laplacian(img_natural, cv2.CV_64F)

plt.figure(figsize=(15, 10))
plt.subplot(2, 3, 1); plt.imshow(img_natural, cmap='gray'); plt.title('Original (Gris)'); plt.axis('off')
plt.subplot(2, 3, 2); plt.imshow(np.abs(sobel_mag), cmap='gray'); plt.title('Sobel Magnitud'); plt.axis('off')
plt.subplot(2, 3, 3); plt.imshow(np.abs(prewitt_mag), cmap='gray'); plt.title('Prewitt Magnitud'); plt.axis('off')
plt.subplot(2, 3, 4); plt.imshow(np.abs(laplacian), cmap='gray'); plt.title('Laplaciano (2do Orden)'); plt.axis('off')
plt.subplot(2, 3, 5); plt.imshow(np.abs(scharr_mag), cmap='gray'); plt.title('Scharr Magnitud'); plt.axis('off')
plt.tight_layout()
plt.savefig(os.path.join(media_dir, "1_sobel_prewitt_laplacian_scharr.png"), dpi=150)
plt.close()

print("Notebook Runner: Executing Step 2 (Canny Thresholds)...")
canny_low = cv2.Canny(img_natural, 30, 80)
canny_mid = cv2.Canny(img_natural, 80, 150)
canny_high = cv2.Canny(img_natural, 150, 220)
blur_s1 = cv2.GaussianBlur(img_natural, (5, 5), 1.0)
blur_s3 = cv2.GaussianBlur(img_natural, (11, 11), 3.0)
canny_blur_s1 = cv2.Canny(blur_s1, 80, 150)
canny_blur_s3 = cv2.Canny(blur_s3, 80, 150)

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes[0, 0].imshow(img_natural, cmap='gray'); axes[0, 0].set_title('Original'); axes[0, 0].axis('off')
axes[0, 1].imshow(canny_low, cmap='gray'); axes[0, 1].set_title('Canny (Low: 30-80)'); axes[0, 1].axis('off')
axes[0, 2].imshow(canny_mid, cmap='gray'); axes[0, 2].set_title('Canny (Mid: 80-150)'); axes[0, 2].axis('off')
axes[1, 0].imshow(canny_high, cmap='gray'); axes[1, 0].set_title('Canny (High: 150-220)'); axes[1, 0].axis('off')
axes[1, 1].imshow(canny_blur_s1, cmap='gray'); axes[1, 1].set_title('Canny (80-150) + Gauss S=1'); axes[1, 1].axis('off')
axes[1, 2].imshow(canny_blur_s3, cmap='gray'); axes[1, 2].set_title('Canny (80-150) + Gauss S=3'); axes[1, 2].axis('off')
plt.tight_layout()
plt.savefig(os.path.join(media_dir, "2_canny_thresholds_sigma.png"), dpi=150)
plt.close()

print("Notebook Runner: Executing Step 3 (Contour Detection)...")
img_shapes = cv2.imread(shapes_path)
gray_shapes = cv2.cvtColor(img_shapes, cv2.COLOR_BGR2GRAY)
thresh_shapes = cv2.adaptiveThreshold(gray_shapes, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
thresh_shapes_inv = cv2.bitwise_not(thresh_shapes)
contours, hierarchy = cv2.findContours(thresh_shapes_inv, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
img_contours_all = img_shapes.copy()
img_contours_filtered = img_shapes.copy()
cv2.drawContours(img_contours_all, contours, -1, (255, 0, 0), 3)
filtered_contours = [cnt for cnt in contours if 2000 < cv2.contourArea(cnt) < 25000]
cv2.drawContours(img_contours_filtered, filtered_contours, -1, (0, 255, 0), 3)

fig, axes = plt.subplots(1, 3, figsize=(15, 5))
axes[0].imshow(thresh_shapes_inv, cmap='gray'); axes[0].set_title('Binarización Adaptativa Invertida'); axes[0].axis('off')
axes[1].imshow(cv2.cvtColor(img_contours_all, cv2.COLOR_BGR2RGB)); axes[1].set_title(f'Todos los Contornos ({len(contours)})'); axes[1].axis('off')
axes[2].imshow(cv2.cvtColor(img_contours_filtered, cv2.COLOR_BGR2RGB)); axes[2].set_title(f'Contornos Filtrados ({len(filtered_contours)})'); axes[2].axis('off')
plt.tight_layout()
plt.savefig(os.path.join(media_dir, "3_contours_adaptive_hierarchy.png"), dpi=150)
plt.close()

print("Notebook Runner: Executing Step 4 (Polygon Approximation)...")
img_shapes_classified = img_shapes.copy()
for idx, cnt in enumerate(filtered_contours):
    perimeter = cv2.arcLength(cnt, True)
    area = cv2.contourArea(cnt)
    epsilon = 0.03 * perimeter
    approx = cv2.approxPolyDP(cnt, epsilon, True)
    vertices = len(approx)
    shape_name = "Desconocido"
    color = (255, 255, 255)
    if vertices == 3: shape_name = "Triangulo"; color = (0, 0, 255)
    elif vertices == 4:
        x, y, w, h = cv2.boundingRect(cnt)
        shape_name = "Cuadrado" if 0.95 <= float(w)/h <= 1.05 else "Rectangulo"
        color = (0, 255, 0)
    elif vertices == 5: shape_name = "Pentagono"; color = (255, 0, 255)
    elif vertices == 10: shape_name = "Estrella"; color = (0, 255, 255)
    elif vertices > 5: shape_name = "Circulo"; color = (255, 255, 0)
    M = cv2.moments(cnt)
    cx = int(M['m10']/M['m00']) if M['m00'] > 0 else 0
    cy = int(M['m01']/M['m00']) if M['m00'] > 0 else 0
    cv2.drawContours(img_shapes_classified, [approx], -1, color, 3)
    cv2.putText(img_shapes_classified, f"{shape_name} ({vertices}v)", (cx - 45, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img_shapes_classified, f"{shape_name} ({vertices}v)", (cx - 45, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

plt.figure(figsize=(8, 8))
plt.imshow(cv2.cvtColor(img_shapes_classified, cv2.COLOR_BGR2RGB))
plt.title('Aproximación Poligonal y Clasificación de Formas')
plt.axis('off')
plt.savefig(os.path.join(media_dir, "4_polygon_approximation_shapes.png"), dpi=150)
plt.close()

print("Notebook Runner: Executing Step 5 (Moments Analysis)...")
img_moments = img_shapes.copy()
for idx, cnt in enumerate(filtered_contours):
    M = cv2.moments(cnt)
    cx = int(M['m10']/M['m00']) if M['m00'] > 0 else 0
    cy = int(M['m01']/M['m00']) if M['m00'] > 0 else 0
    mu11, mu20, mu02 = M['mu11'], M['mu20'], M['mu02']
    diff = mu20 - mu02
    theta = 0.5 * np.arctan2(2 * mu11, diff) if diff != 0 else 0.0
    term1 = mu20 + mu02
    term2 = np.sqrt(4*(mu11**2) + (mu20 - mu02)**2)
    l1 = (term1 + term2)/2.0
    l2 = (term1 - term2)/2.0
    eccentricity = np.sqrt(1 - (l2/l1)) if l1 > 0 and l2 >= 0 else 0.0
    line_length = 50
    xe = int(cx + line_length * np.cos(theta))
    ye = int(cy + line_length * np.sin(theta))
    cv2.circle(img_moments, (cx, cy), 6, (0, 0, 255), -1)
    cv2.line(img_moments, (cx, cy), (xe, ye), (255, 255, 255), 3)
    cv2.putText(img_moments, f"Ecc:{round(eccentricity, 2)}", (cx - 30, cy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.putText(img_moments, f"Ecc:{round(eccentricity, 2)}", (cx - 30, cy + 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1, cv2.LINE_AA)

plt.figure(figsize=(8, 8))
plt.imshow(cv2.cvtColor(img_moments, cv2.COLOR_BGR2RGB))
plt.title('Centroides, Orientación y Excentricidad')
plt.axis('off')
plt.savefig(os.path.join(media_dir, "5_moments_centroids_orientation.png"), dpi=150)
plt.close()
print("Notebook Runner: All plots successfully exported!")
