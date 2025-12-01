import os
import csv
import time
import json
import tempfile
from typing import Dict, Any

import requests
import pandas as pd
import numpy as np
import cv2
import pytesseract
from PIL import Image, UnidentifiedImageError
import pillow_heif
from openai import AzureOpenAI

from app.core.config import (
    PLAQUE_AZURE_OCR_ENDPOINT,
    PLAQUE_AZURE_OCR_KEY,
    PLAQUE_AZURE_OCR_MODEL_ID,
    PLAQUE_AZURE_OAI_ENDPOINT,
    PLAQUE_AZURE_OAI_KEY,
    PLAQUE_AZURE_OAI_API_VERSION,
    PLAQUE_AZURE_OAI_DEPLOYMENT,
    PLAQUE_METADATA_FILE,
    PLAQUE_CLIENT_NAME,
)


# ===== Fonctions utilitaires OCR / qualité image (copiées de ton code) =====

def is_image_blurry(image_path, threshold=100.0) -> bool:
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return True
    variance = cv2.Laplacian(image, cv2.CV_64F).var()
    return variance < threshold


def is_image_unreadable(image_path, min_brightness=40, min_contrast=20, min_size=(200, 200)) -> bool:
    try:
        image = Image.open(image_path).convert("L")
        img_np = np.array(image)

        if image.size[0] < min_size[0] or image.size[1] < min_size[1]:
            return True

        brightness = float(np.mean(img_np))
        if brightness < min_brightness:
            return True

        contrast = float(np.std(img_np))
        if contrast < min_contrast:
            return True

        return False
    except Exception:
        return True


def contains_text(image_path, min_confidence=0.5, min_text_length=5) -> bool:
    try:
        image = cv2.imread(image_path)
        if image is None:
            print(f"Erreur de lecture de l'image : {image_path}")
            return False

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_OTSU | cv2.THRESH_BINARY_INV)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        text_regions = [cv2.boundingRect(cnt) for cnt in contours if cv2.contourArea(cnt) > 100]
        if not text_regions:
            return False

        custom_config = r'--oem 3 --psm 6'
        extracted_text = pytesseract.image_to_string(gray, config=custom_config)
        extracted_text = extracted_text.strip()
        return len(extracted_text) >= min_text_length

    except Exception as e:
        print(f"Erreur dans contains_text : {e}")
        return False


def contains_text_signal_plate(image_path, area_threshold=0.01, min_text_len=5) -> bool:
    try:
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
        image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)

        _, thresh = cv2.threshold(gray, 180, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        img_area = image_cv.shape[0] * image_cv.shape[1]
        region_detected = any(cv2.contourArea(cnt) > area_threshold * img_area for cnt in contours)

        text = pytesseract.image_to_string(image)
        has_text = len(text.strip()) >= min_text_len

        return region_detected and has_text
    except Exception as e:
        print(f"[PROCESSING ERROR] {image_path} - {e}")
        return False


# ===== Form Recognizer + GPT extraction (copié de ton ocr_utils) =====

def analyse_image_with_azure(image_path: str) -> Dict[str, Any]:
    url = f"{PLAQUE_AZURE_OCR_ENDPOINT}/formrecognizer/documentModels/{PLAQUE_AZURE_OCR_MODEL_ID}:analyze?api-version=2023-07-31"
    headers = {
        "Content-Type": "image/jpeg",
        "Ocp-Apim-Subscription-Key": PLAQUE_AZURE_OCR_KEY,
    }
    with open(image_path, "rb") as f:
        img_data = f.read()

    response = requests.post(url, headers=headers, data=img_data)
    response.raise_for_status()
    result_url = response.headers["operation-location"]

    while True:
        result = requests.get(result_url, headers={"Ocp-Apim-Subscription-Key": PLAQUE_AZURE_OCR_KEY}).json()
        status = result.get("status")
        if status == "succeeded":
            break
        elif status == "failed":
            raise Exception(f"Azure OCR Failed on {image_path}")
        time.sleep(1)
    return result


plaque_llm_client = AzureOpenAI(
    api_version=PLAQUE_AZURE_OAI_API_VERSION,
    azure_endpoint=PLAQUE_AZURE_OAI_ENDPOINT,
    api_key=PLAQUE_AZURE_OAI_KEY,
)


def extract_fields_with_gpt(text: str) -> Dict[str, Any]:
    prompt = f"""
    À partir du texte suivant extrait d'une plaque signalétique, extrait les informations suivantes :
    - Marque
    - Modèle
    - Numéro de série
    - Date de fabrication
    - Tension (V)
    - Fréquence (Hz)
    - Type de gaz
    - Charge de gaz
    - Pression haute (HP)
    - Pression basse (LP)
    - Pays de fabrication
    - Type de matériel (Chauffage ou Climatisation)

    Retourne la réponse au format JSON.
    Si le texte est vide retourne None.

    Texte OCR :
    {text}
    """

    response = plaque_llm_client.chat.completions.create(
        model=PLAQUE_AZURE_OAI_DEPLOYMENT,
        messages=[
            {"role": "system", "content": "Tu es un assistant technique d'extraction de données techniques."},
            {"role": "user", "content": prompt},
        ],
        max_completion_tokens=1000,
    )

    result = response.choices[0].message.content
    try:
        extracted_data = json.loads(result)
    except json.JSONDecodeError as e:
        print("Erreur de parsing JSON:", e)
        print("Texte brut renvoyé par GPT :\n", result)
        extracted_data = {}
    time.sleep(1)
    return extracted_data


# === Gestion metadata CSV (reprend ton init_metadata_file / append_metadata) ===

def init_metadata_file():
    metadata_file = PLAQUE_METADATA_FILE
    metadata_dir = os.path.dirname(metadata_file)
    if metadata_dir and not os.path.exists(metadata_dir):
        os.makedirs(metadata_dir, exist_ok=True)

    if not os.path.exists(metadata_file):
        with open(metadata_file, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Client", "Ville", "Code Magasin",
                "Type de matériel", "N° Série", "Marque",
                "Type de gaz", "Charge de gaz", "Pression haute (HP)",
                "Pression basse (LP)", "Modèle", "Date Fab",
                "Statut OCR", "Fichier"
            ])


