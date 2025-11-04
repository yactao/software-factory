import os, io, base64, tempfile
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
from fastapi import HTTPException

def _parse_scale(m_per_pixel: Optional[float], ratio_str: Optional[str]) -> float:
    if m_per_pixel is not None:
        return float(m_per_pixel)
    if ratio_str:
        try:
            a, b = ratio_str.split("/")
            return 1.0 / float(b)
        except Exception:
            raise HTTPException(status_code=400, detail="Format d’échelle invalide, ex 1/100")
    return float(os.environ.get("PIXEL_TO_METER_RATIO", "0.02"))

def _pdf_to_image(file_bytes: bytes) -> Image.Image:
    try:
        from pdf2image import convert_from_bytes
    except Exception as e:
        raise HTTPException(500, f"pdf2image et poppler requis: {e}")
    pages = convert_from_bytes(file_bytes)
    if not pages:
        raise HTTPException(400, "PDF vide")
    return pages[0].convert("RGB")

def _annotate_image(pil_img: Image.Image, detections: list) -> Image.Image:
    draw = ImageDraw.Draw(pil_img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None
    w, h = pil_img.size
    for d in detections:
        bb = d["bounding_box"]
        left = bb["left"] * w
        top = bb["top"] * h
        width = bb["width"] * w
        height = bb["height"] * h
        box = [left, top, left + width, top + height]
        label = f"{d['tag_name']} ({d['probability']*100:.1f}%)"
        draw.rectangle(box, outline="red", width=3)
        if font:
            draw.text((left + 5, top + 5), label, fill="red", font=font)
        else:
            draw.text((left + 5, top + 5), label, fill="red")
    return pil_img

def _pil_to_base64(pil_img: Image.Image, format_: str = "JPEG", quality: int = 90) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format=format_, quality=quality)
    return base64.b64encode(buf.getvalue()).decode("utf-8")

def _normalize_target(target):
    if isinstance(target, list):
        return target[0] if target else None
    if isinstance(target, dict):
        return target.get("name") or target.get("tag_name") or None
    if isinstance(target, str):
        return target
    return None