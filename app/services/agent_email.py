# app/services/agent_email.py backend service for email question answering with LLM
from typing import Dict, Any, List, Optional
import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from openai import OpenAI

from app.core.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL
from app.core.obo import get_graph_token_on_behalf_of
from app.utils.graph_client import (
    list_messages_minimal,
    get_message_detail,
    get_attachments_for_message,
)

# =========================================================
# LLM Client
# =========================================================

deepseek_client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url=DEEPSEEK_API_URL,
)

# =========================================================
# SYSTEM PROMPT (METIER)
# =========================================================

SYSTEM_EMAIL_PROMPT = """
Tu es un assistant spécialisé dans la lecture d’emails Outlook via Microsoft Graph.
Tu n’as accès qu’aux emails fournis par l’application.
Tu ne dois jamais inventer d’emails, de dates, d’expéditeurs ou de contenus.

RÈGLES STRICTES :

1) LISTE PAR DATE
- Retourne la liste complète des emails de la date demandée
- Pour chaque email : sujet, expéditeur, date, résumé court (1 phrase)
- Ne retourne jamais le contenu complet

2) LISTE PAR EXPÉDITEUR
- Retourne TOUS les emails de l’expéditeur
- Pour chaque email : sujet, expéditeur, date, résumé court
- Aucune limitation (pas de top 5 / top 10)

3) EMAIL SPÉCIFIQUE
- Retourne UN SEUL email
- Contenu COMPLET de l’email
- AUCUN résumé

Ne mélange jamais plusieurs modes.
N’invente rien.
"""

# =========================================================
# Helpers
# =========================================================

MAX_AUTO_SUMMARIES = 5  # bonne pratique perf
def detect_read_filter(question: str) -> Optional[bool]:
    q = (question or "").lower()

    if "non lu" in q or "non lus" in q or "unread" in q or "pas lu" in q:
        return False

    if (" lu" in q or " lus" in q or "read" in q) and \
       ("non lu" not in q and "non lus" not in q and "pas lu" not in q):
        return True

    return None

def clean_email_html(html: str) -> str:
    soup = BeautifulSoup(html or "", "html.parser")
    for tag in soup(["script", "style"]):
        tag.extract()
    text = soup.get_text(separator="\n")
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text[:1200]

def extract_sender_keywords(question: str) -> List[str]:
    stop_words = {
        "donne", "moi", "liste", "des", "emails", "email",
        "de", "les", "tous", "toutes"
    }
    words = [w for w in re.split(r"\W+", question.lower()) if len(w) >= 3]
    return [w for w in words if w not in stop_words]

def sender_matches(email: Dict[str, Any], keywords: List[str]) -> bool:
    addr = (
        email.get("from", {})
        .get("emailAddress", {})
        .get("address", "")
        .lower()
    )
    name = (
        email.get("from", {})
        .get("emailAddress", {})
        .get("name", "")
        .lower()
    )
    haystack = f"{addr} {name}"
    return all(k in haystack for k in keywords)

