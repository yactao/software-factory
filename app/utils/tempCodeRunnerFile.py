# app/utils/graph_client.py
from typing import Any, Dict, List, Optional

from datetime import datetime, timezone
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"

def _auth_headers(token: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"}

async def list_messages_minimal(
    graph_token: str,
    top: int = 30,
    subject_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    # $select minimal = perf (best practice)
    select = "id,subject,from,receivedDateTime,hasAttachments,toRecipients"
    url = f"{GRAPH_BASE_URL}/me/messages?$top={top}&$select={select}"

    if subject_contains:
        # contains(subject,'x') fonctionne sur beaucoup de tenants, sinon fallback côté app
        safe_subject = subject_contains.replace("'", "''")
        url += f"&$filter=contains(subject,'{safe_subject}')"


    client = get_http_client()
    r = await client.get(url, headers=_auth_headers(graph_token))
    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
    return r.json().get("value", [])

async def get_message_detail(
    graph_token: str,
    message_id: str,
) -> Dict[str, Any]:
    select = "id,subject,from,toRecipients,ccRecipients,bccRecipients,receivedDateTime,sentDateTime,body,hasAttachments"
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
) -> tuple[bytes, str]:
    url = f"{GRAPH_BASE_URL}/me/messages/{message_id}/attachments/{attachment_id}/$value"
    client = get_http_client()
    r = await client.get(url, headers=_auth_headers(graph_token))
    if r.status_code != 200:
        raise RuntimeError(f"Graph error {r.status_code}: {r.text}")
    content_type = r.headers.get("Content-Type", "application/octet-stream")
    return r.content, content_type


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
