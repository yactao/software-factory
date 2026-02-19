# app/services/agent_global_audit.py

from typing import Tuple

from fastapi import HTTPException

from app.core.config import RAG_LLM_PROVIDER
from app.services.llm_provider import (
    get_llm_client_and_model,
    llm_chat_completion_with_client,
)
from app.services.blob_global_pdf import download_global_audit_pdf_to_temp
from app.services.pdf_extract import extract_text_from_pdf


def _system_prompt_with_text(extracted_text: str) -> str:
    return (
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


def answer_global_with_kimi(question: str) -> Tuple[str, bool]:
    """
    Analyse le PDF global (toutes fiches d'audit) avec le LLM configuré (Kimi, OpenAI ou Azure OpenAI).

    - Kimi: upload PDF vers l'API (file-extract) puis chat avec le texte extrait.
    - OpenAI: upload PDF vers l'API (user_data) puis chat avec le fichier en pièce jointe.
    - Azure OpenAI: extraction locale du texte PDF puis chat avec le texte dans le prompt.

    Retourne (answer, uses_context=True).
    """
    provider = (RAG_LLM_PROVIDER or "kimi").strip().lower()
    client, model = get_llm_client_and_model("rag_global")

    # 1) Télécharger le PDF depuis Azure Blob
    try:
        pdf_path = download_global_audit_pdf_to_temp()
    except Exception as e:
        raise HTTPException(500, f"Erreur lors du chargement du PDF global: {e}")

    extracted_text: str = ""
    use_file_in_message = False
    file_id = None

    if provider == "kimi":
        # Kimi: upload + extraction via API
        try:
            with open(pdf_path, "rb") as f:
                uploaded_file = client.files.create(
                    file=f,
                    purpose="file-extract",
                )
            file_id = uploaded_file.id
            extracted_text = client.files.content(file_id=file_id).text or ""
        except Exception as e:
            raise HTTPException(
                500, f"Erreur lors de l'upload/extraction du PDF global (Kimi): {e}"
            )
        if not extracted_text or not extracted_text.strip():
            raise HTTPException(500, "Le texte extrait du PDF global est vide.")
        # On envoie le texte dans le prompt (comportement actuel)
        system_prompt = _system_prompt_with_text(extracted_text)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        answer = llm_chat_completion_with_client(
            client, model, messages, temperature=0.2, max_tokens=2048
        )
        return answer.strip(), True

    if provider == "openai":
        # OpenAI: upload PDF puis envoi du file_id dans le message user (API File inputs)
        try:
            with open(pdf_path, "rb") as f:
                uploaded = client.files.create(
                    file=f,
                    purpose="user_data",
                )
            file_id = uploaded.id
        except Exception as e:
            # Fallback: extraction locale puis prompt texte
            try:
                extracted_text = extract_text_from_pdf(pdf_path)
            except HTTPException:
                raise HTTPException(
                    500,
                    f"Erreur upload PDF OpenAI et extraction locale impossible: {e}",
                )
            if not extracted_text or not extracted_text.strip():
                raise HTTPException(500, "PDF vide ou extraction impossible.")
            system_prompt = _system_prompt_with_text(extracted_text)
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ]
            answer = llm_chat_completion_with_client(
                client, model, messages, temperature=0.2, max_tokens=2048
            )
            return answer.strip(), True
        # Envoi du PDF en pièce jointe
        system_prompt = (
            "Tu es un assistant technique spécialisé en audits de climatisation, "
            "chauffage et ventilation pour des magasins.\n"
            "Tu disposes d'un document PDF qui regroupe plusieurs fiches d'audit.\n\n"
            "Tu dois répondre STRICTEMENT à partir de ce document.\n"
            "Si une information n'est pas présente, dis-le clairement.\n\n"
            "Réponds en texte brut, sans Markdown, sans emojis, sans puces.\n"
            "Langue: réponds dans la langue de la question.\n"
            "Réponse concise et pertinente.\n"
        )
        user_content = [
            {"type": "file", "file": {"file_id": file_id}},
            {"type": "text", "text": question},
        ]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]
        answer = llm_chat_completion_with_client(
            client, model, messages, temperature=0.2, max_tokens=2048
        )
        return answer.strip(), True

    # azure_openai (ou autre): pas d'upload PDF côté API, on extrait le texte localement
    try:
        extracted_text = extract_text_from_pdf(pdf_path)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(500, f"Erreur extraction PDF (fallback): {e}")
    if not extracted_text or not extracted_text.strip():
        raise HTTPException(500, "Le texte extrait du PDF global est vide.")
    system_prompt = _system_prompt_with_text(extracted_text)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ]
    answer = llm_chat_completion_with_client(
        client, model, messages, temperature=0.2, max_tokens=2048
    )
    return answer.strip(), True
