import cv2
import numpy as np
import os

def simulate_processing_output():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    input_path = os.path.join(base_dir, "media", "natural.png")
    output_path = os.path.join(base_dir, "media", "8_processing_sobel_convolution.png")
    
    if not os.path.exists(input_path):
        print("Error: natural.png not found.")
        return
        
    # Load original image
    img = cv2.imread(input_path)
    img_resized = cv2.resize(img, (512, 512))
    
    # Run manual Sobel
    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.sqrt(sobelx**2 + sobely**2)
    
    # Threshold (similar to edgeThreshold = 60 in processing)
    thresh = 60.0
    edge_mask = mag > thresh
    
    # Create Neon Sketch Artistic Fusion
    artistic = np.zeros_like(img_resized)
    h, w, _ = img_resized.shape
    
    for y in range(h):
        for x in range(w):
            if edge_mask[y, x]:
                # Neon gradient (Cyan to Purple/Pink) based on horizontal position
                ratio = x / w
                r = int(255 * ratio)
                g = int(255 * (1.0 - ratio))
                b = 255
                artistic[y, x] = [b, g, r]  # BGR order
            else:
                # Dimmed original image
                artistic[y, x] = np.uint8(img_resized[y, x] * 0.25)
                
    # Create final 1024x512 canvas
    canvas = np.zeros((512, 1024, 3), dtype=np.uint8)
    canvas[:, :512] = img_resized
    canvas[:, 512:] = artistic
    
    # Add title text for left panel
    cv2.putText(canvas, "Imagen Original", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Add right panel banner and title
    cv2.rectangle(canvas, (512, 0), (1024, 45), (255, 180, 0), -1) # Blue-cyan banner in BGR
    cv2.putText(canvas, "Modo 5: Efecto Artistico 'Neon Glow' (Fusion)", (532, 28), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    
    # Add bottom instruction banner
    cv2.rectangle(canvas, (0, 480), (1024, 512), (30, 30, 30), -1)
    cv2.putText(canvas, "Controles: [1-5] Cambiar Modo | [+/-] Ajustar Umbral: 60 | Convoluciones Sobel calculadas pixel a pixel", 
                (20, 500), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1, cv2.LINE_AA)
                
    cv2.imwrite(output_path, canvas)
    print(f"Processing simulation saved to: {output_path}")

if __name__ == "__main__":
    simulate_processing_output()
