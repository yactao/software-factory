# app/services/agent_global_audit.py

from typing import Tuple

from fastapi import HTTPException

from app.core.config import KIMI_MODEL_GLOBAL
from app.services.kimi_client import get_kimi_client
from app.services.blob_global_pdf import download_global_audit_pdf_to_temp


def answer_global_with_kimi(question: str) -> Tuple[str, bool]:
    """
    Analyse le PDF global (toutes fiches d'audit) avec Kimi.

    Étapes :
      1) Téléchargement du PDF global depuis Azure Blob (fichier temporaire)
      2) Upload vers Kimi avec purpose="file-extract"
      3) Récupération du texte extrait via files.content(...)
      4) Appel chat.completions classique en envoyant ce texte dans le prompt

    Retourne (answer, uses_context=True).
    """

    client = get_kimi_client()

    # 1) Télécharger le PDF depuis Azure Blob dans un fichier temporaire
    try:
        pdf_path = download_global_audit_pdf_to_temp()
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du chargement du PDF global: {e}")

    # 2) Uploader le fichier à Kimi pour extraction
    try:
        with open(pdf_path, "rb") as f:
            uploaded_file = client.files.create(
                file=f,
                purpose="file-extract",  # mode d’extraction de texte chez Moonshot
            )
    except Exception as e:
        raise HTTPException(500, f"Erreur lors de l'upload du PDF global vers Kimi: {e}")

    file_id = uploaded_file.id

    # 3) Récupérer le texte extrait par Kimi
    try:
        extracted_text = client.files.content(file_id=file_id).text
    except Exception as e:
        raise HTTPException(500, f"Erreur lors de l'extraction du texte du PDF global: {e}")

    if not extracted_text or not extracted_text.strip():
        raise HTTPException(500, "Le texte extrait du PDF global est vide.")

    # 4) Construire le prompt pour le chat
    system_prompt = (
        "Tu es un assistant technique spécialisé en audits de climatisation, "
        "chauffage et ventilation pour des magasins.\n"
        "Tu disposes d'un document unique qui regroupe plusieurs fiches d'audit de magasins.\n\n"
        "Tu dois répondre STRICTEMENT à partir de ce document.\n"
        "Si une information n'est pas présente, dis-le clairement.\n\n"
        "Le texte suivant correspond au contenu intégral du document global:\n"
        "----- DOCUMENT GLOBAL DEBUT -----\n"
        f"{extracted_text}\n"
        "----- DOCUMENT GLOBAL FIN -----\n\n"
        "Réponds en texte brut, sans Markdown, sans emojis, sans puces.\n"
        "Donne une réponse structurée, claire et concise, adaptée à un contexte d'entreprise."
        "Si la question ne peut pas être répondue avec le contexte, dis-le clairement.\n\n"
        "Langue: réponds dans la langue de la question."
        "Tu synthétises les informations pertinentes du document pour répondre à la question.\n"
        "La réponse doit être complète et précise et contient juste ce qui est demandé dans la question.\n"
        "Ne rajoute pas d'informations qui ne sont pas dans le document.\n"
        "Ne soit pas trop long, vise une réponse concise et pertinente.\n"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]

    # 5) Appel du modèle Kimi pour générer la réponse
    try:
        completion = client.chat.completions.create(
            model=KIMI_MODEL_GLOBAL,
            messages=messages,
            temperature=0.2,
            max_tokens=2048,
        )
    except Exception as e:
        raise HTTPException(500, f"Erreur Kimi (global): {e}")

    msg = completion.choices[0].message

    # 6) Récupération du texte de réponse (gestion string ou liste de blocs)
    if isinstance(msg.content, str):
        answer = msg.content
    else:
        parts = []
        for part in msg.content:
            if isinstance(part, dict) and part.get("type") in ("output_text", "text"):
                parts.append(part.get("text", ""))
            elif isinstance(part, str):
                parts.append(part)
        answer = " ".join(parts) if parts else str(msg.content)

    return answer.strip(), True
