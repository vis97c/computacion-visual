import cv2
import numpy as np
import os

def create_shapes_image(output_path):
    """Generates an image with distinct geometric shapes (triangle, rectangle, circle, pentagon, star)."""
    # Create a dark gray canvas (600x600)
    img = np.zeros((600, 600, 3), dtype=np.uint8) + 30
    
    # Define colors
    white = (240, 240, 240)
    light_blue = (230, 210, 50)
    orange = (50, 140, 240)
    magenta = (180, 50, 220)
    yellow = (50, 220, 240)
    
    # 1. Circle (top-left)
    cv2.circle(img, (150, 150), 60, light_blue, -1)
    
    # 2. Rectangle (top-right)
    cv2.rectangle(img, (380, 90), (510, 210), orange, -1)
    
    # 3. Triangle (bottom-left)
    pts_tri = np.array([[150, 370], [80, 490], [220, 490]], np.int32)
    cv2.drawContours(img, [pts_tri], 0, magenta, -1)
    
    # 4. Pentagon (bottom-right)
    pts_pent = []
    center_pent = (450, 430)
    r_pent = 70
    for i in range(5):
        angle = i * 2 * np.pi / 5 - np.pi / 2
        x = int(center_pent[0] + r_pent * np.cos(angle))
        y = int(center_pent[1] + r_pent * np.sin(angle))
        pts_pent.append([x, y])
    cv2.drawContours(img, [np.array(pts_pent, np.int32)], 0, yellow, -1)
    
    # 5. Star (center)
    pts_star = []
    center_star = (300, 300)
    r_outer = 60
    r_inner = 25
    for i in range(10):
        r = r_outer if i % 2 == 0 else r_inner
        angle = i * 2 * np.pi / 10 - np.pi / 2
        x = int(center_star[0] + r * np.cos(angle))
        y = int(center_star[1] + r * np.sin(angle))
        pts_star.append([x, y])
    cv2.drawContours(img, [np.array(pts_star, np.int32)], 0, white, -1)

    # Save to disk
    cv2.imwrite(output_path, img)
    print(f"Saved: {output_path}")

