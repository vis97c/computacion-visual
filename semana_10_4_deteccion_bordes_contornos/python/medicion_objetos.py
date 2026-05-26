import cv2
import numpy as np
import os

def run_object_measurement():
    # File paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_path = os.path.join(base_dir, "media", "scale_ref.png")
    output_path = os.path.join(base_dir, "media", "7_corners_and_scale_measurement.png")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist. Run generate_test_images.py first.")
        return
    
    # Load image
    img = cv2.imread(input_path)
    output_img = img.copy()
    h, w, _ = img.shape
    
    # 1. Calibrar Escala usando el cuadrado de referencia azul
    # El cuadrado azul tiene color BGR (180, 80, 80) -> Azul dominante
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Rango de color azul en HSV para detectar el bloque de referencia
    lower_blue = np.array([100, 100, 50])
    upper_blue = np.array([140, 255, 255])
    blue_mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    # Encontrar contorno de la referencia
    ref_contours, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if len(ref_contours) == 0:
        print("Error: No se encontró la tarjeta de calibración de referencia azul.")
        # Fallback a escala fija (5 px/mm)
        pixels_per_mm = 5.0
        print(f"Usando calibración por defecto: {pixels_per_mm} px/mm")
    else:
        # Encontrar el contorno más grande de la máscara azul
        ref_contour = max(ref_contours, key=cv2.contourArea)
        rx, ry, rw, rh = cv2.boundingRect(ref_contour)
        
        # El cuadrado azul representa 20mm de lado en la realidad
        ref_real_size_mm = 20.0
        # Usamos el promedio del ancho y el alto en píxeles para robustez
        ref_pixel_size = (rw + rh) / 2.0
        pixels_per_mm = ref_pixel_size / ref_real_size_mm
        
        print("\n--- SISTEMA DE CALIBRACIÓN DE ESCALA ---")
        print(f"Cuadrado de Referencia detectado en x={rx}, y={ry}")
        print(f"Tamaño en Píxeles: {ref_pixel_size}px | Tamaño Real: {ref_real_size_mm}mm")
        print(f"Factor de Escala: {round(pixels_per_mm, 3)} px/mm")

    # 2. Segmentar todas las piezas (A, B, C)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Umbralizado invertido para separar objetos oscuros de fondo claro (225)
    _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
    
    # Restar el cuadrado azul de la máscara binaria para no medirlo como objeto
    thresh = cv2.bitwise_and(thresh, thresh, mask=cv2.bitwise_not(blue_mask))
    
    # Limpieza morfológica
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Encontrar contornos de las piezas
    obj_contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print("\n--- INICIANDO MEDICIÓN DE OBJETOS ---")
    
    for idx, cnt in enumerate(obj_contours):
        area_px = cv2.contourArea(cnt)
        if area_px < 1000:  # Filtrar ruido de texto o líneas
            continue
            
        # Calcular momentos para centroide
        M = cv2.moments(cnt)
        cx = int(M['m10'] / M['m00']) if M['m00'] > 0 else 0
        cy = int(M['m01'] / M['m00']) if M['m00'] > 0 else 0
        
        # Calcular perímetro en píxeles y convertir a mm
        perimeter_px = cv2.arcLength(cnt, True)
        perimeter_mm = perimeter_px / pixels_per_mm
        
        # Calcular área en mm²
        area_mm2 = area_px / (pixels_per_mm ** 2)
        
        # Aproximación poligonal para clasificar la forma
        epsilon = 0.03 * perimeter_px
        approx = cv2.approxPolyDP(cnt, epsilon, True)
        vertices = len(approx)
        
        # Bounding box rotado (orientación del objeto)
        min_area_rect = cv2.minAreaRect(cnt)
        (center, size, angle) = min_area_rect
        w_px, h_px = size
        
        w_mm = w_px / pixels_per_mm
        h_mm = h_px / pixels_per_mm
        
        # Identificación de forma por contorno
        shape_name = "Polígono"
        if vertices == 3:
            shape_name = "Triángulo"
        elif vertices == 4:
            # Comprobar si es un rectángulo o cuadrado
            aspect_ratio = max(w_px, h_px) / min(w_px, h_px)
            shape_name = "Cuadrado" if aspect_ratio < 1.1 else "Rectángulo"
        elif vertices > 6:
            shape_name = "Círculo / Óvalo"
            
        # Dibujar contorno y caja rotada
        box = cv2.boxPoints(min_area_rect)
        box = np.int32(box)
        cv2.drawContours(output_img, [box], 0, (0, 100, 255), 1) # Caja rotada naranja/azul
        cv2.drawContours(output_img, [cnt], -1, (200, 0, 100), 2)  # Contorno púrpura
        
        # Dibujar centroide
        cv2.circle(output_img, (cx, cy), 4, (0, 0, 255), -1)
        
        # Mostrar mediciones en la imagen
        label_y = cy - 40
        cv2.putText(output_img, f"{shape_name} (Vertices: {vertices})", (cx - 60, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.putText(output_img, f"Dim: {round(max(w_mm, h_mm), 1)} x {round(min(w_mm, h_mm), 1)} mm", (cx - 60, label_y + 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1, cv2.LINE_AA)
        cv2.putText(output_img, f"Area: {round(area_mm2, 1)} mm2", (cx - 60, label_y + 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1, cv2.LINE_AA)
        cv2.putText(output_img, f"Perim: {round(perimeter_mm, 1)} mm", (cx - 60, label_y + 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (80, 80, 80), 1, cv2.LINE_AA)
        
        print(f"Objeto #{idx+1}: {shape_name} | Vértices={vertices} | Centroide=({cx},{cy}) | Dimensiones={round(w_mm,1)}x{round(h_mm,1)}mm | Área={round(area_mm2,1)}mm²")

    # 3. Detección de esquinas Harris (Corner Detection)
    # Convertir a flotante de 32 bits
    gray_float = np.float32(gray)
    # Aplicar Harris
    dst = cv2.cornerHarris(gray_float, blockSize=3, ksize=3, k=0.04)
    # Dilatar para visualización de esquinas
    dst = cv2.dilate(dst, None)
    
    # Umbral para las esquinas detectadas e incorporarlas a la imagen final
    # Marcamos las esquinas con puntos cyan brillantes
    output_img[dst > 0.01 * dst.max()] = [255, 255, 0]
    
    # Rotulación e indicación en el mapa
    cv2.putText(output_img, "* Puntos Cyan = Esquinas Harris Detectadas", (250, 480),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 100, 0), 1, cv2.LINE_AA)
    
    # Dibujar regla de escala visual arriba a la derecha
    cv2.rectangle(output_img, (w - 200, 10), (w - 10, 40), (240, 240, 240), -1)
    cv2.rectangle(output_img, (w - 200, 10), (w - 10, 40), (100, 100, 100), 1)
    # Una barra de 10mm de largo (50 píxeles si la escala es 5)
    bar_width_px = int(10.0 * pixels_per_mm)
    cv2.line(output_img, (w - 180, 25), (w - 180 + bar_width_px, 25), (0, 0, 0), 3)
    cv2.putText(output_img, "10 mm", (w - 180, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 0, 0), 1, cv2.LINE_AA)
    
    # Guardar imagen resultante
    cv2.imwrite(output_path, output_img)
    print("\n--- MEDICIÓN Y DETECCIÓN DE ESQUINAS COMPLETADAS ---")
    print(f"Resultados guardados en: {output_path}\n")

if __name__ == "__main__":
    run_object_measurement()
