import colorsys

def detect_color_theory(colors):
    """
    Identifies color harmony scheme (Monochromatic, Analogous, Complementary,
    Triadic, Split-Complementary) and computes a Color Harmony Score.
    
    Parameters:
    - colors: list of 5 RGB colors (each is a list/tuple of [R, G, B])
    
    Returns:
    - result: dict containing:
      - scheme: string name of color scheme
      - score: float color harmony score (0-100)
    """
    if not colors or len(colors) == 0:
        return {"scheme": "Neutral Scheme", "score": 50.0}

    # Convert RGB [0-255] to HSV (H in 0-360, S in 0-100, V in 0-100)
    hsv_list = []
    for rgb in colors:
        r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        hsv_list.append((h * 360.0, s * 100.0, v * 100.0))

    # Filter out highly desaturated or dark colors (neutral grays/whites/blacks)
    active_hues = [h for h, s, v in hsv_list if s > 15 and v > 15]

    if len(active_hues) < 2:
        # If almost all colors are neutral, it's Monochromatic
        return {"scheme": "Monochromatic Color Scheme", "score": 90.0}

    active_hues.sort()
    n = len(active_hues)

    # Calculate cyclic gaps between consecutive hues
    gaps = []
    for i in range(n):
        gap = (active_hues[(i + 1) % n] - active_hues[i]) % 360
        gaps.append(gap)

    max_gap = max(gaps) if gaps else 0
    max_gap_idx = gaps.index(max_gap) if gaps else 0

    # 1. Monochromatic Check (all active hues within 30 degrees)
    total_spread = 360 - max_gap
    if total_spread <= 30:
        return {
            "scheme": "Monochromatic Color Scheme",
            "score": float(round(100.0 - (total_spread / 30.0 * 15.0), 1)) # 85-100
        }

    # 2. Analogous Check (all active hues within 90 degrees)
    if total_spread <= 90:
        return {
            "scheme": "Analogous Color Scheme",
            "score": float(round(100.0 - ((total_spread - 30) / 60.0 * 20.0), 1)) # 80-100
        }

    # 3. Complementary Check
    # Look for a pair of hues that are roughly 180 degrees apart (150 to 210 degrees)
    complementary_pairs = []
    for i in range(n):
        for j in range(i + 1, n):
            diff = abs(active_hues[i] - active_hues[j])
            diff = min(diff, 360 - diff)
            if 150 <= diff <= 210:
                complementary_pairs.append((active_hues[i], active_hues[j], diff))

    if len(complementary_pairs) > 0:
        # Best pair deviation from 180
        best_pair = min(complementary_pairs, key=lambda x: abs(x[2] - 180.0))
        deviation = abs(best_pair[2] - 180.0)
        score = max(100.0 - (deviation / 30.0 * 25.0), 75.0) # 75-100

        # Check if it fits Split-Complementary
        # A split complementary has one hue on one side, and two hues adjacent to its complement (~150 and ~210 deg away)
        # If we have 3 or more hues and some are split complementary
        if n >= 3:
            # Check split-complementary distances
            for base in active_hues:
                has_split_1 = False
                has_split_2 = False
                for other in active_hues:
                    if other == base:
                        continue
                    diff = (other - base) % 360
                    if 130 <= diff <= 160:
                        has_split_1 = True
                    if 200 <= diff <= 230:
                        has_split_2 = True
                if has_split_1 and has_split_2:
                    return {
                        "scheme": "Split-Complementary Color Scheme",
                        "score": 92.0
                    }

        return {
            "scheme": "Complementary Color Scheme",
            "score": float(round(score, 1))
        }

    # 4. Triadic Check
    # Three hues separated by ~120 degrees (90 to 150 degrees each)
    if n >= 3:
        triadic_scores = []
        for i in range(n):
            for j in range(i + 1, n):
                for k in range(j + 1, n):
                    d1 = min(abs(active_hues[i] - active_hues[j]), 360 - abs(active_hues[i] - active_hues[j]))
                    d2 = min(abs(active_hues[j] - active_hues[k]), 360 - abs(active_hues[j] - active_hues[k]))
                    d3 = min(abs(active_hues[k] - active_hues[i]), 360 - abs(active_hues[k] - active_hues[i]))
                    
                    # Ideal values are 120, 120, 120
                    dev = abs(d1 - 120.0) + abs(d2 - 120.0) + abs(d3 - 120.0)
                    if dev < 90: # reasonable triadic fit
                        triadic_scores.append(100.0 - (dev / 90.0 * 30.0))
        
        if len(triadic_scores) > 0:
            return {
                "scheme": "Triadic Color Scheme",
                "score": float(round(max(triadic_scores), 1))
            }

    # Default fallback: Mixed/Polychromatic harmony
    return {
        "scheme": "Polychromatic Color Scheme",
        "score": float(72.5)
    }