def generate_suggestions(
        brightness,
        contrast,
        composition
):

    tips = []

    if brightness < 100:
        tips.append(
            "Increase brightness for stronger visual impact."
        )

    if contrast < 50:
        tips.append(
            "Improve contrast to emphasize focal points."
        )

    if composition < 60:
        tips.append(
            "Improve composition using Rule of Thirds."
        )

    if len(tips) == 0:

        tips.append(
            "Artwork shows good visual balance and composition."
        )

    return tips