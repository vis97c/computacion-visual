import cv2
import numpy as np
import os

def run_quality_inspection():
    # File paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_path = os.path.join(base_dir, "media", "pieces.png")
    output_path = os.path.join(base_dir, "media", "6_quality_control_defects.png")
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} does not exist. Run generate_test_images.py first.")
        return
    
    # Load image
    img = cv2.imread(input_path)
    h, w, _ = img.shape
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Binarization using adaptive thresholding or simple thresholding
    # Since background is light gray (~180) and washers are dark (~60)
    _, thresh = cv2.threshold(gray, 110, 255, cv2.THRESH_BINARY_INV)
    
    # Clean binary mask with morphological operations
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
    
    # Find contours with hierarchy (CCOMP gives 2-level hierarchy: external and internal boundaries)
    contours, hierarchy = cv2.findContours(thresh, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE)
    
    if hierarchy is None:
        print("No contours found.")
        return
        
    hierarchy = hierarchy[0]
    
    # Filter and analyze external contours
    # Washers should have a minimum area to filter out text and lines
    min_area = 3000
    max_area = 15000
    
    ok_count = 0
    defect_count = 0
    total_count = 0
    
    # Visual output canvas (copy of original image)
    output_img = img.copy()
    
    print("\n--- INICIANDO SISTEMA DE CONTROL DE CALIDAD ---")
    
    for i, cnt in enumerate(contours):
        # Check if it is an external contour (has no parent contour in 2-level hierarchy)
        # In cv2.RETR_CCOMP, external contours have hierarchy[i][3] == -1
        if hierarchy[i][3] != -1:
            continue
            
        area = cv2.contourArea(cnt)
        if not (min_area < area < max_area):
            continue
            
        total_count += 1
        
        # 1. Centroid
        M = cv2.moments(cnt)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])
        else:
            cx, cy = 0, 0
            
        # 2. Outer radius and circularity
        perimeter = cv2.arcLength(cnt, True)
        (x_circle, y_circle), r_outer = cv2.minEnclosingCircle(cnt)
        r_outer = round(r_outer, 1)
        
        # Fit ellipse to evaluate shape eccentricity/deformations
        ellipse_aspect_ratio = 1.0
        if len(cnt) >= 5:
            ellipse = cv2.fitEllipse(cnt)
            (center, axes, angle) = ellipse
            major_axis = max(axes)
            minor_axis = min(axes)
            ellipse_aspect_ratio = major_axis / minor_axis if minor_axis > 0 else 1.0
            
        # Circularity factor = 4 * pi * area / (perimeter^2)
        circularity = 4 * np.pi * area / (perimeter ** 2)
        
        # 3. Inner Hole Analysis (Hierarchy Child)
        child_idx = hierarchy[i][2]
        has_hole = child_idx != -1
        
        r_inner = 0
        if has_hole:
            child_cnt = contours[child_idx]
            _, r_inner = cv2.minEnclosingCircle(child_cnt)
            r_inner = round(r_inner, 1)
            
        # 4. Defect Classification Rules
        is_ok = True
        defect_reason = "OK"
        
        # Thresholds for defects (based on target perfect values: r_outer ~ 50px, r_inner ~ 20px)
        # R_outer perfect ~ 50px
        # Circularity perfect circle contour ~ 0.90+ (since it's a solid outer boundary)
        # Outer ratio of area to enclosing circle area
        enclosing_circle_area = np.pi * (r_outer ** 2)
        area_ratio = area / enclosing_circle_area if enclosing_circle_area > 0 else 0
        
        if not has_hole:
            is_ok = False
            defect_reason = "Sin Orificio"
        elif r_inner > 26:
            is_ok = False
            defect_reason = "Diam. Int. Excesivo"
        elif area_ratio < 0.85:
            # Sliced off or broken
            is_ok = False
            defect_reason = "Pieza Rota/Incompleta"
        elif ellipse_aspect_ratio > 1.15:
            # Oval / squished shape
            is_ok = False
            defect_reason = "Pieza Deformada"
            
        # 5. Draw Results
        color = (0, 200, 0) if is_ok else (0, 0, 220)  # Green if OK, Red if Defect
        
        if is_ok:
            ok_count += 1
        else:
            defect_count += 1
            
        # Draw contour boundary
        cv2.drawContours(output_img, [cnt], -1, color, 3)
        # Draw centroid
        cv2.circle(output_img, (cx, cy), 5, (255, 0, 0), -1)
        
        # Draw child contour (inner hole) if exists
        if has_hole:
            cv2.drawContours(output_img, [contours[child_idx]], -1, (255, 100, 0), 2)
            
        # Draw bounding rectangle
        rx, ry, rw, rh = cv2.boundingRect(cnt)
        cv2.rectangle(output_img, (rx - 5, ry - 5), (rx + rw + 5, ry + rh + 5), color, 1)
        
        # Display Stats above piece
        text_y_start = ry - 15
        cv2.putText(output_img, f"ID: #{total_count} - {defect_reason}", (rx, text_y_start), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
        cv2.putText(output_img, f"R_ext: {r_outer}px", (rx, text_y_start + 120), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 50, 50), 1, cv2.LINE_AA)
        cv2.putText(output_img, f"R_int: {r_inner}px", (rx, text_y_start + 132), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 50, 50), 1, cv2.LINE_AA)
        cv2.putText(output_img, f"Eccen: {round(ellipse_aspect_ratio, 2)}", (rx, text_y_start + 144), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (50, 50, 50), 1, cv2.LINE_AA)
        
        # Print to console
        print(f"Pieza #{total_count}: Centroid=({cx}, {cy}) | R_ext={r_outer}px | R_int={r_inner}px | AspectRatio={round(ellipse_aspect_ratio, 3)} | Area Ratio={round(area_ratio, 3)} | Estado: {defect_reason}")
        
    # Draw summary banner at top of output image
    cv2.rectangle(output_img, (0, 0), (w, 45), (40, 40, 40), -1)
    summary_text = f"CONTROL DE CALIDAD - Total: {total_count} | Aceptadas (OK): {ok_count} | Defectuosas: {defect_count}"
    cv2.putText(output_img, summary_text, (20, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (240, 240, 240), 2, cv2.LINE_AA)
    
    # Save the output image
    cv2.imwrite(output_path, output_img)
    print(f"--- INSPECION COMPLETADA ---")
    print(f"Resultados guardados en: {output_path}")
    print(f"Resumen: Total={total_count}, OK={ok_count}, Defectos={defect_count}\n")

if __name__ == "__main__":
    run_quality_inspection()
