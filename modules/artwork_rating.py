def calculate_rating(composition, color, contrast, aesthetic):
    """
    Calculates overall rating on a 0-10 scale.
    
    Parameters:
    - composition: float (0-100)
    - color: float (0-100)
    - contrast: float (0-100)
    - aesthetic: float (0-100)
    
    Returns:
    - rating: float (0.0 to 10.0)
    """
    # Average the four scores and scale to 10
    total = float(composition) + float(color) + float(contrast) + float(aesthetic)
    rating = total / 4.0
    return round(rating / 10.0, 1)