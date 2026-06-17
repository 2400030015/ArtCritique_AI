def generate_verdict(
    rating,
    style,
    composition,
    balance
):

    verdict = f"""

Artwork Style:
{style}

Overall Rating:
{rating}/10

Composition Score:
{composition}

Balance Score:
{balance}

Professional Analysis:

The artwork demonstrates
strong artistic qualities
and visual consistency.

The composition effectively
guides viewer attention.

The balance between
elements creates visual
stability and aesthetic
appeal.

"""

    return verdict