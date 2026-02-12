# ==========================================
# response_generator.py – aligné sur aina vision architecture
# Résumé puis reformulation automatique via Azure OpenAI.
# ==========================================

from openai import AzureOpenAI
from typing import Any, Dict, Optional


class ResponseGenerator:
    def __init__(self, endpoint: str, api_key: str, deployment: str):
        """
        Génère des réponses finales basées sur les résultats du calcul.
        Reformule le résumé via Azure OpenAI pour une réponse naturelle.
        """
        self.endpoint = endpoint
        self.api_key = api_key
        self.deployment = deployment
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version="2024-12-01-preview",
        )

    def generate_response(
        self,
        intent: str,
        target: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> str:
        if not data:
            return "❌ Aucun résultat calculé."

        mapping = {
            "salon": "Living room",
            "cuisine": "Kitchen",
            "garage": "Garage",
            "salle de bain": "Bathroom",
            "chambre": "Room",
            "wc": "WC",
            "mur": "wall",
        }
        count_key_variants: Dict[str, list] = {
            "kitchen": ["Kitchen", "Kit room", "kit room"],
            "living room": ["Living room"],
            "room": ["Room", "room"],
            "bathroom": ["Bathroom", "bathroom"],
            "garage": ["Garage", "garage"],
            "wall": ["wall", "Wall"],
        }

        if target:
            t = (target or "").strip().lower()
            if t in ("total", "totale", "totales", "global", "globale"):
                normalized_target = "total"
            else:
                normalized_target = mapping.get(t, target)
        else:
            normalized_target = None

        surfaces = data.get("surfaces", {})
        perimeters = data.get("perimeters", {})
        counts = data.get("counts", {})
        room_surfaces = {k: v for k, v in surfaces.items() if k != "total"}
        room_perimeters = {k: v for k, v in perimeters.items() if k != "total"}

        def safe_get(d: dict, key: Optional[str]):
            if key is None:
                return None
            return d.get(key) or (d.get(key.capitalize()) if isinstance(key, str) else None)

        summary: Optional[str] = None

        if intent == "surface":
            if normalized_target == "total" or normalized_target is None:
                total_surface = surfaces.get("total") or sum(room_surfaces.values())
                summary = f"La surface totale du plan est d'environ {total_surface:.2f} m²."
            else:
                value = safe_get(surfaces, normalized_target)
                if value is None:
                    available = ", ".join(room_surfaces.keys()) if room_surfaces else "aucune"
                    return f"❌ Impossible de trouver la surface de '{target}'. Pièces disponibles : {available}."
                summary = f"La surface de '{normalized_target}' est d'environ {value:.2f} m²."

        elif intent == "perimetre":
            if normalized_target == "total" or normalized_target is None:
                total_perimeter = perimeters.get("total") or sum(room_perimeters.values())
                summary = f"Le périmètre total du plan est estimé à {total_perimeter:.2f} mètres."
            else:
                value = safe_get(perimeters, normalized_target)
                if value is None:
                    available = ", ".join(room_perimeters.keys()) if room_perimeters else "aucun"
                    return f"❌ Impossible de calculer le périmètre de '{target}'. Pièces disponibles : {available}."
                summary = f"Le périmètre de '{normalized_target}' est estimé à {value:.2f} mètres."

        elif intent == "analyse_globale":
            s = surfaces.get("total") or sum(room_surfaces.values())
            p = perimeters.get("total") or sum(room_perimeters.values())
            summary = f"L'analyse globale indique une surface totale de {s:.2f} m² et un périmètre total de {p:.2f} mètres."

        elif intent == "count":
            if not normalized_target:
                total_count = sum(counts.values())
                summary = f"Il y a {total_count} zone(s) / pièce(s) détectée(s) sur le plan."
            else:
                summary = None
                t_lower = (normalized_target or "").lower().replace(" ", "")
                found_count = 0
                matched_name = None
                for key in counts:
                    if key.lower().replace(" ", "") == t_lower or t_lower in key.lower().replace(" ", ""):
                        found_count += counts[key]
                        matched_name = key
                if matched_name is not None:
                    summary = f"Vous avez {found_count} {matched_name}(s) dans le plan." if found_count != 1 else f"Vous avez 1 {matched_name} dans le plan."
                else:
                    for variant_key, keys_to_try in count_key_variants.items():
                        if variant_key in (target or "").lower() or (target or "").lower() in variant_key:
                            found_count = sum(counts.get(k, 0) for k in keys_to_try)
                            if found_count > 0:
                                label = normalized_target or target
                                summary = f"Vous avez {found_count} {label}(s) dans le plan."
                            break
                    if summary is None:
                        available = ", ".join(counts.keys()) if counts else "aucune"
                        return f"Aucune pièce de type « {target} » trouvée. Types détectés : {available}."

        else:
            summary = "❌ Je n'ai pas compris l'intention de la demande."

        if summary is None:
            return "❌ Aucun résumé généré."

        # Reformulation avec Azure OpenAI (comme aina vision architecture)
        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[
                    {
                        "role": "system",
                        "content": "Tu es un assistant multilanguage professionnel en architecture. Reformule la réponse de manière claire et naturelle, sans ajouter d'astérisques ni de markdown.",
                    },
                    {"role": "user", "content": summary},
                ],
                max_completion_tokens=150,
            )
            message = (response.choices[0].message.content or "").strip()
            return message or summary
        except Exception as e:
            return f"⚠️ Erreur lors de la génération de réponse : {e}\n\nRésumé : {summary}"


# Compatibilité avec vision.py (API Vision classique) : fonction standalone
_default_generator: Optional[ResponseGenerator] = None


def _get_default_generator() -> ResponseGenerator:
    global _default_generator
    if _default_generator is None:
        from app.core.config import (
            AZURE_OAI_ENDPOINT,
            AZURE_OAI_KEY,
            AZURE_OAI_DEPLOYMENT,
        )
        _default_generator = ResponseGenerator(
            endpoint=AZURE_OAI_ENDPOINT,
            api_key=AZURE_OAI_KEY,
            deployment=AZURE_OAI_DEPLOYMENT,
        )
    return _default_generator


def generate_response(
    intent: str,
    detections: Any,
    surfaces: Dict[str, float],
    perimeters: Dict[str, float],
    counts: Optional[Dict[str, int]] = None,
    img_height: Any = None,
    scale_ratio: Any = None,
    target: Optional[str] = None,
) -> str:
    """
    Signature legacy pour vision.py. Délègue à ResponseGenerator.
    """
    data = {
        "surfaces": surfaces,
        "perimeters": perimeters,
        "counts": counts or {},
    }
    return _get_default_generator().generate_response(
        intent=intent,
        target=target,
        data=data,
    )
