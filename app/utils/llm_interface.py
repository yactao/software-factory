# modules/llm_interface.py

from openai import AzureOpenAI
import logging
import json


class LLMInterface:
    def __init__(self, endpoint: str, api_key: str, deployment: str, model: str = None):
        """
        Initialise le client Azure OpenAI.
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment = deployment
        self.model = model or deployment  # fallback si model non fourni

        # Création du client Azure
        self.client = AzureOpenAI(
            api_version="2024-12-01-preview",  # adapte selon ton Azure
            azure_endpoint=self.endpoint,
            api_key=self.api_key 
        )

        # Logger
        self.logger = logging.getLogger("LLMInterface")
        logging.basicConfig(level=logging.INFO)
        self.logger.info(f"LLM initialisé avec le déploiement : {deployment}")

    def analyze_request(self, user_input: str):
        """
        Envoie la requête utilisateur au modèle Azure OpenAI pour analyse.
        Retour : dict avec clés 'intent' et 'target'
        """
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Tu es un assistant d'analyse de plans architecturaux multilangue. "
                            "Extrait deux champs en JSON uniquement : intent et target.\n"
                            "1. intent : un parmi [surface, perimetre, analyse_globale, count, detection_objets].\n"
                            "2. target : nom de la pièce/type si demandé (ex: Living room, Kitchen), ou null.\n"
                            "Règles : 'surface totale' / 'périmètre total' -> intent=surface ou perimetre, target=null.\n"
                            "Si l'utilisateur demande le NOMBRE (combien de X, how many X) -> intent=count, target=nom de la pièce en anglais (Kitchen, Living room, Room, Bathroom, Garage, etc.).\n"
                            "Exemples : \"donne moi la surface total\" -> {\"intent\": \"surface\", \"target\": null}\n"
                            "\"combien de kitchen j'ai dans mon plan\" -> {\"intent\": \"count\", \"target\": \"Kitchen\"}\n"
                            "\"combien de chambres\" -> {\"intent\": \"count\", \"target\": \"Room\"}\n"
                            "\"surface du salon\" -> {\"intent\": \"surface\", \"target\": \"Living room\"}\n"
                            "\"analyse globale\" -> {\"intent\": \"analyse_globale\", \"target\": null}"
                        )
                    },
                    {"role": "user", "content": user_input}
                ],
                max_completion_tokens=5000
            )

            # --- Récupérer le contenu ---
            response_content = response.choices[0].message.content

            # --- Forcer un string si ce n'est pas une string ---
            if not isinstance(response_content, str):
                response_text = json.dumps(response_content)
            else:
                response_text = response_content.strip()

            self.logger.info(f"Réponse brute du modèle : {response_text}")

            # --- Parsing JSON ---
            try:
                parsed = json.loads(response_text)
                intent = parsed.get("intent", "analyse_globale")
                target = parsed.get("target")
                # Forcer target à être string ou None
                if isinstance(target, list):
                    target = target[0] if target else None
                elif not isinstance(target, str):
                    target = None
                return {"intent": intent, "target": target}
            except (json.JSONDecodeError, TypeError):
                # Fallback si JSON invalide
                self.logger.warning("Réponse non-JSON reçue, fallback en texte brut.")
                return {"intent": str(response_text).lower(), "target": None}

        except Exception as e:
            self.logger.error(f"Erreur d'appel LLM: {e}")
            return {"intent": "analyse_globale", "target": None}
