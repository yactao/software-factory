from PIL import ImageDraw, ImageFont

def annotate_image(image, detections, color="red", font_size=20):
    """
    Dessine les bounding boxes et les labels sur une image.
    
    Args:
        image (PIL.Image): L'image originale.
        detections (list): Liste de détections (chaque élément contient 'tag_name' et 'bounding_box').
        color (str): Couleur du rectangle (par défaut rouge).
        font_size (int): Taille du texte du label.
    
    Returns:
        PIL.Image: Image annotée.
    """
    draw = ImageDraw.Draw(image)

    # Essaie de charger une police claire et lisible
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    for d in detections:
        bbox = d["bounding_box"]
        tag = d["tag_name"]

        # Conversion du format Custom Vision (0–1) en pixels
        x0 = bbox["left"] * image.width
        y0 = bbox["top"] * image.height
        x1 = x0 + bbox["width"] * image.width
        y1 = y0 + bbox["height"] * image.height

        # Dessin du rectangle
        draw.rectangle([x0, y0, x1, y1], outline=color, width=3)

        # Label au-dessus du rectangle
        text = f"{tag}"
        text_size = draw.textbbox((x0, y0), text, font=font)
        draw.rectangle([text_size[0], text_size[1], text_size[2], text_size[3]], fill=color)
        draw.text((x0, y0 - font_size), text, fill="white", font=font)

    return image