def append_metadata(fields: Dict[str, Any], client: str, ville: str, code_magasin: str,
                    statut_ocr: str, filename: str):
    metadata_file = PLAQUE_METADATA_FILE
    with open(metadata_file, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            client,
            ville,
            code_magasin,
            fields.get("Type de matériel", ""),
            fields.get("Numéro de série", ""),
            fields.get("Marque", ""),
            fields.get("Type de gaz", ""),
            fields.get("Charge de gaz", ""),
            fields.get("Pression haute (HP)", ""),
            fields.get("Pression basse (LP)", ""),
            fields.get("Modèle", ""),
            fields.get("Date de fabrication", ""),
            statut_ocr,
            filename,
        ])


# === Agent plaques (reprend ta classe PlaqueAgentGPT) ===

class PlaqueAgentGPT:
    def __init__(self) -> None:
        self.client = plaque_llm_client
        self.history = []

    def handle_request(self, image_path: str, user_request: str) -> str:
        # 1) OCR Azure
        ocr_result = analyse_image_with_azure(image_path)
        text = ""
        for page in ocr_result.get("analyzeResult", {}).get("pages", []):
            for line in page.get("lines", []):
                text += line.get("content", "") + "\n"

        if text.strip() == "":
            return "⚠️ Aucun texte détecté sur l'image."

        # 2) Extraction des champs via GPT
        extracted_data = extract_fields_with_gpt(text)
        extracted_data["file_name"] = os.path.basename(image_path)
        self.history.append(extracted_data)

        # 3) Compréhension de la requête via GPT
        prompt = f"""
Tu es un assistant technique spécialisé pour plaques signalétiques.
Voici les données extraites de l'image : {extracted_data}

Voici la requête de l'utilisateur :
\"{user_request}\"

Instructions :
1. Si l'utilisateur demande un fichier CSV ou Excel, répond uniquement :
"GENERATE_FILE_CSV" ou "GENERATE_FILE_XLSX".
2. Si l'utilisateur demande une ou plusieurs informations spécifiques, renvoie uniquement ces champs sous forme claire.
3. Si l'utilisateur demande toutes les informations, renvoie toutes les données de façon lisible.
4. Répond toujours de façon naturelle.
"""

        response = self.client.chat.completions.create(
            model=PLAQUE_AZURE_OAI_DEPLOYMENT,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant technique pour extraire des informations de plaques signalétiques."
                },
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=1000,
        )

        gpt_reply = response.choices[0].message.content.strip()

        # 4) Gestion CSV / XLSX
        if "GENERATE_FILE_CSV" in gpt_reply:
            init_metadata_file()
            output_file = "Resultats/extracted_data.csv"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            pd.DataFrame([extracted_data]).to_csv(output_file, index=False)
            return f"✅ Fichier généré : {output_file}"

        if "GENERATE_FILE_XLSX" in gpt_reply:
            init_metadata_file()
            output_file = "Resultats/extracted_data.xlsx"
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            pd.DataFrame([extracted_data]).to_excel(output_file, index=False)
            return f"✅ Fichier généré : {output_file}"

        # 5) Sinon, renvoyer directement la réponse GPT
        return gpt_reply


# Helper pour utiliser l’agent à partir d’un binaire FastAPI
def run_plaque_agent_on_bytes(image_bytes: bytes, filename: str, user_request: str) -> str:
    """Écrit les bytes dans un fichier temp, lance l'agent, et supprime le temp."""
    suffix = os.path.splitext(filename or "upload.jpg")[1] or ".jpg"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(image_bytes)
        tmp_path = tmp.name

    try:
        agent = PlaqueAgentGPT()
        return agent.handle_request(tmp_path, user_request)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass
