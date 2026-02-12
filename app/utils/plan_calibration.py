# ==========================================
# Calibration automatique des plans 2D (aligné sur aina vision architecture/modules/calibration.py)
# Utilise la détection de la plus longue ligne (Hough) pour calculer le ratio m/pixel.
# ==========================================

from typing import Optional

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False


def get_scale_ratio(image_path: str, real_length_m: float) -> Optional[float]:
    """
    Calcule le ratio mètre/pixel en détectant la plus longue ligne du plan.
    Même logique que PlanCalibration dans aina vision architecture/modules/calibration.py.

    :param image_path: chemin vers l'image du plan (jpg, png, etc.)
    :param real_length_m: longueur réelle de référence en mètres
    :return: scale_ratio (m/pixel) ou None si échec (pas de lignes, pas de cv2, etc.)
    """
    if not _HAS_CV2 or real_length_m <= 0:
        return None

    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None

        edges = cv2.Canny(img, 50, 150)
        lines = cv2.HoughLinesP(
            edges, 1, np.pi / 180,
            threshold=100, minLineLength=50, maxLineGap=10
        )
        if lines is None or len(lines) == 0:
            return None

        max_len = 0.0
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            if length > max_len:
                max_len = length

        if max_len <= 0:
            return None

        return float(real_length_m) / max_len
    except Exception:
        return None
