import os
import pandas as pd
import numpy as np
import cv2
import joblib
import json
from sklearn.model_selection import StratifiedKFold
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

from pipeline import load_image, segment_particles, extract_features

def get_image_paths_mapping(df):
    """
    Maps Resumen row indices to the actual TIFF/PNG file paths on disk.
    Matches the file structures inside the Ceroplastic directory.
    """
    mapping = {}
    current_folder = None
    
    for idx, row in df.iterrows():
        val = row.iloc[0]
        if pd.isna(val):
            continue
            
        val_str = str(val).strip()
        # Check for folder headers
        if val_str in ['P2T2M1-A', 'P3T1M1-B', 'P6T1M4B', 'P7T1M1-B', 'P8T1M5-B']:
            current_folder = val_str
            continue
            
        try:
            img_num = int(val)
            if current_folder is None:
                # First part (1 to 115) maps to P5, P7, P4 folders
                if 1 <= img_num <= 51:
                    mapping[idx] = f"Ceroplastic/P5T1M5-A/IMG_{img_num:04d}.tif"
                elif 52 <= img_num <= 82:
                    mapping[idx] = f"Ceroplastic/P7T1M4-B/IMG_{img_num:04d}.tif"
                elif 83 <= img_num <= 115:
                    mapping[idx] = f"Ceroplastic/P4T1M4-B/IMG_{img_num:04d}.tif"
            else:
                if current_folder == 'P2T2M1-A':
                    mapping[idx] = f"Ceroplastic/P2T2M1-A/P2T1M1-A-{img_num}.tif"
                elif current_folder == 'P3T1M1-B':
                    mapping[idx] = f"Ceroplastic/P3T1M1-B/P3T1M1-B-{img_num:02d}.tif"
                elif current_folder == 'P6T1M4B':
                    if img_num == 20:
                        mapping[idx] = f"Ceroplastic/P6T1M4-B/P6T1M4-B.png"
                    else:
                        mapping[idx] = f"Ceroplastic/P6T1M4-B/P6T1M4-B-{img_num}.tif"
                elif current_folder == 'P7T1M1-B':
                    mapping[idx] = f"Ceroplastic/P7T1M1-B/P7T1M1-B-{img_num}.tif"
                elif current_folder == 'P8T1M5-B':
                    mapping[idx] = f"Ceroplastic/P8T1M5-B/P8T1M5-B-{img_num:02d}.tif"
        except ValueError:
            pass
            
    return mapping

def resolve_consensus_label(row):
    """
    Determines the final label based on the consensus column and individual votes.
    """
    tipo = str(row['TipoConsenso']).strip().lower()
    if pd.notna(row['TipoConsenso']) and tipo not in ['nan', '', 'no']:
        if 'fibra' in tipo: return 'Fibra'
        if 'pellet' in tipo: return 'Pellet'
        if 'pelicula' in tipo or 'pelcula' in tipo: return 'Pelicula'
        if 'espuma' in tipo: return 'Espuma'
        if 'fragmento' in tipo: return 'Fragmento'
        return 'Fragmento' # default microplastic fallback
        
    # Check individual votes if no consensus type is filled
    votes = [
        str(row['Melissa']).strip().lower(),
        str(row['Brayan']).strip().lower(),
        str(row['Camila']).strip().lower()
    ]
    si_votes = sum(1 for v in votes if 'si' in v or 'sí' in v or 'pued' in v or 'prob' in v)
    if si_votes >= 2:
        return 'Fragmento' # Default fallback
    return 'No Microplastico'

