# ocr_utils.py
import json
import requests
import time
from modules.config import (
    AZURE_ENDPOINT, AZURE_KEY, AZURE_MODEL_ID,
    AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME
)
from openai import AzureOpenAI

# Client OCR standard
def analyse_image_with_azure(image_path):
    """Envoie l'image au Form Recognizer Azure et retourne les résultats extraits."""
    url = f"{AZURE_ENDPOINT}/formrecognizer/documentModels/{AZURE_MODEL_ID}:analyze?api-version=2023-07-31"
    headers = {
        "Content-Type": "image/jpeg",
        "Ocp-Apim-Subscription-Key": AZURE_KEY
    }
    with open(image_path, "rb") as f:
        img_data = f.read()
    response = requests.post(url, headers=headers, data=img_data)
    response.raise_for_status()
    result_url = response.headers["operation-location"]
    while True:
        result = requests.get(result_url, headers={"Ocp-Apim-Subscription-Key": AZURE_KEY}).json()
        if result.get("status") == "succeeded":
            break
        elif result.get("status") == "failed":
            raise Exception(f"Azure OCR Failed on {image_path}")
        elif result.get("content") == "":
            raise Exception(f"Azure OCR Failed on {image_path}")
        time.sleep(1)
    return result

# Client Azure OpenAI
client = AzureOpenAI(
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
)

# Extraction via GPT
def extract_fields_with_gpt(text):
    """Utiliser GPT pour extraire les entités du texte OCR et les retourner sous forme de dictionnaire."""
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

    response = client.chat.completions.create(
        model=AZURE_OPENAI_DEPLOYMENT_NAME,
        messages=[
            {"role": "system", "content": "Tu es un assistant technique d'extraction de données techniques."},
            {"role": "user", "content": prompt}
        ],
        max_completion_tokens=100000,
    )

    result = response.choices[0].message.content
    
    # Tenter de convertir le texte en dictionnaire
    try:
        extracted_data = json.loads(result)  # Transforme le str en dict Python
    except json.JSONDecodeError as e:
        print("Erreur de parsing JSON:", e)
        print("Texte brut renvoyé par GPT :\n", result)
        extracted_data  = {}
    time.sleep(1)
    return  extracted_data 
