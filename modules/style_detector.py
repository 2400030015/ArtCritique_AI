def detect_style(brightness, contrast, edge_density=5.0):
    """
    OpenCV-based fallback heuristic for style classification.
    
    Parameters:
    - brightness: float (0-255)
    - contrast: float (0-127)
    - edge_density: float percentage (0-100)
    
    Returns:
    - style: string predicted style
    """
    if edge_density < 1.5 and (brightness > 200 or brightness < 50):
        return "Minimalism"
    elif contrast > 75 and edge_density > 15.0:
        return "Abstract"
    elif brightness < 90 and contrast > 50:
        return "Expressionism"
    elif brightness > 150 and contrast < 40:
        return "Minimalism"
    else:
        return "Realism"