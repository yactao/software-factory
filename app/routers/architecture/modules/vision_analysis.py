# ==========================================
# MODULE : VisionAnalyzer
# Azure Custom Vision – Détection d'objets
# ==========================================

from azure.cognitiveservices.vision.customvision.prediction import CustomVisionPredictionClient
from msrest.authentication import ApiKeyCredentials
from PIL import Image, ImageDraw, ImageFont
import io
import os
import yaml


class VisionAnalyzer:
    def __init__(self, endpoint, prediction_key, model_name, project_id, min_confidence=0.6):
        """
        Initialise le client Azure Custom Vision (mode Détection d'objets).
        """
        self.endpoint = endpoint.rstrip("/")
        self.prediction_key = prediction_key
        self.model_name = model_name
        self.project_id = project_id
        self.min_confidence = min_confidence

        try:
            credentials = ApiKeyCredentials(in_headers={"Prediction-key": self.prediction_key})
            self.client = CustomVisionPredictionClient(endpoint=self.endpoint, credentials=credentials)
            print("✅ VisionAnalyzer initialisé avec succès.")
        except Exception as e:
            print(f"❌ Erreur d'initialisation du client Custom Vision : {e}")

    # --------------------------------------------------------------------------------
    def get_image_size(self, image_path):
        """Retourne (largeur, hauteur) de l'image en pixels."""
        with Image.open(image_path) as img:
            return img.size  # (width, height)

    # --------------------------------------------------------------------------------
    @classmethod
    def from_yaml(cls, path):
        """
        Crée une instance à partir d'un fichier YAML global (clé 'azure').
        """
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        azure_cfg = cfg.get("azure")
        if not azure_cfg:
            raise ValueError("Section 'azure' introuvable dans config.yaml")

        endpoint = azure_cfg.get("endpoint")
        prediction_key = azure_cfg.get("prediction_key")
        model_name = azure_cfg.get("model_name")
        project_id = azure_cfg.get("project_id")
        min_confidence = azure_cfg.get("min_confidence", 0.6)

        if not all([endpoint, prediction_key, model_name, project_id]):
            raise ValueError("❌ Paramètres Custom Vision manquants dans config.yaml")

        return cls(
            endpoint=endpoint,
            prediction_key=prediction_key,
            model_name=model_name,
            project_id=project_id,
            min_confidence=min_confidence
        )

    # --------------------------------------------------------------------------------
    def detect_objects(self, image_path):
        """
        Envoie une image locale à Azure Custom Vision pour détecter des objets.
        Retourne une liste de dictionnaires (tag, probabilité, bounding box).
        """
        try:
            print(f"📤 Envoi de {os.path.basename(image_path)} à Azure Custom Vision...")

            with open(image_path, "rb") as image_file:
                results = self.client.detect_image(
                    project_id=self.project_id,
                    published_name=self.model_name,
                    image_data=image_file.read()
                )

            detections = []
            for pred in results.predictions:
                if pred.probability >= self.min_confidence:
                    detections.append({
                        "tag_name": pred.tag_name,
                        "probability": round(pred.probability, 3),
                        "bounding_box": {
                            "left": pred.bounding_box.left,
                            "top": pred.bounding_box.top,
                            "width": pred.bounding_box.width,
                            "height": pred.bounding_box.height
                        }
                    })

            if not detections:
                print("⚠️ Aucune détection au-dessus du seuil de confiance.")
            else:
                print(f"✅ {len(detections)} objets détectés.")

            return detections

        except Exception as e:
            print(f"❌ Erreur lors de la prédiction: {e}")
            return []

    # --------------------------------------------------------------------------------
    def detect_objects_pil(self, pil_image):
        """
        Détection à partir d'une image PIL (utile pour flux d'images en mémoire).
        """
        try:
            image_bytes = io.BytesIO()
            pil_image.save(image_bytes, format="JPEG")
            image_bytes.seek(0)

            results = self.client.detect_image(
                project_id=self.project_id,
                published_name=self.model_name,
                image_data=image_bytes.read()
            )

            detections = []
            for pred in results.predictions:
                if pred.probability >= self.min_confidence:
                    detections.append({
                        "tag_name": pred.tag_name,
                        "probability": round(pred.probability, 3),
                        "bounding_box": {
                            "left": pred.bounding_box.left,
                            "top": pred.bounding_box.top,
                            "width": pred.bounding_box.width,
                            "height": pred.bounding_box.height
                        }
                    })

            return detections

        except Exception as e:
            print(f"❌ Erreur lors de la prédiction PIL: {e}")
            return []

    # --------------------------------------------------------------------------------
    def draw_detections(self, image_path, detections):
        """
        Dessine les bounding boxes sur l'image et affiche le résultat.
        """
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            font = ImageFont.load_default()

            w, h = img.size

            for det in detections:
                bb = det["bounding_box"]
                left = bb["left"] * w
                top = bb["top"] * h
                width = bb["width"] * w
                height = bb["height"] * h

                box = [left, top, left + width, top + height]
                draw.rectangle(box, outline="red", width=3)
                label = f"{det['tag_name']} ({det['probability']*100:.1f}%)"
                draw.text((left, top - 10), label, fill="red", font=font)

            img.show()

        except Exception as e:
            print(f"❌ Erreur lors de l'affichage : {e}")
