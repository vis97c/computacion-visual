import cv2
import numpy as np

def load_image(image_path_or_bytes):
    """
    Loads an image from a file path or from bytes.
    Automatically handles TIFF and other formats supported by OpenCV.
    """
    if isinstance(image_path_or_bytes, bytes):
        nparr = np.frombuffer(image_path_or_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    else:
        img = cv2.imread(image_path_or_bytes)
    return img

def segment_particles(img, min_area=200, border_margin=5):
    """
    Applies adaptive thresholding and morphological filters to segment
    particles from the white paper background.
    Filters out particles that touch the border, are too small, or belong
    to fixed markings like scale bars, text annotations, and gridded paper lines.
    Returns:
        contours: list of valid contours
        thresh: the binary thresholded image (inverted, so background is black and particles are white)
    """
    if img is None:
        return [], None
        
    h_img, w_img = img.shape[:2]
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # 1. Check if the image has a cyan/blue gridded background (mean hue > 70)
    # If so, mask out the dark teal grid lines by replacing them with the median gray value.
    gray_masked = gray.copy()
    mean_hue = np.mean(hsv[:, :, 0])
    if mean_hue > 70:
        # Strictly target grid dots/lines without erasing fibers
        lower_grid = np.array([90, 130, 30])
        upper_grid = np.array([108, 255, 180])
        grid_mask = cv2.inRange(hsv, lower_grid, upper_grid)
        median_val = np.median(gray)
        gray_masked[grid_mask > 0] = median_val
        
    # 2. Blur to smooth out paper texture and noise
    blurred = cv2.GaussianBlur(gray_masked, (5, 5), 0)
    
    # 3. Adaptive thresholding: since background is paper, we segment dark objects.
    # Invert the threshold (THRESH_BINARY_INV) so particles are white (255) and background is black (0)
    thresh = cv2.adaptiveThreshold(
        blurred, 255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        51, 8
    )
    
    # 4. Morphological opening to remove tiny noise spots
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
    
    # 5. Find all external contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # 6. First pass: Detect scale bar horizontal line(s)
    # The scale bar line is usually a very wide, thin, horizontal line.
    scale_lines_boxes = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        aspect_ratio = float(w) / h if h > 0 else 0
        if aspect_ratio > 8 and h < 50 and w > 80:
            scale_lines_boxes.append((x, y, w, h))
            
    # 7. Second pass: Filter out noise, borders, and scale bar elements
    filtered_contours = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
            
        x, y, w, h = cv2.boundingRect(c)
        # Check if bounding box touches the edge of the image
        if (x <= border_margin) or (y <= border_margin) or \
           (x + w >= w_img - border_margin) or (y + h >= h_img - border_margin):
            continue
            
        # Check if this contour is one of the detected scale lines
        is_scale_line = False
        for sx, sy, sw, sh in scale_lines_boxes:
            if x == sx and y == sy and w == sw and h == sh:
                is_scale_line = True
                break
        if is_scale_line:
            continue
            
        # Check if this contour is close to any detected scale lines (likely scale text/markings like "200 µm")
        is_near_scale = False
        max_dist = 150 if h_img > 1000 else 60
        for sx, sy, sw, sh in scale_lines_boxes:
            # Horizontal overlap check
            overlap = not (x + w < sx or x > sx + sw)
            # Vertical distance check
            vertical_dist = min(abs(y - sy), abs(y + h - sy), abs(y - (sy + sh)), abs(y + h - (sy + sh)))
            if overlap and vertical_dist < max_dist:
                is_near_scale = True
                break
        if is_near_scale:
            continue
            
        # Fallback static ROI checks for other printed headers that don't have clear lines
        if h_img > 1000 and y > h_img * 0.7:  # bottom 30% of high-res images
            continue

            
        filtered_contours.append(c)
        
    return filtered_contours, thresh

def extract_features(contour, img, hsv_img):
    """
    Extracts 16 morphology and color features from a particle contour.
    Features:
        0. Area
        1. Perimeter
        2. Circularity
        3. Aspect Ratio (w/h)
        4. Elongation (major_axis / minor_axis of fitted ellipse)
        5. Solidity (area / convex_hull_area)
        6. Eccentricity
        7-9. Mean B, G, R
        10-12. Std Dev B, G, R
        13-15. Mean H, S, V
    """
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    
    # Shape properties
    circularity = 4 * np.pi * area / (perimeter ** 2) if perimeter > 0 else 0
    
    x, y, w, h = cv2.boundingRect(contour)
    aspect_ratio = float(w) / h if h > 0 else 0
    
    # Ellipse features (requires at least 5 points)
    if len(contour) >= 5:
        try:
            _, (ma, my), _ = cv2.fitEllipse(contour)
            major = max(ma, my)
            minor = min(ma, my)
            elongation = major / minor if minor > 0 else 1.0
            eccentricity = np.sqrt(1 - (minor / major) ** 2) if major > 0 else 0.0
        except:
            elongation = 1.0
            eccentricity = 0.0
    else:
        elongation = 1.0
        eccentricity = 0.0
        
    hull = cv2.convexHull(contour)
    hull_area = cv2.contourArea(hull)
    solidity = area / hull_area if hull_area > 0 else 0.0
    
    # Color features inside contour
    mask = np.zeros(img.shape[:2], dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    
    mean_val, std_val = cv2.meanStdDev(img, mask=mask)
    mean_bgr = mean_val.flatten()[:3]
    std_bgr = std_val.flatten()[:3]
    
    mean_hsv = cv2.mean(hsv_img, mask=mask)[:3]
    
    features = [
        float(area),
        float(perimeter),
        float(circularity),
        float(aspect_ratio),
        float(elongation),
        float(solidity),
        float(eccentricity),
        float(mean_bgr[0]), float(mean_bgr[1]), float(mean_bgr[2]),
        float(std_bgr[0]), float(std_bgr[1]), float(std_bgr[2]),
        float(mean_hsv[0]), float(mean_hsv[1]), float(mean_hsv[2])
    ]
    
    return features

def get_class_color(class_name):
    """
    Returns BGR color for drawing boxes.
    """
    bgr_colors = {
        'Pellet': (0, 255, 0),        # Green
        'Fibra': (0, 0, 255),         # Red
        'Fragmento': (0, 165, 255),   # Orange
        'Pelicula': (255, 0, 255),    # Magenta
        'Espuma': (0, 255, 255),      # Yellow
        'No Microplastico': (150, 150, 150) # Gray
    }
    return bgr_colors.get(class_name, (255, 255, 255))
