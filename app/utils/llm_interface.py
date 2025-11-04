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
                            "Ta tâche est de comprendre l'intention de l'utilisateur et la traduire en anglais "
                            "et d'extraire deux informations :\n"
                            "1. intent : le type de demande parmi [surface, detection_objets, perimetre, analyse_globale].\n"
                            "2. target : la pièce ou l'objet concerné s'il est mentionné (ex: living room, kitchen, garage...).\n"
                            "Tu dois répondre UNIQUEMENT sous forme de dictionnaire JSON valide.\n"
                            "Ex: {\"intent\": \"surface\", \"target\": \"living room\"} ou {\"intent\": \"surface\", \"target\": null}."
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
