import numpy as np
import cv2
import pytesseract
from PIL import Image, UnidentifiedImageError
import pillow_heif


def is_image_blurry(image_path, threshold=100.0):
    """Détecte si l'image est floue via la variance du Laplacien."""
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return True
    variance = cv2.Laplacian(image, cv2.CV_64F).var()
    return variance < threshold

def is_image_unreadable(image_path, min_brightness=40, min_contrast=20, min_size=(200, 200)):
    """
    Détermine si l'image est potentiellement illisible :
    - Faible luminosité
    - Faible contraste
    - Taille trop petite
    """
    try:
        image = Image.open(image_path).convert("L")  # Niveaux de gris
        img_np = np.array(image)

        # Vérification de taille minimale
        if image.size[0] < min_size[0] or image.size[1] < min_size[1]:
            return True

        # Luminosité moyenne
        brightness = np.mean(img_np)
        if brightness < min_brightness:
            return True

        # Contraste (écart-type)
        contrast = np.std(img_np)
        if contrast < min_contrast:
            return True

        return False
    except Exception:
        return True  # Si erreur de lecture, on considère l'image illisible


def contains_text(image_path, min_confidence=0.5, min_text_length=5):
    try:
        # Chargement image
        image = cv2.imread(image_path)
        if image is None:
            print(f"Erreur de lecture de l'image : {image_path}")
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ===== Étape 1 : Détection de région contenant du texte =====
        ret, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(binary, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text_regions = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 100]

        if not text_regions:
            return False  # Pas de régions de texte visibles

        # ===== Étape 2 : OCR avec Tesseract =====
        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(gray, config=custom_config)

        # Nettoyage du texte
        extracted_text = extracted_text.strip()
        if len(extracted_text) >= min_text_length:
            return True  # Texte significatif trouvé
        else:
            return False  # Du texte détecté mais probablement du bruit

    except Exception as e:
        print(f"Erreur dans contains_text : {e}")
        return False
import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError
import pytesseract
import pillow_heif

def contains_text_signal_plate(image_path, area_threshold=0.01, min_text_len=5):
    try:
        # Chargement de l'image (supporte HEIC)
        if image_path.lower().endswith('.heic'):
            heif_file = pillow_heif.read_heif(image_path)
            image = Image.frombytes(
                heif_file.mode,
                heif_file.size,
                heif_file.data,
                "raw",
                heif_file.mode
            )
        else:
            image = Image.open(image_path)
    except (UnidentifiedImageError, Exception) as e:
        print(f"[IMAGE OPEN ERROR] {image_path} - {e}")
        return False

    try:
        # Convertir en format OpenCV
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

        # === Étape 1 : Contour pour détecter zone texte potentielle ===
        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        img_area = image_cv.shape[0] * image_cv.shape[1]
        region_detected = any(cv2.contourArea(cnt) > area_threshold * img_area for cnt in contours)

        # === Étape 2 : OCR pour vérifier du vrai texte lisible ===
        text = pytesseract.image_to_string(image)
        has_text = len(text.strip()) >= min_text_len

        return region_detected and has_text
    except Exception as e:
        print(f"[PROCESSING ERROR] {image_path} - {e}")
        return False