def get_correction_contour(x, y, w, h, thresh_img):
    """
    Finds the segmented contour in thresh_img that intersects the most with the user's manual bounding box.
    If no significant overlap is found, returns a rectangular contour representing the box itself.
    """
    contours, _ = cv2.findContours(thresh_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best_contour = None
    max_overlap = 0
    
    for c in contours:
        cx, cy, cw, ch = cv2.boundingRect(c)
        # Intersection
        ix = max(x, cx)
        iy = max(y, cy)
        iw = min(x + w, cx + cw) - ix
        ih = min(y + h, cy + ch) - iy
        if iw > 0 and ih > 0:
            overlap = iw * ih
            if overlap > max_overlap:
                max_overlap = overlap
                best_contour = c
                
    # If overlap is significant (> 20% of contour bbox or user bbox), return it
    if best_contour is not None and max_overlap > 0.2 * (w * h):
        return best_contour
        
    # Fallback to rectangular contour
    rect_contour = np.array([
        [[x, y]],
        [[x + w, y]],
        [[x + w, y + h]],
        [[x, y + h]]
    ], dtype=np.int32)
    return rect_contour

def build_ceroplastic_dataset(excel_path=None):
    """
    Loads all labeled images, extracts features from the largest segmented particle in each,
    and returns X, y arrays. Loads manual corrections from manual_corrections.json
    to override/add samples where corrections are available.
    """
    import json
    if excel_path is None:
        excel_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Ceroplastic/Clasificación microplasticos-guia.xlsx")
        
    df = pd.read_excel(excel_path, sheet_name='Resumen').iloc[1:]
    df.columns = ['Imagen', 'Melissa', 'Brayan', 'Camila', 'TipoConsenso', 'Folder']
    
    # Load manual corrections
    corrections = {}
    corrections_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "manual_corrections.json")
    if os.path.exists(corrections_path):
        try:
            with open(corrections_path, 'r') as f:
                corrections = json.load(f)
            print(f"Loaded manual corrections for {len(corrections)} files.")
        except Exception as e:
            print(f"Warning: Could not load manual corrections: {e}")
            
    # Get mapping of index to file path
    path_mapping = get_image_paths_mapping(df)
    
    # Build list of samples
    samples = []
    labels = []
    skipped = 0
    
    # Base directory for images is relative to the excel_path
    base_dir = os.path.dirname(excel_path)
    
    for idx, row in df.iterrows():
        if idx not in path_mapping:
            continue
            
        rel_path = path_mapping[idx]
        img_path = os.path.join(base_dir, rel_path)
        filename = os.path.basename(img_path)
        label = resolve_consensus_label(row)
        
        # Load and process image
        img = load_image(img_path)
        if img is None:
            print(f"Warning: Could not load image {img_path}")
            skipped += 1
            continue
            
        contours, thresh = segment_particles(img)
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # If manual corrections exist for this image, extract features for ALL corrected particles
        if filename in corrections:
            file_corrections = corrections[filename]
            if len(file_corrections) == 0:
                continue
                
            for p in file_corrections:
                p_class = p["class"]
                px, py, pw, ph = p["x"], p["y"], p["w"], p["h"]
                
                # Get contour for this corrected box
                c = get_correction_contour(px, py, pw, ph, thresh)
                
                # Extract features
                features = extract_features(c, img, hsv_img)
                samples.append(features)
                labels.append(p_class)
        else:
            # Default consensus path
            if len(contours) == 0:
                skipped += 1
                continue
                
            # Select the dominant (largest) particle as the annotated sample
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Extract features
            features = extract_features(largest_contour, img, hsv_img)
            
            samples.append(features)
            labels.append(label)
            
    X = np.array(samples)
    y = np.array(labels)
    
    print(f"Ceroplastic Dataset Built! Samples: {len(X)}, Skipped: {skipped}")
    return X, y

# Keep alias for backward compatibility
build_dataset = build_ceroplastic_dataset

def build_valerio_dataset(valerio_dir=None):
    """
    Loads all annotated images in Valerio dataset, extracts features,
    and returns X, y arrays. Caches the extracted features to a file.
    """
    if valerio_dir is None:
        valerio_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Valerio")
        
    cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "valerio_features_cache.joblib")
    if os.path.exists(cache_path):
        try:
            print("Loading Valerio features from cache...")
            cached_data = joblib.load(cache_path)
            return cached_data["X"], cached_data["y"]
        except Exception as e:
            print(f"Warning: Could not load Valerio cache, rebuilding... {e}")

    # Build dataset from scratch
    samples = []
    labels = []
    skipped = 0
    
    # Valerio categories mapping:
    category_mapping = {
        "beads": "Pellet",
        "fibers": "Fibra",
        "fragments": "Fragmento"
    }

    splits = ["train", "valid", "test"]
    for split in splits:
        split_dir = os.path.join(valerio_dir, split)
        json_path = os.path.join(split_dir, "_annotations.coco.json")
        if not os.path.exists(json_path):
            print(f"Warning: Annotation file not found: {json_path}")
            continue
            
        with open(json_path, 'r') as f:
            coco_data = json.load(f)
            
        images_by_id = {img["id"]: img for img in coco_data["images"]}
        categories = {cat["id"]: cat["name"] for cat in coco_data["categories"]}
        
        print(f"Processing Valerio {split} split ({len(coco_data['annotations'])} annotations)...")
        for ann in coco_data["annotations"]:
            img_id = ann["image_id"]
            img_info = images_by_id.get(img_id)
            if img_info is None:
                continue
                
            file_name = img_info["file_name"]
            img_path = os.path.join(split_dir, file_name)
            
            img = load_image(img_path)
            if img is None:
                skipped += 1
                continue
                
            hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            contours, thresh = segment_particles(img)
            
            bbox = ann["bbox"] # [x, y, w, h]
            x, y, w, h = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])
            
            # Find the best matching contour or fallback to bbox rect
            c = get_correction_contour(x, y, w, h, thresh)
            
            # Extract features
            features = extract_features(c, img, hsv_img)
            samples.append(features)
            
            # Get label
            raw_label = categories.get(ann["category_id"], "fragments")
            mapped_label = category_mapping.get(raw_label.lower(), "Fragmento")
            labels.append(mapped_label)
            
    X = np.array(samples)
    y = np.array(labels)
    
    print(f"Valerio Dataset Built! Samples: {len(X)}, Skipped: {skipped}")
    
    # Save cache
    try:
        joblib.dump({"X": X, "y": y}, cache_path)
        print(f"Valerio features successfully cached to {cache_path}!")
    except Exception as e:
        print(f"Warning: Could not save Valerio cache: {e}")
        
    return X, y

