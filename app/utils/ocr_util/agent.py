# agent_gpt.py
from modules.ocr_utils import analyse_image_with_azure, extract_fields_with_gpt
from openai import AzureOpenAI
import pandas as pd
from modules.config import AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_API_VERSION, AZURE_OPENAI_DEPLOYMENT_NAME

class PlaqueAgentGPT:
    """Agent qui utilise GPT pour comprendre la requête utilisateur"""

    def __init__(self):
        self.client = AzureOpenAI(
            api_version=AZURE_OPENAI_API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
        )
        self.history = []

    def handle_request(self, image_path, user_request):
        # 1️⃣ OCR
        ocr_result = analyse_image_with_azure(image_path)
        text = ""
        for page in ocr_result.get("analyzeResult", {}).get("pages", []):
            for line in page.get("lines", []):
                text += line.get("content", "") + "\n"

        if text.strip() == "":
            return "⚠️ Aucun texte détecté sur l'image."

        # 2️⃣ Extraction des champs via GPT
        extracted_data = extract_fields_with_gpt(text)
        extracted_data["file_name"] = image_path.split("/")[-1]
        self.history.append(extracted_data)

        # 3️⃣ Compréhension de la requête par GPT
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
            model=AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {"role": "system", "content": "Tu es un assistant technique pour extraire des informations de plaques signalétiques."},
                {"role": "user", "content": prompt}
            ],
            max_completion_tokens=1000,
        )

        gpt_reply = response.choices[0].message.content.strip()

        # 4️⃣ Vérifier si GPT demande de générer un fichier
        if "GENERATE_FILE_CSV" in gpt_reply:
            output_file = "extracted_data.csv"
            pd.DataFrame([extracted_data]).to_csv(output_file, index=False)
            return f"✅ Fichier généré : {output_file}"

        elif "GENERATE_FILE_XLSX" in gpt_reply:
            output_file = "extracted_data.xlsx"
            pd.DataFrame([extracted_data]).to_excel(output_file, index=False)
            return f"✅ Fichier généré : {output_file}"

        # 5️⃣ Sinon, GPT renvoie directement la réponse
        return gpt_reply