def format_recipient_list(recipients: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Return list of {name, address} from Graph recipients."""
    out: List[Dict[str, str]] = []
    for r in recipients or []:
        ea = (r or {}).get("emailAddress") or {}
        out.append({
            "name": ea.get("name") or "",
            "address": ea.get("address") or "",
        })
    return out

def format_sender(email: Dict[str, Any]) -> Dict[str, str]:
    ea = (email.get("from") or {}).get("emailAddress") or {}
    return {
        "name": ea.get("name") or "",
        "address": ea.get("address") or "Inconnu",
    }

def extract_date_from_question(question: str) -> Optional[str]:
    match = re.search(r"(\d{2})[/-](\d{2})[/-](\d{4})", question)
    if not match:
        return None

    day, month, year = match.groups()
    try:
        dt = datetime(int(year), int(month), int(day))
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return None


def pick_best_email(question: str, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
    words = [w for w in re.split(r"\W+", question.lower()) if len(w) >= 4]
    if not emails: 
        raise RuntimeError("Aucun email disponible pour sélection")
    best, score = emails[0], -1
    for e in emails:
        subj = (e.get("subject") or "").lower()
        s = sum(1 for w in words if w in subj)
        if s > score:
            best, score = e, s
    return best


async def summarize_email_llm(text: str) -> str:
    prompt = f"""
Résume l'email suivant en UNE phrase courte et factuelle.
N'invente rien.

Email :
{text[:1200]}
"""
    resp = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "Assistant de résumé d'emails."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=60,
    )
    return resp.choices[0].message.content.strip()

# =========================================================
# Date-based filtering
def smart_filter(question: str, emails: List[dict]) -> List[dict]:
    """Filtre intelligent central (logique qui marchait)."""
    q = (question or "").lower()

    # 1) Filtrer par expéditeur
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

    # 2) Date exacte JJ/MM/AAAA
    match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", q)
    if match:
        try:
            target_date = datetime.strptime(match.group(1), "%d/%m/%Y").date()
            return [
                e for e in emails
                if e.get("receivedDateTime") and
                   datetime.fromisoformat(
                       e["receivedDateTime"].replace("Z", "")
                   ).date() == target_date
            ]
        except ValueError:
            pass

    # 3) Aujourd’hui
    if "aujourd'hui" in q or "today" in q:
        today = datetime.utcnow().date()
        return [
            e for e in emails
            if e.get("receivedDateTime") and
               datetime.fromisoformat(
                   e["receivedDateTime"].replace("Z", "")
               ).date() == today
        ]
    # 3bis) Hier / Yesterday
    if "hier" in q or "yesterday" in q:
        yesterday = (datetime.utcnow().date() - timedelta(days=1))
        return [
            e for e in emails
            if e.get("receivedDateTime") and
            datetime.fromisoformat(
                e["receivedDateTime"].replace("Z", "")
            ).date() == yesterday
        ]

    # 4) Cette semaine
    if "semaine" in q:
        today = datetime.utcnow().date()
        return [
            e for e in emails
            if e.get("receivedDateTime") and
               (today - datetime.fromisoformat(
                   e["receivedDateTime"].replace("Z", "")
               ).date()).days <= 7
        ]

    # 5) Sujet (fallback)
    words = [w for w in q.split() if len(w) > 2]
    subject_matched = [
        e for e in emails
        if any(word in (e.get("subject") or "").lower() for word in words)
    ]

    return subject_matched

# =========================================================
# Main entrypoint
# =========================================================

async def answer_email_with_llm(
    question: str,
    claims: Dict[str, Any],
) -> Dict[str, Any]:
    print("🔥 agent_email.py LOADED (FINAL VERSION) 🔥")

    # =====================================================
    # Auth / OBO
    # =====================================================
    user_token = claims.get("raw_token")
    if not user_token:
        raise RuntimeError("Token utilisateur manquant")

    user_id = claims.get("oid") or claims.get("sub") or "unknown"

    graph_token = await get_graph_token_on_behalf_of(
        user_token=user_token,
        user_id=user_id,
    )

    # =====================================================
    # Detect read / unread intent ONCE
    # =====================================================
    q_lower = (question or "").lower()
    read_filter = detect_read_filter(question)

    is_read_query = any(
        k in q_lower
        for k in ["non lu", "non lus", "unread", "pas lu", "lu", "lus", "read"]
    )

    # =====================================================
    # List messages (Graph minimal)
    # =====================================================
    candidates = await list_messages_minimal(
        graph_token=graph_token,
        top=1000,
        is_read=read_filter,  # Graph-side filtering
    )

    # =====================================================
    # Hard safety filter (Python)
    # =====================================================
    if read_filter is not None:
        candidates = [
            e for e in candidates
            if bool(e.get("isRead")) == read_filter
        ]

    # =====================================================
    # Smart semantic filter (ONLY if not read/unread query)
    # =====================================================
    if not is_read_query:
        candidates = smart_filter(question, candidates)

    if not candidates:
        return {
            "answer": "Aucun email correspondant à votre demande.",
            "emails": [],
        }

    # =====================================================
    # Detect LIST mode
    # =====================================================
    is_list = (
        any(k in q_lower for k in ["liste", "list", "tous", "toutes", "emails"])
        or is_read_query
        or bool(re.search(r"\d{1,2}/\d{1,2}/\d{4}", q_lower))
        or "aujourd'hui" in q_lower
        or "today" in q_lower
        or "semaine" in q_lower
    )

    # =====================================================
    # MODE LISTE → RESUME ONLY (NEVER BODY)
    # =====================================================
    if is_list:
        items: List[Dict[str, Any]] = []
        auto_summary_count = 0

        for e in candidates:
            summary: Optional[str] = None
            clean_body: Optional[str] = None

            # Always generate a REAL résumé (1 sentence)
            if auto_summary_count < MAX_AUTO_SUMMARIES:
                detail = await get_message_detail(
                    graph_token=graph_token,
                    message_id=e.get("id"),
                )

                body_html = (detail or {}).get("body", {}).get("content", "")
                if body_html:
                    clean_body = clean_email_html(body_html)

                if clean_body:
                    try:
                        summary = await summarize_email_llm(clean_body)
                        auto_summary_count += 1
                    except Exception:
                        summary = None

            if not summary:
                summary = "Résumé indisponible"

            items.append({
                "message_id": e.get("id"),
                "subject": e.get("subject") or "(Sans sujet)",

                # Structured metadata
                "from": format_sender(e),
                "to": format_recipient_list(e.get("toRecipients", [])),
                "cc": format_recipient_list(e.get("ccRecipients", [])),
                "bcc": format_recipient_list(e.get("bccRecipients", [])),
                "isRead": bool(e.get("isRead")),
                "receivedDateTime": e.get("receivedDateTime"),
                "hasAttachments": bool(e.get("hasAttachments")),

                # ✅ REAL résumé (never raw body)
                "summary": summary,
            })

        return {
            "answer": f"Voici les {len(items)} email(s) correspondants.",
            "emails": items,
        }

    # =====================================================
    # MODE EMAIL UNIQUE → FULL CONTENT
    # =====================================================
    best = pick_best_email(question, candidates)
    message_id = best["id"]

    detail = await get_message_detail(
        graph_token=graph_token,
        message_id=message_id,
    )

    body_html = (detail or {}).get("body", {}).get("content", "")
    clean_body = clean_email_html(body_html)

    attachments = []
    if detail and detail.get("hasAttachments"):
        attachments = await get_attachments_for_message(
            graph_token=graph_token,
            message_id=message_id,
        )

    return {
        "answer": clean_body,
        "emails": [
            {
                "message_id": message_id,
                "subject": detail.get("subject") or "(Sans sujet)",

                "from": format_sender(detail),
                "to": format_recipient_list(detail.get("toRecipients", [])),
                "cc": format_recipient_list(detail.get("ccRecipients", [])),
                "bcc": format_recipient_list(detail.get("bccRecipients", [])),

                "receivedDateTime": detail.get("receivedDateTime"),
                "isRead": bool(detail.get("isRead")),

                # ✅ Full body ONLY here
                "body": clean_body,
                "attachments": attachments,
            }
        ],
    }
