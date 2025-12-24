# app/services/agent_email.py

from typing import Dict, Any, List, Tuple
from datetime import datetime
import re
from app.core.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
import os
from openai import OpenAI

from bs4 import BeautifulSoup

from app.utils.graph_client import fetch_all_emails, get_message_attachments

from app.utils.graph_client import (
    get_message_attachments,
    download_message_attachment
)
deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_API_URL,
)

def clean_email_html(html: str) -> str:
    """Convertit un email HTML en texte propre et supprime les parties inutiles."""
    soup = BeautifulSoup(html or "", "html.parser")

    for tag in soup(["script", "style"]):
        tag.extract()

    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    return text[:2000]


def smart_filter(question: str, emails: List[dict]) -> List[dict]:
    """Filtre intelligent avant d'envoyer au LLM."""
    q = (question or "").lower()

    # 1) Filtrer par expéditeur (ex: "mourad", "firas", etc.)
    for email in emails:
        sender = email.get("from", {}).get("emailAddress", {}).get("address", "")
        if sender:
            s = sender.lower()
            if any(name in q for name in s.split("@")[0].split(".")):
                return [
                    e for e in emails
                    if s in (e.get("from", {})
                             .get("emailAddress", {})
                             .get("address", "")
                             .lower())
                ]

    # 2) Détection d'une date (ex: "11/11/2025")
    date_pattern = r"(\d{1,2}/\d{1,2}/\d{4})"
    match = re.search(date_pattern, q)
    if match:
        date_str = match.group(1)
        try:
            target_date = datetime.strptime(date_str, "%d/%m/%Y").date()
            filtered = []
            for e in emails:
                d = e.get("receivedDateTime")
                if d:
                    email_date = datetime.fromisoformat(d.replace("Z", "")).date()
                    if email_date == target_date:
                        filtered.append(e)
            return filtered
        except Exception:
            pass

    # 3) Emails d’aujourd’hui
    if "aujourd'hui" in q or "today" in q:
        today = datetime.utcnow().date()
        return [
            e for e in emails
            if e.get("receivedDateTime") and
               datetime.fromisoformat(e["receivedDateTime"].replace("Z", "")).date() == today
        ]

    # 4) Emails de cette semaine
    if "semaine" in q:
        today = datetime.utcnow().date()
        return [
            e for e in emails
            if e.get("receivedDateTime") and
               (today - datetime.fromisoformat(e["receivedDateTime"].replace("Z", "")).date()).days <= 7
        ]

    # 5) Filtrer par mot-clé dans le sujet
    words = q.split()
    return [
        email for email in emails
        if any(word in (email.get("subject") or "").lower() for word in words)
    ] or emails


def _format_attachments_for_context(graph_token: str, message_id: str) -> Tuple[str, List[dict]]:
    """
    Récupère les pièces jointes depuis Graph pour alimenter le prompt,
    et retourne:
      - attachments_text (lisible pour le LLM)
      - attachments_structured (pour le frontend)
    """
    attachments_data = get_message_attachments(graph_token, message_id)

    attachments_text = ""
    attachments_structured: List[dict] = []

    if attachments_data and "value" in attachments_data:
        for att in attachments_data["value"]:
            if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
                attachments_text += (
                    f"- ID: {att.get('id')}\n"
                    f"  Nom: {att.get('name')}\n"
                    f"  Type: {att.get('contentType')}\n"
                    f"  Taille: {att.get('size')}\n"
                )
                attachments_structured.append({
                    "id": att.get("id"),
                    "name": att.get("name"),
                    "contentType": att.get("contentType"),
                    "size": att.get("size"),
                })

    return attachments_text, attachments_structured