def create_pieces_image(output_path):
    """Generates an image of mechanical washers simulating a quality control conveyor belt.
    Some washers are perfect, some have defects (cracks, deformation, wrong size)."""
    # Canvas (800x400) - Light conveyor belt color
    img = np.zeros((400, 800, 3), dtype=np.uint8) + 180
    
    # Draw conveyor belt lines (aesthetic)
    for y in range(0, 400, 40):
        cv2.line(img, (0, y), (800, y), (170, 170, 170), 1)
    
    # Function to draw a washer (outer circle filled, inner circle filled with background color)
    def draw_washer(canvas, center, outer_r, inner_r, color, defect_type=None):
        cx, cy = center
        # Perfect washer mask
        mask = np.zeros(canvas.shape[:2], dtype=np.uint8)
        cv2.circle(mask, (cx, cy), outer_r, 255, -1)
        cv2.circle(mask, (cx, cy), inner_r, 0, -1)
        
        # Apply defect if specified
        if defect_type == "broken":
            # Draw a black polygon to slice off a chunk of the outer boundary
            pts = np.array([[cx + 35, cy - 25], [cx + 65, cy], [cx + 35, cy + 25]], np.int32)
            cv2.fillPoly(mask, [pts], 0)
        elif defect_type == "deformed":
            # Draw an oval outer boundary instead of a perfect circle
            mask_oval = np.zeros(canvas.shape[:2], dtype=np.uint8)
            cv2.ellipse(mask_oval, (cx, cy), (outer_r + 15, outer_r - 10), 30, 0, 360, 255, -1)
            cv2.circle(mask_oval, (cx, cy), inner_r, 0, -1)
            mask = mask_oval
        elif defect_type == "hole_size":
            # Washer with an excessively large inner hole (inner_r is increased)
            mask = np.zeros(canvas.shape[:2], dtype=np.uint8)
            cv2.circle(mask, (cx, cy), outer_r, 255, -1)
            cv2.circle(mask, (cx, cy), inner_r + 12, 0, -1)
        elif defect_type == "crack":
            # Draw a narrow crack line cutting into the washer
            cv2.line(mask, (cx, cy), (cx - 55, cy - 20), 0, 3)
            
        # Draw the masked washer on the canvas
        indices = np.where(mask == 255)
        canvas[indices] = color

    # Draw washers
    # Washer 1: Perfect (Normal) at (150, 200)
    draw_washer(img, (150, 200), 50, 20, (60, 60, 60))
    cv2.putText(img, "#1 (OK)", (100, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)
    
    # Washer 2: Broken edge at (300, 200)
    draw_washer(img, (300, 200), 50, 20, (60, 60, 60), defect_type="broken")
    cv2.putText(img, "#2 (Defecto: Roto)", (220, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)
    
    # Washer 3: Perfect at (450, 200)
    draw_washer(img, (450, 200), 50, 20, (60, 60, 60))
    cv2.putText(img, "#3 (OK)", (400, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (40, 40, 40), 2)
    
    # Washer 4: Deformed (Oval) at (600, 200)
    draw_washer(img, (600, 200), 50, 20, (60, 60, 60), defect_type="deformed")
    cv2.putText(img, "#4 (Defecto: Deformado)", (510, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)
    
    # Washer 5: Cracked or Wrong Inner Hole at (730, 200) -- Let's use wrong inner hole
    draw_washer(img, (720, 200), 50, 20, (60, 60, 60), defect_type="hole_size")
    cv2.putText(img, "#5 (Defecto: Diam. Int.)", (630, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 180), 2)

    cv2.imwrite(output_path, img)
    print(f"Saved: {output_path}")

def create_scale_ref_image(output_path):
    """Generates an image containing objects of unknown size next to a reference calibration square.
    The square is exactly 100x100 pixels, representing 20mm x 20mm (5 pixels per mm)."""
    img = np.zeros((500, 700, 3), dtype=np.uint8) + 225
    
    # Draw reference square (blue) at top-left
    # Reference Size: 100x100 pixels = 20mm x 20mm (Scale: 5 pixels / mm)
    cv2.rectangle(img, (50, 50), (150, 150), (180, 80, 80), -1)
    cv2.putText(img, "REF: 20x20 mm", (45, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 50, 50), 1, cv2.LINE_AA)
    
    # Draw objects to measure:
    # 1. A metallic block (Rectangle) - size 120 x 200 pixels = 24 x 40 mm
    cv2.rectangle(img, (250, 100), (450, 220), (70, 70, 70), -1)
    
    # 2. A circular token (Circle) - diameter 150 pixels = 30 mm
    cv2.circle(img, (550, 300), 75, (100, 100, 100), -1)
    
    # 3. A triangular wedge (Triangle) - base 140 pixels (28mm), height 180 pixels (36mm)
    pts = np.array([[200, 300], [130, 480], [270, 480]], np.int32)
    cv2.drawContours(img, [pts], 0, (80, 120, 80), -1)
    
    # Add text label indicators
    cv2.putText(img, "Pieza A", (320, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)
    cv2.putText(img, "Pieza B", (520, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)
    cv2.putText(img, "Pieza C", (170, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (40, 40, 40), 1)
    
    cv2.imwrite(output_path, img)
    print(f"Saved: {output_path}")

def create_natural_image(output_path):
    """Generates a synthetic complex natural-looking scene with smooth gradients and geometric textures.
    Ideal for comparing edge-detection filter thickness and noise resilience."""
    h, w = 512, 512
    # Create smooth gradient background
    x = np.linspace(0, 1, w)
    y = np.linspace(0, 1, h)
    xv, yv = np.meshgrid(x, y)
    
    # Base background pattern
    gray_bg = np.uint8((0.5 * np.sin(2 * np.pi * xv * 3) + 0.5 * np.cos(2 * np.pi * yv * 2) + 1.0) * 80 + 30)
    img = cv2.merge([gray_bg, gray_bg, gray_bg])
    
    # Draw a complex watch/clock like face (with multiple nested circles, tick marks, and text)
    center = (256, 256)
    cv2.circle(img, center, 180, (200, 200, 200), 4)
    cv2.circle(img, center, 170, (80, 80, 80), 2)
    cv2.circle(img, center, 10, (50, 50, 220), -1)
    
    # Draw hands
    cv2.line(img, center, (256, 120), (20, 20, 20), 4) # Minute hand
    cv2.line(img, center, (340, 310), (20, 20, 20), 6) # Hour hand
    cv2.line(img, center, (150, 200), (40, 40, 230), 2) # Second hand
    
    # Draw tick marks
    for angle_deg in range(0, 360, 30):
        angle = np.deg2rad(angle_deg)
        p1 = (int(center[0] + 150 * np.cos(angle)), int(center[1] + 150 * np.sin(angle)))
        p2 = (int(center[0] + 168 * np.cos(angle)), int(center[1] + 168 * np.sin(angle)))
        cv2.line(img, p1, p2, (30, 30, 30), 3)
        
    # Draw a textured rectangular card underneath
    sub_rect = img[320:460, 40:220]
    grid = np.zeros(sub_rect.shape, dtype=np.uint8)
    grid[::10, :, :] = 255
    grid[:, ::10, :] = 255
    img[320:460, 40:220] = cv2.addWeighted(sub_rect, 0.6, grid, 0.4, 0)
    
    # Add a smooth gradient overlay circle
    gradient_circle = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(gradient_circle, (120, 120), 80, 255, -1)
    gradient_mask = np.float32(gradient_circle) / 255.0
    for c in range(3):
        img[:, :, c] = np.uint8(img[:, :, c] * (1.0 - 0.5 * gradient_mask) + (128 * xv) * gradient_mask)

    # Add minor Gaussian noise to simulate real capture noise
    noise = np.random.normal(0, 8, img.shape).astype(np.float32)
    img_noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)

    cv2.imwrite(output_path, img_noisy)
    print(f"Saved: {output_path}")

if __name__ == "__main__":
    # Target directory for output images
    output_dir = os.path.join(os.path.dirname(__file__), "..", "media")
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating synthetic workshop test images...")
    create_shapes_image(os.path.join(output_dir, "shapes.png"))
    create_pieces_image(os.path.join(output_dir, "pieces.png"))
    create_scale_ref_image(os.path.join(output_dir, "scale_ref.png"))
    create_natural_image(os.path.join(output_dir, "natural.png"))
    print("All test images successfully created in the 'media/' folder!")