def build_ceroplastic_valerio_dataset(excel_path=None, valerio_dir=None):
    """
    Fuses the Ceroplastic and Valerio datasets by extracting features from both
    and concatenating them.
    """
    print("Building Ceroplastic dataset for fusion...")
    X_cero, y_cero = build_ceroplastic_dataset(excel_path)
    
    print("Building Valerio dataset for fusion...")
    X_val, y_val = build_valerio_dataset(valerio_dir)
    
    X = np.concatenate((X_cero, X_val), axis=0)
    y = np.concatenate((y_cero, y_val), axis=0)
    
    print(f"Fusion Dataset Built! Ceroplastic: {len(X_cero)}, Valerio: {len(X_val)}, Total: {len(X)}")
    return X, y

def train_and_evaluate(model_name='ceroplastic'):
    """
    Runs the dataset building for the specified model_name ('ceroplastic', 'valerio', or 'ceroplastic_valerio'),
    trains a Random Forest model with Stratified K-Fold CV,
    reports performance metrics, and saves the final trained model.
    """
    print(f"\n=== Starting Training for Model: {model_name} ===")
    
    if model_name == 'ceroplastic':
        X, y = build_ceroplastic_dataset()
        model_filename = "microplastics_model_ceroplastic.joblib"
    elif model_name == 'valerio':
        X, y = build_valerio_dataset()
        model_filename = "microplastics_model_valerio.joblib"
    elif model_name == 'ceroplastic_valerio':
        X, y = build_ceroplastic_valerio_dataset()
        model_filename = "microplastics_model_ceroplastic_valerio.joblib"
    else:
        raise ValueError(f"Unknown model_name: {model_name}")
        
    classes = np.unique(y)
    print("Target classes in dataset:", classes)
    for c in classes:
        print(f"  {c}: {sum(y == c)} samples")
        
    # Stratified K-Fold Cross Validation
    min_class_samples = min(sum(y == c) for c in classes)
    n_splits = min(5, min_class_samples)
    if n_splits < 2:
        n_splits = 2
        print(f"Warning: Smallest class has only {min_class_samples} samples. Setting CV n_splits to 2.")
        
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=42)
    
    cv_accs = []
    all_y_true = []
    all_y_pred = []
    
    print(f"\nStarting Cross Validation with {n_splits} splits...")
    rf = RandomForestClassifier(n_estimators=100, class_weight='balanced', random_state=42)
    
    for fold, (train_idx, val_idx) in enumerate(skf.split(X, y)):
        X_train, y_train = X[train_idx], y[train_idx]
        X_val, y_val = X[val_idx], y[val_idx]
        
        # Train fold model
        rf.fit(X_train, y_train)
        
        # Predict
        y_pred = rf.predict(X_val)
        
        acc = accuracy_score(y_val, y_pred)
        cv_accs.append(acc)
        
        all_y_true.extend(y_val)
        all_y_pred.extend(y_pred)
        print(f"  Fold {fold+1} Accuracy: {acc*100:.2f}%")
        
    mean_acc = np.mean(cv_accs)
    print(f"\nMean CV Accuracy: {mean_acc*100:.2f}%")
    
    print("\nClassification Report (Overall CV):")
    print(classification_report(all_y_true, all_y_pred, zero_division=0))
    
    # Train final model on all data
    print("Training final model on full dataset...")
    final_model = RandomForestClassifier(n_estimators=150, class_weight='balanced', random_state=42)
    final_model.fit(X, y)
    
    # Save the model
    model_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, model_filename)
    
    # Feature importance
    feature_names = [
        "Area", "Perimeter", "Circularity", "Aspect_Ratio", "Elongation", "Solidity", "Eccentricity",
        "Mean_B", "Mean_G", "Mean_R", "Std_B", "Std_G", "Std_R", "Mean_H", "Mean_S", "Mean_V"
    ]
    importances = final_model.feature_importances_
    sorted_idx = np.argsort(importances)[::-1]
    
    print("\nFeature Importances:")
    feature_importance_list = []
    for idx in sorted_idx:
        print(f"  {feature_names[idx]}: {importances[idx]:.4f}")
        feature_importance_list.append({
            "feature": feature_names[idx],
            "importance": float(importances[idx])
        })
        
    # Save model metadata and model
    model_data = {
        "model": final_model,
        "classes": final_model.classes_.tolist(),
        "mean_accuracy": float(mean_acc),
        "feature_importances": feature_importance_list,
        "confusion_matrix": confusion_matrix(all_y_true, all_y_pred, labels=final_model.classes_.tolist()).tolist()
    }
    
    joblib.dump(model_data, model_path)
    print(f"Final model and metrics successfully saved to {model_path}!")
    
    # Keep legacy file updated if we trained the ceroplastic model
    if model_name == 'ceroplastic':
        legacy_path = os.path.join(model_dir, "microplastics_model.joblib")
        joblib.dump(model_data, legacy_path)
        print(f"Legacy model file also updated at {legacy_path}!")
        
    return model_data

if __name__ == "__main__":
    import sys
    model_arg = 'ceroplastic'
    if len(sys.argv) > 1:
        model_arg = sys.argv[1]
    train_and_evaluate(model_arg)
