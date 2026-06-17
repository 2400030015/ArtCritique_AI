import cv2
import numpy as np

def balance_score(img):
    """
    Measures visual balance by comparing weight distribution (luminance & edges)
    across the left/right and top/bottom axes.
    
    Parameters:
    - img: OpenCV BGR image
    
    Returns:
    - balance_score: dict containing float value from 0.0 to 100.0
    """
    if img is None or img.size == 0:
        return {
            "balance_score": 0.0
        }
    h_orig, w_orig = img.shape[:2]
    if h_orig < 2 or w_orig < 2:
        return {
            "balance_score": 100.0
        }
    max_dim = 1000
    if max(h_orig, w_orig) > max_dim:
        scale = max_dim / float(max(h_orig, w_orig))
        img_resized = cv2.resize(img, (int(w_orig * scale), int(h_orig * scale)))
        h, w = img_resized.shape[:2]
    else:
        img_resized = img
        h, w = h_orig, w_orig

    gray = cv2.cvtColor(img_resized, cv2.COLOR_BGR2GRAY)
    
    # Compute Canny edges for detail weight
    edges = cv2.Canny(gray, 50, 150)
    
    # Define half boundary indices
    half_w = w // 2
    half_h = h // 2

    # Left & Right halves
    left_lum = np.mean(gray[:, :half_w])
    right_lum = np.mean(gray[:, half_w:])
    left_edges = np.mean(edges[:, :half_w])
    right_edges = np.mean(edges[:, half_w:])

    # Top & Bottom halves
    top_lum = np.mean(gray[:half_h, :])
    bottom_lum = np.mean(gray[half_h:, :])
    top_edges = np.mean(edges[:half_h, :])
    bottom_edges = np.mean(edges[half_h:, :])

    # Calculate weights (60% luminance, 40% edges/texture details)
    weight_left = 0.6 * left_lum + 0.4 * (left_edges * 255.0 / 100.0)
    weight_right = 0.6 * right_lum + 0.4 * (right_edges * 255.0 / 100.0)
    
    weight_top = 0.6 * top_lum + 0.4 * (top_edges * 255.0 / 100.0)
    weight_bottom = 0.6 * bottom_lum + 0.4 * (bottom_edges * 255.0 / 100.0)

    # Calculate balance scores
    max_lr = max(weight_left + weight_right, 1.0)
    lr_balance = 100.0 - (abs(weight_left - weight_right) / max_lr * 100.0)

    max_tb = max(weight_top + weight_bottom, 1.0)
    tb_balance = 100.0 - (abs(weight_top - weight_bottom) / max_tb * 100.0)

    # Average left-right and top-bottom balance
    overall_balance = 0.5 * lr_balance + 0.5 * tb_balance

    return {
        "balance_score": float(round(overall_balance, 2))
    }