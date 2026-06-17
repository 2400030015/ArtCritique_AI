import numpy as np
import cv2
from sklearn.cluster import KMeans

def analyze_colors(img):
    """
    Analyzes dominant colors, brightness, contrast, saturation, warm/cool ratio,
    and dynamic range.
    
    Parameters:
    - img: OpenCV BGR image
    
    Returns:
    - result: dict containing metrics
    """
    # 1. Basic properties
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    brightness = np.mean(gray)
    contrast = np.std(gray)
    
    # 2. Dynamic Range (95th - 5th percentile of brightness)
    p95 = np.percentile(gray, 95)
    p5 = np.percentile(gray, 5)
    dynamic_range = p95 - p5

    # 3. Saturation and Warm/Cool Balance
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h_channel = hsv[:, :, 0]
    s_channel = hsv[:, :, 1]
    v_channel = hsv[:, :, 2]
    
    avg_saturation = np.mean(s_channel) / 255.0 * 100.0

    # Resize HSV to 100x100 for fast warm/cool pixel-wise scanning
    hsv_small = cv2.resize(hsv, (100, 100))
    h_small = hsv_small[:, :, 0]
    s_small = hsv_small[:, :, 1]
    v_small = hsv_small[:, :, 2]
    
    # Filter out neutral colors (very low saturation or very dark/bright values)
    colored_mask = (s_small > 25) & (v_small > 25) & (v_small < 240)
    
    h_colored = h_small[colored_mask]
    
    if len(h_colored) > 0:
        # OpenCV Hue range is 0-180. Hues 0-45 (0-90 deg) and 135-180 (270-360 deg) are Warm.
        # Hues 45-135 (90-270 deg) are Cool.
        warm_mask = (h_colored < 45) | (h_colored >= 135)
        warm_pixels = np.sum(warm_mask)
        cool_pixels = len(h_colored) - warm_pixels
        warm_ratio = (warm_pixels / len(h_colored)) * 100.0
    else:
        warm_ratio = 50.0  # neutral default

    # 4. KMeans Dominant Colors
    # Resize image to speed up KMeans
    img_small = cv2.resize(img, (150, 150))
    pixels = img_small.reshape((-1, 3))
    
    # Run KMeans
    kmeans = KMeans(
        n_clusters=5,
        random_state=42,
        n_init=5
    )
    labels = kmeans.fit_predict(pixels)
    colors_bgr = kmeans.cluster_centers_.astype(int)
    
    # Convert BGR to RGB
    colors_rgb = [ [int(c[2]), int(c[1]), int(c[0])] for c in colors_bgr ]
    
    counts = np.bincount(labels)
    percentages = (counts / counts.sum()) * 100

    # Sort dominant colors by percentage (descending)
    sorted_indices = np.argsort(percentages)[::-1]
    sorted_colors = [colors_rgb[i] for i in sorted_indices]
    sorted_percentages = [percentages[i] for i in sorted_indices]

    return {
        "brightness": float(round(brightness, 1)),
        "contrast": float(round(contrast, 1)),
        "saturation": float(round(avg_saturation, 1)),
        "warm_cool_ratio": float(round(warm_ratio, 1)),
        "dynamic_range": float(round(dynamic_range, 1)),
        "colors": sorted_colors,
        "percentages": [float(round(p, 1)) for p in sorted_percentages]
    }