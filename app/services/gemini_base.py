import os
import time, random, json
import google.generativeai as genai
from fastapi import HTTPException
from typing import Dict, Any
from ..core.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL_CHAT,
    GEMINI_TEMPERATURE,
    GEMINI_MAX_OUTPUT_TOKENS,
    GEMINI_RETRIES,
)

def _configure_gemini():
    if not GEMINI_API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY non configurée.")
    genai.configure(api_key=GEMINI_API_KEY)

    max_out = int(GEMINI_MAX_OUTPUT_TOKENS)
    temperature = float(GEMINI_TEMPERATURE)

    model = genai.GenerativeModel(
        GEMINI_MODEL_CHAT,
        system_instruction=(
            "Tu es un assistant d’entreprise pour un système RAG. Tu réponds EXCLUSIVEMENT au CONTEXTE fourni. "
            "Si une information n’y figure pas, dis-le et n’invente rien.\n\n"
            "Langue: réponds dans la langue de la question.\n\n"
            "Références: NE METS AUCUNE référence dans le texte (pas de [n], pas de liens). "
            "À la place, renvoie dans le JSON la liste des numéros des SOURCES effectivement utilisées.\n\n"
            "Mise en forme (TEXTE BRUT, PAS DE MARKDOWN):\n"
            "• PAS d’astérisques, PAS de balises markdown, PAS d’emojis, Pas de ponctuation inutile, PAS de tiret court ' - ' au début.\n"
            "• Structure ton output en sections claires avec des titres en MAJUSCULES suivis d'une ligne d'underscores.\n"
            "• Paragraphes complets, listes autorisées mais  sans utiliser un tiret court ' - ' au début de la ligne ou un point.\n\n"
            "• PAS de tirets numérotés, PAS de lettres entre parenthèses, PAS de puces  même pour les sous-listes.\n"
            "• Les titres doivent pas etre tout en majuscules.\n"
            "• Pas de Titres\n\n"
            "• Utilise un langage formel et professionnel adapté au contexte d'entreprise.\n\n" \
            "Instructions pour la réponse:\n"
            "• Fournis une synthèse claire et concise en 6 à 8 phrases.\n"
            "• Utilise des reponses en liste c'est il s'agit de donner une liste de choses ,mais sans utiliser de tirets ou puces.\n"
            "• Ne fais PAS de références dans le texte (pas de [n], pas de liens).\n"
            "• Si le contexte ne permet pas de répondre, dis-le clairement.\n\n"
            "• Réponds de manière concise et précise juste à la demande de l'utilisateur depuis ce qu'il a fourni et le contexte n'ajoute pas d'informations depuis le contexte qui ne sont pas intéressantes a la question.\n\n"
            "Sortie en JSON STRICT:\n"
            "{\n"
            '  "answer": "6 à 8 phrases synthétiques, SANS AUCUNE référence dans le texte et donne de l\'information factuelle.",\n'
            '  "uses_context": true|false,\n'
            '  "used_sources": [ <entiers correspondant aux numéros des SOURCES utilisées, ex: 1,3,4> ]\n'
            "}\n"
        ),
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_out,
            "response_mime_type": "application/json",
        },
    )
    return model


def _configure_gemini_finance():
    if not GEMINI_API_KEY:
        raise HTTPException(500, "GEMINI_API_KEY non configurée.")
    genai.configure(api_key=GEMINI_API_KEY)

    max_out = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS_FIN", os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "1400")))
    temperature = float(os.getenv("GEMINI_TEMPERATURE_FIN", os.getenv("GEMINI_TEMPERATURE", "0.2")))

    model = genai.GenerativeModel(
        GEMINI_MODEL_CHAT,
        system_instruction=(
            "Tu es un assistant financier. Réponds en français a la question demandée en TEXTE BRUT (pas de Markdown, pas d’astérisques, pas d’emojis). "
            "Si tu fais des totaux, indique clairement  et garde le séparateur tel que fourni.\n\n"
            "Les variables GV, PV, montant_annuel sont des montants financiers a indiquer en euros (€). VE correspond au nombre de visites d'entretien effectuées.\n\n"
            "Ne donne pas d'informations hors contexte ou non demandées.\n\n"
            "Schéma de sortie JSON STRICT:\n"
            "{\n"
            '  "answer": "un résumé en 2 a 4 phrases\\n Pour les montants comme montant PV ou  GV ou total annuel donne le en (€) pour VE  en donnees ca mentionne les visites d entretien effectuees"\n'
            '  "uses_context": true\n'
            "}\n"
        ),
        generation_config={
            "temperature": temperature,
            "max_output_tokens": max_out,
            "response_mime_type": "application/json",
        },
    )
    return model


def _call_gemini_json(model, user_text: str) -> Dict[str, Any]:
    for attempt in range(max(1, GEMINI_RETRIES)):
        try:
            resp = model.generate_content([{"role": "user", "parts": [{"text": user_text}]}])
            txt = (resp.text or "").strip()
            try:
                return json.loads(txt)
            except Exception:
                return {"answer": txt or "Réponse vide.", "uses_context": False}
        except Exception as e:
            if attempt < GEMINI_RETRIES - 1:
                time.sleep((2 ** attempt) + random.random())
                continue
            return {"answer": f"Synthèse indisponible (Gemini). Détails: {e}", "uses_context": False}
