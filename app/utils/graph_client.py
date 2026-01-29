# app/utils/graph_client.py
from typing import Any, Dict, List, Optional
from app.core.http_client import get_http_client
from datetime import datetime, timezone
import httpx
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

async def list_messages_minimal(
    graph_token: str,
    top: int = 30,
    subject_contains: Optional[str] = None,
    is_read: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    # $select minimal = perf (best practice)
    select = "id,subject,from,receivedDateTime,ccRecipients,bccRecipients,hasAttachments,toRecipients,isRead,bodyPreview"
    filters = []

    if subject_contains:
        safe_subject = subject_contains.replace("'", "''")
        filters.append(f"contains(subject,'{safe_subject}')")

    if is_read is not None:
        filters.append(f"isRead eq {str(is_read).lower()}")

    filter_q = f"&$filter={' and '.join(filters)}" if filters else ""

    url = (
        f"{GRAPH_BASE_URL}/me/messages"
        f"?$top={top}"
        f"&$select={select}"
        f"{filter_q}"
        f"&$orderby=receivedDateTime desc"
    )


    client = get_http_client()
    r = await client.get(url, headers=_auth_headers(graph_token))
    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
    return r.json().get("value", [])

async def get_message_detail(
    graph_token: str,
    message_id: str,
) -> Dict[str, Any]:
    select = (
    "id,subject,from,toRecipients,ccRecipients,bccRecipients,"
    "receivedDateTime,sentDateTime,isRead,body,hasAttachments"
    )
    url = f"{GRAPH_BASE_URL}/me/messages/{message_id}?$select={select}"
    client = get_http_client()
    r = await client.get(url, headers=_auth_headers(graph_token))
    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
    return r.json()

async def get_attachments_for_message(
    graph_token: str,
    message_id: str,
) -> List[Dict[str, Any]]:
    select = "id,name,contentType,size"
    url = f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments?$select={select}"
    client = get_http_client()
    r = await client.get(url, headers=_auth_headers(graph_token))
    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
    data = r.json().get("value", [])
    # garder seulement fileAttachment
    return [
        {"id": a.get("id"), "name": a.get("name"), "contentType": a.get("contentType"), "size": a.get("size")}
        for a in data
        if a.get("@odata.type") == "#microsoft.graph.fileAttachment"
    ]

async def download_message_attachment(
    graph_token: str,
    message_id: str,
    attachment_id: str,
) -> tuple[bytes, str, str]:
    """
    Télécharge une pièce jointe Outlook et retourne
    (bytes, content_type, filename)
    """

    client = get_http_client()

    # 1️⃣ Get attachment metadata (to retrieve filename)
    meta_url = f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments/{attachment_id}"
    meta_resp = await client.get(meta_url, headers=_auth_headers(graph_token))
    if meta_resp.status_code != 200:
        raise RuntimeError(f"Graph meta error {meta_resp.status_code}: {meta_resp.text}")

    attachment = meta_resp.json()
    filename = attachment.get("name", "attachment")
    content_type = attachment.get("contentType", "application/octet-stream")

    # 2️⃣ Get raw binary content
    content_url = f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments/{attachment_id}/$value"
    content_resp = await client.get(content_url, headers=_auth_headers(graph_token))
    if content_resp.status_code != 200:
        raise RuntimeError(f"Graph content error {content_resp.status_code}: {content_resp.text}")

    return content_resp.content, content_type, filename

async def list_messages_by_sender_paginated(
    graph_token: str,
    sender_contains: str,
    page_size: int = 50,
    max_pages: int = 10,
) -> list[dict]:
    """
    Liste TOUS les emails d’un expéditeur donné,
    sans contrainte de date, avec pagination contrôlée.
    """
    select = (
    "id,subject,from,receivedDateTime,"
    "hasAttachments,bodyPreview,toRecipients"
)

    url = (
        f"{GRAPH_BASE_URL}/me/messages"
        f"?$top={page_size}"
        f"&$select={select}"
        f"&$orderby=receivedDateTime desc"
    )

    client = get_http_client()
    results = []
    pages = 0

    while url and pages < max_pages:
        r = await client.get(url, headers=_auth_headers(graph_token))
        if r.status_code != 200:
            raise RuntimeError(f"Graph error {r.status_code}: {r.text}")

        data = r.json()
        emails = data.get("value", [])

        for e in emails:
            sender = (
                e.get("from", {})
                 .get("emailAddress", {})
                 .get("address", "")
                 .lower()
            )
            if sender_contains.lower() in sender:
                results.append(e)

        url = data.get("@odata.nextLink")
        pages += 1

    return results

async def list_messages_by_exact_date(
    graph_token: str,
    target_date: str,  # YYYY-MM-DD
) -> list[dict]:

    start = f"{target_date}T00:00:00Z"
    end = f"{target_date}T23:59:59Z"

    select = (
        "id,subject,from,receivedDateTime,"
        "hasAttachments,bodyPreview,toRecipients"
    )

    url = (
        "https://graph.microsoft.com/v1.0/me/messages"
        f"?$select={select}"
        f"&$filter=receivedDateTime ge {start} and receivedDateTime le {end}"
        f"&$orderby=receivedDateTime desc"
    )

    client = get_http_client()
    r = await client.get(
        url,
        headers={"Authorization": f"Bearer {graph_token}"}
    )

    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")

    return r.json().get("value", [])

# --- DRAFT EMAIL HELPERS ---
async def create_draft_message(
    graph_token: str,
    *,
    to: list[str],
    subject: str,
    body_html: str,
) -> dict:
    """
    Create a draft message in the user's mailbox.
    Graph: POST /me/messages
    """
    url = f"{GRAPH_BASE_URL}/me/messages"
    payload = {
        "subject": subject,
        "body": {"contentType": "HTML", "content": body_html},
        "toRecipients": [
            {"emailAddress": {"address": addr}} for addr in (to or []) if addr
        ],
    }

    client = get_http_client()
    r = await client.post(url, json=payload, headers=_auth_headers(graph_token))
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Graph draft create error {r.status_code}: {r.text}")

    return r.json()

async def send_draft_message(
    graph_token: str,
    *,
    draft_id: str,
) -> None:
    """
    Send an existing draft message.
    Graph: POST /me/messages/{id}/send
    """
    if not draft_id:
        raise RuntimeError("draft_id manquant")

    url = f"{GRAPH_BASE_URL}/me/messages/{draft_id}/send"
    client = get_http_client()
    r = await client.post(url, headers=_auth_headers(graph_token))
    if r.status_code != 202:
        raise RuntimeError(f"Graph send error {r.status_code}: {r.text}")
   
async def update_draft_message(
    graph_token: str,
    draft_id: str,
    *,
    subject: Optional[str] = None,
    body_html: Optional[str] = None,
) -> Dict[str, Any]:
    url = f"{GRAPH_BASE}/me/messages/{draft_id}"
    payload: Dict[str, Any] = {}

    if subject is not None:
        payload["subject"] = subject

    if body_html is not None:
        payload["body"] = {"contentType": "HTML", "content": body_html}

    if not payload:
        return {"ok": True}

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.patch(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {graph_token}"},
        )

    if resp.status_code >= 300:
        raise RuntimeError(f"Graph update draft failed: {resp.status_code} {resp.text}")

    return resp.json() if resp.text else {"ok": True}