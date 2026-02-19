from typing import List, Dict

from PIL import Image, ImageDraw, ImageFont


def draw_architecture_annotations(
    pil_img: "Image.Image", annotations: List[Dict]
) -> "Image.Image":
    """
    Dessine les bounding boxes (bbox_px) et labels sur une copie de l'image.
    annotations : liste avec au moins
      - label: str
      - bbox_px: {x, y, w, h}
    """
    img = pil_img.copy()
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.load_default()
    except Exception:  # pragma: no cover
        font = None

    for ann in annotations:
        bbox_px = ann.get("bbox_px") or {}
        label = ann.get("label") or ""
        # Accepter float (vrais pixels) et arrondir pour le dessin
        x = int(round(float(bbox_px.get("x", 0))))
        y = int(round(float(bbox_px.get("y", 0))))
        w = int(round(float(bbox_px.get("w", 0))))
        h = int(round(float(bbox_px.get("h", 0))))
        if w <= 0 or h <= 0:
            continue
        box = [x, y, x + w, y + h]
        draw.rectangle(box, outline="red", width=3)
        if label:
            text_pos = (x, max(0, y - 12))
            if font:
                draw.text(text_pos, label, fill="red", font=font)
            else:
                draw.text(text_pos, label, fill="red")

    return img

