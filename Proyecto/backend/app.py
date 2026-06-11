import os
import sys
import base64
import joblib
import cv2
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add current directory to path so imports work when running from root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pipeline import load_image, segment_particles, extract_features, get_class_color
from model_trainer import train_and_evaluate, resolve_consensus_label

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

def normalize_model_name(name):
    if not name:
        return "ceroplastic"
    name = str(name).strip().lower()
    if name == "original":
        return "ceroplastic"
    if name == "fusion":
        return "ceroplastic_valerio"
    return name

MODEL_PATHS = {
    "ceroplastic": os.path.join(os.path.dirname(os.path.abspath(__file__)), "microplastics_model_ceroplastic.joblib"),
    "valerio": os.path.join(os.path.dirname(os.path.abspath(__file__)), "microplastics_model_valerio.joblib"),
    "ceroplastic_valerio": os.path.join(os.path.dirname(os.path.abspath(__file__)), "microplastics_model_ceroplastic_valerio.joblib")
}

EXCEL_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Ceroplastic/Clasificación microplasticos-guia.xlsx")

def get_model(model_name="ceroplastic"):
    """
    Loads the trained model and metadata.
    If it doesn't exist, trains one automatically.
    """
    model_name = normalize_model_name(model_name)
    if model_name not in MODEL_PATHS:
        model_name = "ceroplastic"
        
    model_path = MODEL_PATHS[model_name]
    if not os.path.exists(model_path):
        # If it's ceroplastic and we have the legacy model, copy it to avoid retraining
        if model_name == "ceroplastic":
            legacy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "microplastics_model.joblib")
            if os.path.exists(legacy_path):
                import shutil
                try:
                    shutil.copy(legacy_path, model_path)
                    print(f"Copied legacy model to {model_path}")
                except Exception as e:
                    print(f"Warning: Could not copy legacy model: {e}")
                    
    if not os.path.exists(model_path):
        print(f"Model file for '{model_name}' not found. Training model automatically...")
        try:
            train_and_evaluate(model_name)
        except Exception as e:
            print(f"Error training model '{model_name}': {e}")
            return None
            
    try:
        model_data = joblib.load(model_path)
        return model_data
    except Exception as e:
        print(f"Error loading model '{model_name}': {e}")
        # Fallback to legacy file if it exists
        if model_name == "ceroplastic":
            legacy_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "microplastics_model.joblib")
            if os.path.exists(legacy_path):
                try:
                    return joblib.load(legacy_path)
                except:
                    pass
        return None

