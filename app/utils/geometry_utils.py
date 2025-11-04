def calculate_surface(bbox, img_width: float, img_height: float, scale_ratio: float) -> float:
    w = float(bbox.get("w", 0.0)) * float(img_width) * float(scale_ratio)
    h = float(bbox.get("h", 0.0)) * float(img_height) * float(scale_ratio)
    return float(w * h)  # m²

def calculate_perimeter(bbox, img_width: float, img_height: float, scale_ratio: float) -> float:
    w = float(bbox.get("w", 0.0)) * float(img_width) * float(scale_ratio)
    h = float(bbox.get("h", 0.0)) * float(img_height) * float(scale_ratio)
    return float(2.0 * (w + h))  # m

def adapt_bbox(bbox: dict) -> dict:
    # Custom Vision: keys possibles: width/height ou w/h
    w = bbox.get("width", bbox.get("w", 0.0))
    h = bbox.get("height", bbox.get("h", 0.0))
    try:
        w = float(w)
    except Exception:
        w = 0.0
    try:
        h = float(h)
    except Exception:
        h = 0.0
    return {"w": w, "h": h}

def analyze_global(surfaces: dict, perimeters: dict):
    """
    Retourne exactement (total_surface: float, total_perimeter: float)
    comme attendu par l'endpoint.
    """
    try:
        total_surface = float(sum(float(v) for v in surfaces.values()))
        total_perimeter = float(sum(float(v) for v in perimeters.values()))
    except Exception as e:
        # cohérent avec ton _safe_float
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Surfaces/Périmètres non numériques: {e}")
    return total_surface, total_perimeter
