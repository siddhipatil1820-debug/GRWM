"""
GRWM Outfit Recommendation Engine
Rule-based, explainable outfit matching based on wardrobe contents, occasion, style vibe, and weather.
"""

def generate_recommendation(wardrobe_items, occasion, style, weather='Sunny', preferred_color='Any', notes=''):
    # Categorize user's existing wardrobe items
    categorized = {
        'Tops': [],
        'Bottoms': [],
        'Dresses': [],
        'Outerwear': [],
        'Shoes': [],
        'Accessories': []
    }

    for item in wardrobe_items:
        cat = item['category']
        if cat in categorized:
            categorized[cat].append(dict(item))
        else:
            categorized['Accessories'].append(dict(item))

    # Scoring helper: give higher weight to matching style and preferred color
    def score_item(item):
        score = 0
        if preferred_color and preferred_color.lower() != 'any':
            if preferred_color.lower() in item['color'].lower():
                score += 3
        if style and style.lower() in item['style'].lower():
            score += 2
        return score

    for cat in categorized:
        categorized[cat].sort(key=score_item, reverse=True)

    matched_items = []
    breakdown = {}

    # Decide whether to use a Dress or Top + Bottom
    use_dress = False
    if occasion in ['Wedding', 'Party', 'Festival'] and categorized['Dresses']:
        use_dress = True
    elif not categorized['Tops'] and not categorized['Bottoms'] and categorized['Dresses']:
        use_dress = True

    if use_dress and categorized['Dresses']:
        dress = categorized['Dresses'][0]
        matched_items.append(dress)
        breakdown['Dress'] = f"{dress['item_name']} ({dress['color']} • {dress['style']})"
    else:
        if categorized['Tops']:
            top = categorized['Tops'][0]
            matched_items.append(top)
            breakdown['Top'] = f"{top['item_name']} ({top['color']} • {top['style']})"
        else:
            breakdown['Top'] = "Recommended: Clean button-down or relaxed tee (add to wardrobe)"

        if categorized['Bottoms']:
            bottom = categorized['Bottoms'][0]
            matched_items.append(bottom)
            breakdown['Bottom'] = f"{bottom['item_name']} ({bottom['color']} • {bottom['style']})"
        else:
            breakdown['Bottom'] = "Recommended: Tailored trousers or favorite jeans (add to wardrobe)"

    # Outerwear if cold/rainy or available and requested
    if weather in ['Cold', 'Rainy', 'Cool']:
        if categorized['Outerwear']:
            outer = categorized['Outerwear'][0]
            matched_items.append(outer)
            breakdown['Outerwear'] = f"{outer['item_name']} ({outer['color']})"
        else:
            breakdown['Outerwear'] = f"Layer with a cozy jacket or trench for {weather.lower()} weather"
    elif categorized['Outerwear'] and style in ['Formal', 'Elegant']:
        outer = categorized['Outerwear'][0]
        matched_items.append(outer)
        breakdown['Outerwear'] = f"{outer['item_name']} ({outer['color']})"

    # Shoes
    if categorized['Shoes']:
        shoes = categorized['Shoes'][0]
        matched_items.append(shoes)
        breakdown['Shoes'] = f"{shoes['item_name']} ({shoes['color']})"
    else:
        if occasion in ['College', 'Casual']:
            breakdown['Shoes'] = "Recommended: Classic white or neutral sneakers"
        elif occasion in ['Office', 'Formal']:
            breakdown['Shoes'] = "Recommended: Loafers or pointed flats/heels"
        else:
            breakdown['Shoes'] = "Recommended: Statement heels or embellished flats"

    # Accessories
    if categorized['Accessories']:
        acc = categorized['Accessories'][0]
        matched_items.append(acc)
        breakdown['Accessory'] = f"{acc['item_name']} ({acc['color']})"
    else:
        breakdown['Accessory'] = "Recommended: Minimal tote, shoulder bag, or dainty jewelry"

    # Titles and descriptions based on occasion & vibe
    title_map = {
        'College': 'Campus Ready & Effortless',
        'Office': 'Polished & Professional Elegance',
        'Party': 'Evening Statement Glow',
        'Casual': 'Everyday Chic & Relaxed',
        'Formal': 'Sleek & Sophisticated Fit',
        'Wedding': 'Festive Radiance & Grace',
        'Festival': 'Vibrant Cultural Expression'
    }

    style_tip_map = {
        'College': 'Keep accessories light and comfortable so you stay confident walking between classes.',
        'Office': 'Balanced proportions and cohesive tones make clean office ensembles look intentional.',
        'Party': 'Let one bold piece lead the look, keeping supporting items harmonized and sleek.',
        'Casual': 'Layering subtle textures elevates casual streetwear into a curated aesthetic.',
        'Formal': 'Tailored lines and streamlined silhouettes always deliver enduring timelessness.',
        'Wedding': 'Pair delicate jewelry and refined footwear to let festive silhouettes shine.',
        'Festival': 'Have fun expressing yourself with vibrant hues, rich accents, and lively styling.'
    }

    title = f"{title_map.get(occasion, 'Your Curated Fit')} — {style}"
    
    # Explainable rationale
    matched_names = [item['item_name'] for item in matched_items]
    if matched_names:
        item_summary = ", ".join(matched_names)
        explanation = (
            f"Curated directly from your wardrobe: we paired {item_summary} to achieve a {style.lower()} "
            f"aesthetic suitable for a {occasion.lower()} setting. Chosen to feel balanced and comfortable in {weather.lower()} conditions."
        )
        description = f"A customized look drawing from your personal clothing collection to suit {occasion} with a {style.lower()} attitude."
    else:
        explanation = (
            f"Your closet does not yet contain items for {occasion}. "
            f"We have generated the optimal {style.lower()} styling formula above so you know what pieces to wear or add to your closet next!"
        )
        description = f"Ideal {style} formula tailored for {occasion}."

    if preferred_color and preferred_color.lower() != 'any':
        explanation += f" Prioritized your preferred color palette ({preferred_color})."

    if notes:
        explanation += f" Adjusted with consideration for your note: '{notes}'."

    return {
        'title': title,
        'description': description,
        'explanation': explanation,
        'items': matched_items,
        'clothing_items': matched_items,
        'breakdown': breakdown,
        'style_tip': style_tip_map.get(occasion, 'Wear what makes you feel like the main character ✨')
    }