def answer_email_with_llm(
    question: str,
    graph_token: str,
    claims: Dict[str, Any],
) -> Dict[str, Any]:

    # 1) Récupération emails avec pagination (max 500)
    emails = fetch_all_emails(graph_token, max_emails=500)
    if not emails:
        return {"answer": "Aucun email trouvé.", "emails": []}

    # 2) Filtrage intelligent avant LLM
    filtered_emails = smart_filter(question, emails)[:20]  # éviter explosion tokens

    email_context = ""
    extracted_emails: List[dict] = []

    # 3) Construire le contexte pour le LLM (AVEC pièces jointes réelles)
    for i, msg in enumerate(filtered_emails):
        message_id = msg.get("id")

        sender = msg.get("from", {}).get("emailAddress", {}).get("address", "Inconnu")

        destinataires = [
            r.get("emailAddress", {}).get("address", "Inconnu")
            for r in msg.get("toRecipients", [])
        ]
        cc_list = [
            r.get("emailAddress", {}).get("address", "Inconnu")
            for r in msg.get("ccRecipients", [])
        ]
        bcc_list = [
            r.get("emailAddress", {}).get("address", "Inconnu")
            for r in msg.get("bccRecipients", [])
        ]

        date_received = msg.get("receivedDateTime", "Non disponible")
        date_sent = msg.get("sentDateTime", "Non disponible")

        subject = msg.get("subject", "(Sans sujet)")
        body_html = msg.get("body", {}).get("content", "")
        clean_body = clean_email_html(body_html)

        attachments_text, attachments_structured = _format_attachments_for_context(
            graph_token=graph_token,
            message_id=message_id,
        )

        email_context += f"""
### EMAIL {i+1}
MessageID: {message_id}
De: {sender}
À: {", ".join(destinataires) or "Non disponible"}
CC: {", ".join(cc_list) or "Non disponible"}
BCC: {", ".join(bcc_list) or "Non disponible"}
Date réception: {date_received}
Date envoi: {date_sent}
Sujet: {subject}
Pièces jointes:
{attachments_text if attachments_text else "Aucune"}
Contenu:
{clean_body}
---------------------------------------------
"""

        extracted_emails.append({
            "message_id": message_id,
            "sender": sender,
            "recipients": destinataires,
            "cc": cc_list,
            "bcc": bcc_list,
            "date_received": date_received,
            "date_sent": date_sent,
            "subject": subject,
            "body": clean_body,
            "attachments": attachments_structured,
        })

    # 4) Prompt final (celui que tu voulais, avec règles strictes)
    extraction_prompt = f"""
Tu es un assistant expert en analyse d'emails Outlook.
Tu ne réponds QU’À PARTIR des emails fournis ci-dessous.
Ne JAMAIS inventer d’informations.

RÈGLES ABSOLUES (OBLIGATOIRES) :
- N’invente JAMAIS un email, un contenu ou une pièce jointe
- Si une information n’existe pas dans les emails fournis, écris explicitement "Non disponible"
- Si une pièce jointe existe, utilise UNIQUEMENT son ID et son nom fournis
- N’invente JAMAIS de lien de téléchargement
- N’invente JAMAIS de nom de fichier

Voici les emails disponibles :
{email_context}

Ta tâche dépend de la question de l'utilisateur :

────────────────────────────────

1️⃣ SI l'utilisateur demande UN EMAIL PRÉCIS :

TYPE: EMAIL_UNIQUE
Sujet: <sujet exact>
Expéditeur: <email>
Destinataires: <liste>
CC: <liste>
BCC: <liste>
Date de réception: <date>
Date d'envoi: <date>
Pièces jointes:
- Nom: <nom exact>
  ID: <id exact>
  Type: <contentType>
(ou "Aucune" si vide)

Contenu:
<contenu exact>

────────────────────────────────

2️⃣ SI l'utilisateur demande UNE LISTE D'EMAILS :

TYPE: LISTE_EMAILS
Emails:
- Sujet: <sujet>
  Expéditeur: <email>
  Destinataires: <liste>
  CC: <liste>
  BCC: <liste>
  Date de réception: <date>
  Date d'envoi: <date>
  Pièces jointes:
  - Nom: <nom exact>
    ID: <id exact>
  (ou "Aucune")
  Résumé: <résumé très court>

────────────────────────────────

3️⃣ SI l'utilisateur demande UN RÉSUMÉ GÉNÉRAL :

TYPE: RESUME
Résumé:
<texte court>

────────────────────────────────

4️⃣ SI AUCUN EMAIL NE CORRESPOND :

TYPE: AUCUN
Message: Aucun email ne correspond.

────────────────────────────────

IMPORTANT :
- Si plusieurs emails correspondent mais que l’utilisateur semble en vouloir un seul, retourne le plus pertinent
- Ne change JAMAIS le format ci-dessus
- Ne rajoute AUCUN texte en dehors du format

Question de l'utilisateur :
{question}
"""

    # 5) Appel LLM (client AINA)
    # -> on garde ton comportement: renvoyer le texte brut + emails structurés
        # 5) Appel LLM (DeepSeek – inline, comme EMAILREADER)
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un assistant expert en analyse d'emails Outlook.",
                },
                {
                    "role": "user",
                    "content": extraction_prompt,
                },
            ],
        )

        if not response or not response.choices:
            answer_text = ""
        else:
            answer_text = response.choices[0].message.content or ""

    except Exception as e:
        # log minimal, sans casser le flux
        print("❌ DeepSeek error:", e)
        answer_text = ""


    return {
        "answer": answer_text or "Aucune réponse générée.",
        "emails": extracted_emails,
        
    }


def list_email_attachments(
    message_id: str,
    claims: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Liste les pièces jointes (fileAttachment uniquement)
    pour un email Outlook donné.
    """

    # 🔐 Récupération du token Graph depuis les claims
    # (temporaire, sans OBO)
    graph_token = claims.get("graph_access_token")
    if not graph_token:
        raise RuntimeError(
            "Token Graph manquant dans les claims (OBO non implémenté)"
        )

    data = get_message_attachments(
        graph_token=graph_token,
        message_id=message_id,
    )

    attachments: List[Dict[str, Any]] = []

    for att in data.get("value", []):
        if att.get("@odata.type") == "#microsoft.graph.fileAttachment":
            attachments.append({
                "id": att.get("id"),
                "name": att.get("name"),
                "contentType": att.get("contentType"),
                "size": att.get("size"),
            })

    return attachments


def download_email_attachment(
    message_id: str,
    attachment_id: str,
    claims: Dict[str, Any],
) -> Tuple[bytes, str, str | None]:
    """
    Télécharge une pièce jointe Outlook et retourne :
    - bytes
    - content_type
    - filename (optionnel)
    """

    # 🔐 Récupération du token Graph
    graph_token = claims.get("graph_access_token")
    if not graph_token:
        raise RuntimeError(
            "Token Graph manquant dans les claims (OBO non implémenté)"
        )

    file_bytes, content_type = download_message_attachment(
        graph_token=graph_token,
        message_id=message_id,
        attachment_id=attachment_id,
    )

    if not file_bytes:
        raise RuntimeError("Pièce jointe introuvable")

    # Nom de fichier → récupéré côté Graph si dispo
    filename = attachment_id  # fallback safe

    return file_bytes, content_type, filename

