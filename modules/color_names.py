def get_color_name(rgb):
    """
    Finds the closest named color to the input RGB tuple.
    
    Parameters:
    - rgb: tuple of (R, G, B)
    
    Returns:
    - color_name: string representing name of closest color.
    """
    r, g, b = rgb

    # Standard color map
    color_map = {
        "Red": (255, 0, 0),
        "Crimson": (220, 20, 60),
        "Deep Pink": (255, 20, 147),
        "Light Pink": (255, 182, 193),
        "Orange": (255, 165, 0),
        "Gold": (255, 215, 0),
        "Yellow": (255, 255, 0),
        "Lavender": (230, 230, 250),
        "Magenta": (255, 0, 255),
        "Purple": (128, 0, 128),
        "Violet": (138, 43, 226),
        "Indigo": (75, 0, 130),
        "Blue": (0, 0, 255),
        "Sky Blue": (135, 206, 235),
        "Cyan": (0, 255, 255),
        "Teal": (0, 128, 128),
        "Turquoise": (64, 224, 208),
        "Forest Green": (34, 139, 34),
        "Green": (0, 128, 0),
        "Lime Green": (50, 205, 50),
        "Olive": (128, 128, 0),
        "Beige": (245, 245, 220),
        "Wheat": (245, 222, 179),
        "Tan": (210, 180, 140),
        "Brown": (139, 69, 19),
        "Maroon": (128, 0, 0),
        "Navy": (0, 0, 128),
        "White": (255, 255, 255),
        "Alabaster": (240, 240, 230),
        "Silver": (192, 192, 192),
        "Gray": (128, 128, 128),
        "Charcoal": (54, 69, 79),
        "Black": (0, 0, 0),
        "Coral": (255, 127, 80),
        "Salmon": (250, 128, 114)
    }

    # Find color with minimum Euclidean distance
    min_dist = float('inf')
    closest_name = "Mixed Tone"

    for name, target_rgb in color_map.items():
        dist = (r - target_rgb[0])**2 + (g - target_rgb[1])**2 + (b - target_rgb[2])**2
        if dist < min_dist:
            min_dist = dist
            closest_name = name

    return closest_name