@app.route("/api/predict", methods=["POST"])
def predict():
    """
    Receives an image, segments particles, predicts their classes,
    draws bounding boxes, and returns the results.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
        
    model_name = request.args.get("model", request.form.get("model", "ceroplastic"))
    model_name = normalize_model_name(model_name)
    
    try:
        file_bytes = file.read()
        img = load_image(file_bytes)
        if img is None:
            return jsonify({"error": "Invalid image format or failed to load image"}), 400
            
        h_img, w_img = img.shape[:2]
        
        # Load model
        model_data = get_model(model_name)
        if model_data is None:
            return jsonify({"error": f"Model '{model_name}' not available"}), 500
            
        rf_model = model_data["model"]
        
        # Segment particles
        contours, thresh = segment_particles(img)
        
        particles = []
        counts = {
            "Pellet": 0,
            "Fibra": 0,
            "Fragmento": 0,
            "Pelicula": 0,
            "Espuma": 0,
            "No Microplastico": 0
        }
        
        annotated_img = img.copy()
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        for i, c in enumerate(contours):
            x, y, w, h = cv2.boundingRect(c)
            area = cv2.contourArea(c)
            perimeter = cv2.arcLength(c, True)
            circ = 4 * np.pi * area / (perimeter**2) if perimeter > 0 else 0
            
            # Extract features for this particle
            features = extract_features(c, img, hsv_img)
            
            # Run prediction
            pred_class = rf_model.predict([features])[0]
            
            # Track counts
            if pred_class in counts:
                counts[pred_class] += 1
                
            # Draw bounding box and label
            color = get_class_color(pred_class)
            cv2.rectangle(annotated_img, (x, y), (x + w, y + h), color, 2)
            
            # Text label
            label_text = f"P{i}: {pred_class}"
            # Adjust font scale based on resolution
            font_scale = 0.5 if h_img < 1000 else 1.0
            thickness = 1 if h_img < 1000 else 2
            cv2.putText(
                annotated_img, label_text, (x, max(y - 5, 15)), 
                cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, thickness
            )
            
            particles.append({
                "id": i,
                "x": int(x),
                "y": int(y),
                "w": int(w),
                "h": int(h),
                "area": float(area),
                "circularity": float(circ),
                "class": pred_class
            })
            
        # Encode annotated image as JPEG in base64
        _, buffer = cv2.imencode(".jpg", annotated_img)
        img_base64 = base64.b64encode(buffer).decode("utf-8")
        
        # Encode original image as JPEG in base64
        _, orig_buffer = cv2.imencode(".jpg", img)
        orig_base64 = base64.b64encode(orig_buffer).decode("utf-8")
        
        # Calculate summary metrics
        total_detected = len(contours)
        total_microplastics = sum(counts[c] for c in counts if c != "No Microplastico")
        
        return jsonify({
            "annotated_image": img_base64,
            "original_image": orig_base64,
            "particles": particles,
            "counts": counts,
            "total_detected": total_detected,
            "total_microplastics": total_microplastics,
            "image_size": [w_img, h_img],
            "model_used": model_name
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to process image: {str(e)}"}), 500

@app.route("/api/model-info", methods=["GET"])
def model_info():
    """
    Returns metrics of the currently loaded model.
    """
    model_name = request.args.get("model", "ceroplastic")
    model_name = normalize_model_name(model_name)
    
    model_data = get_model(model_name)
    if model_data is None:
        return jsonify({"error": f"Model '{model_name}' not available"}), 500
        
    return jsonify({
        "classes": model_data["classes"],
        "mean_accuracy": model_data["mean_accuracy"],
        "feature_importances": model_data["feature_importances"],
        "confusion_matrix": model_data["confusion_matrix"],
        "model_name": model_name
    })

@app.route("/api/train", methods=["POST"])
def train():
    """
    Triggers model training and returns the new model information.
    """
    data = request.get_json(silent=True) or {}
    model_name = request.args.get("model", data.get("model", "ceroplastic"))
    model_name = normalize_model_name(model_name)
    
    try:
        train_and_evaluate(model_name)
        return model_info()
    except Exception as e:
        return jsonify({"error": f"Model training failed: {str(e)}"}), 500

@app.route("/api/stats", methods=["GET"])
def stats():
    """
    Reads the Excel file and summarizes the annotator statistics.
    """
    if not os.path.exists(EXCEL_PATH):
        return jsonify({"error": f"Excel file not found at {EXCEL_PATH}"}), 404
        
    try:
        xl = pd.ExcelFile(EXCEL_PATH)
        df_m = xl.parse("Melissa").iloc[1:]
        df_b = xl.parse("Brayan").iloc[1:]
        df_c = xl.parse("Camila").iloc[1:]
        df_r = xl.parse("Resumen").iloc[1:]
        
        df_r.columns = ["Imagen", "Melissa", "Brayan", "Camila", "TipoConsenso", "Folder"]
        
        # Calculate consensus distribution
        df_r["FinalClass"] = df_r.apply(resolve_consensus_label, axis=1)
        class_dist = df_r["FinalClass"].value_counts().to_dict()
        
        # Calculate annotator agreement
        df_clean = pd.DataFrame({
            "Melissa": df_r["Melissa"].astype(str).str.strip().str.lower(),
            "Brayan": df_r["Brayan"].astype(str).str.strip().str.lower(),
            "Camila": df_r["Camila"].astype(str).str.strip().str.lower()
        }).dropna()
        
        # Normalize responses
        def norm(v):
            if "si" in v or "sí" in v: return "si"
            if "no" in v: return "no"
            return "no se"
            
        for col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(norm)
            
        all_agree = (df_clean["Melissa"] == df_clean["Brayan"]) & (df_clean["Brayan"] == df_clean["Camila"])
        agreement_rate = float(all_agree.mean())
        
        return jsonify({
            "total_samples": len(df_r),
            "class_distribution": class_dist,
            "agreement_rate": agreement_rate,
            "annotator_counts": {
                "Melissa": df_clean["Melissa"].value_counts().to_dict(),
                "Brayan": df_clean["Brayan"].value_counts().to_dict(),
                "Camila": df_clean["Camila"].value_counts().to_dict()
            }
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed to compute statistics: {str(e)}"}), 500

CORRECTIONS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_corrections.json")

@app.route("/api/correct", methods=["POST"])
def correct():
    """
    Saves manual labeling corrections for a specific file.
    """
    import json
    data = request.get_json()
    if not data or "filename" not in data or "particles" not in data:
        return jsonify({"error": "Invalid payload"}), 400
        
    filename = data["filename"]
    particles = data["particles"]
    
    # Load existing corrections
    corrections = {}
    if os.path.exists(CORRECTIONS_PATH):
        try:
            with open(CORRECTIONS_PATH, 'r') as f:
                corrections = json.load(f)
        except Exception as e:
            print(f"Error reading corrections: {e}")
            
    # Update corrections for this file
    corrections[filename] = particles
    
    try:
        with open(CORRECTIONS_PATH, 'w') as f:
            json.dump(corrections, f, indent=2)
        return jsonify({"success": True, "message": "Corrections saved successfully"})
    except Exception as e:
        return jsonify({"error": f"Failed to save corrections: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
