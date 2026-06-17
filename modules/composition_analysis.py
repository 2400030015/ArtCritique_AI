import cv2
import numpy as np

def analyze_composition(img):
    """
    Analyzes composition using Rule of Thirds alignment, symmetry, and visual weight.
    
    Parameters:
    - img: OpenCV BGR image
    
    Returns:
    - result: dict containing composition_score, symmetry_score, rule_of_thirds_score,
             focal_point_score, focal_point, focal_point_relative, and edge_density.
    """
    if img is None or img.size == 0:
        return {
            "composition_score": 0.0,
            "symmetry_score": 0.0,
            "rule_of_thirds_score": 0.0,
            "focal_point_score": 0.0,
            "focal_point": (0, 0),
            "focal_point_relative": (0.0, 0.0),
            "edge_density": 0.0
        }

    h_orig, w_orig = img.shape[:2]
    if h_orig < 2 or w_orig < 2:
        return {
            "composition_score": 50.0,
            "symmetry_score": 50.0,
            "rule_of_thirds_score": 50.0,
            "focal_point_score": 50.0,
            "focal_point": (0, 0),
            "focal_point_relative": (0.0, 0.0),
            "edge_density": 0.0
        }

    max_dim = 1000
    if max(h_orig, w_orig) > max_dim:
        scale = max_dim / float(max(h_orig, w_orig))
        img_resized = cv2.resize(img, (int(w_orig * scale), int(h_orig * scale)))
        h, w = img_resized.shape[:2]
    else:
        scale = 1.0
        img_resized = img
        h, w = h_orig, w_orig

    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)

    # 1. Edge Density Map for Visual Detail / Salience
    edges = cv2.Canny(gray, 50, 150)
    edge_density = np.sum(edges > 0) / (h * w)
    
    # Normalizing edge density: target is ~8-15% for standard rich compositions.
    # We map 0% to 0, 10% to 100, and 30%+ to 50 (overly busy).
    if edge_density < 0.10:
        edge_density_score = (edge_density / 0.10) * 100
    else:
        edge_density_score = max(100 - (edge_density - 0.10) * 250, 40)

    # 2. Visual Saliency & Focal Point Detection
    # We blur the edge map to find areas with a cluster of details
    blur_kernel = int(max(w, h) // 15) | 1  # must be odd
    saliency_map = cv2.GaussianBlur(edges.astype(float), (blur_kernel, blur_kernel), 0)
    
    # Add localized luminance variance to account for lighting focal points
    local_mean = cv2.blur(gray, (blur_kernel, blur_kernel))
    local_var = cv2.blur(np.square(gray.astype(float) - local_mean), (blur_kernel, blur_kernel))
    local_var_norm = cv2.normalize(local_var, None, 0, 255, cv2.NORM_MINMAX)
    
    combined_energy = saliency_map + 0.5 * local_var_norm
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(combined_energy)
    
    focal_x_resized, focal_y_resized = max_loc  # Coordinates of maximum energy on resized image
    focal_x = int(round(focal_x_resized / scale))
    focal_y = int(round(focal_y_resized / scale))

    # 3. Rule of Thirds Check
    # The 4 intersection points in the image
    third_x = [w // 3, (2 * w) // 3]
    third_y = [h // 3, (2 * h) // 3]
    intersections = [
        (third_x[0], third_y[0]),
        (third_x[1], third_y[0]),
        (third_x[0], third_y[1]),
        (third_x[1], third_y[1])
    ]

    # Calculate distance from focal point to nearest third intersection (in resized space)
    min_dist = float('inf')
    for ix, iy in intersections:
        dist = np.sqrt((focal_x_resized - ix) ** 2 + (focal_y_resized - iy) ** 2)
        if dist < min_dist:
            min_dist = dist

    # Max possible distance is from center to a corner (approximately)
    diag_length = np.sqrt(w ** 2 + h ** 2)
    
    # Map distance to score
    # Within 5% of diagonal length: perfect (100)
    # Outside: declines linearly
    if min_dist <= (diag_length * 0.05):
        thirds_score = 100.0
    else:
        thirds_score = max(100 - (min_dist / (diag_length * 0.25)) * 100, 20)

    # 4. Symmetry Analysis
    # Resize to 256x256 for uniform comparison
    resized_gray = cv2.resize(gray, (256, 256))
    
    # Horizontal flip
    flipped_h = cv2.flip(resized_gray, 1)
    diff_h = np.mean(np.abs(resized_gray.astype(float) - flipped_h.astype(float)))
    sym_h = max(100 - (diff_h / 255.0 * 200.0), 0) # scaled: 0 diff is 100, 127 diff is 0

    # Vertical flip
    flipped_v = cv2.flip(resized_gray, 0)
    diff_v = np.mean(np.abs(resized_gray.astype(float) - flipped_v.astype(float)))
    sym_v = max(100 - (diff_v / 255.0 * 200.0), 0)

    symmetry_score_val = max(sym_h, sym_v)

    # 5. Combined Composition Score
    # Balanced weights: Rule of Thirds (40%), Symmetry (30%), Edge Detail distribution (30%)
    overall_score = 0.40 * thirds_score + 0.30 * symmetry_score_val + 0.30 * edge_density_score

    return {
        "composition_score": float(round(overall_score, 1)),
        "symmetry_score": float(round(symmetry_score_val, 1)),
        "rule_of_thirds_score": float(round(thirds_score, 1)),
        "focal_point_score": float(round(thirds_score, 1)),
        "focal_point": (int(focal_x), int(focal_y)),
        "focal_point_relative": (float(round(focal_x_resized / w, 3)), float(round(focal_y_resized / h, 3))),
        "edge_density": float(round(edge_density * 100, 2))
    }

def composition_score(img):
    """Wrapper calling analyze_composition to maintain API backward compatibility."""
    return analyze_composition(img)