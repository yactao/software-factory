def generate_response(intent, detections, surfaces, perimeters, img_height, scale_ratio, target=None):
    """
    Génère la réponse finale à afficher dans Streamlit.
    """
    try:
        # === Cas 1 : demande de surface ===
        if intent == "surface":
            if target and target in surfaces:
                surface = surfaces[target]
                return f"La surface de la pièce **{target}** est estimée à **{surface:.2f} m²**."
            elif len(surfaces) == 1:
                # Une seule pièce détectée : afficher directement
                key = list(surfaces.keys())[0]
                return f"La surface de la pièce **{key}** est estimée à **{surfaces[key]:.2f} m²**."
            else:
                return "Je n’ai pas trouvé cette pièce sur le plan. Vérifie le nom ou reformule ta demande."

        # === Cas 2 : demande de périmètre ===
        elif intent == "perimetre":
            if target and target in perimeters:
                perimeter = perimeters[target]
                return f"Le périmètre de la pièce **{target}** est estimé à **{perimeter:.2f} m**."
            elif len(perimeters) == 1:
                key = list(perimeters.keys())[0]
                return f"Le périmètre de la pièce **{key}** est estimé à **{perimeters[key]:.2f} m**."
            else:
                return "Je n’ai pas trouvé cette pièce sur le plan."

        # === Cas 3 : demande globale ===
        elif intent == "analyse_globale":
            result_lines = [f"Nombre total de pièces détectées : {len(surfaces)}\n"]
            for tag, surf in surfaces.items():
                peri = perimeters.get(tag, 0)
                result_lines.append(f"• **{tag}** — Surface : {surf:.2f} m² | Périmètre : {peri:.2f} m")
            return "\n".join(result_lines)

        # === Cas 4 : autre cas non reconnu ===
        else:
            return "Je n’ai pas compris la demande. Peux-tu reformuler ?"

    except Exception as e:
        return f"Erreur lors de la génération de la réponse : {e}"
