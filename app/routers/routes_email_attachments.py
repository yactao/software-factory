# app/routers/routes_email_attachments.py

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import _auth_dependency, _require_scope
from app.core.obo import get_graph_token_on_behalf_of
from app.utils.graph_client import (
    get_attachments_for_message,
    download_message_attachment,
)

router = APIRouter()

@router.get("/api/aina/email/{message_id}/attachments")
async def get_email_attachments(
    message_id: str,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Liste les pièces jointes d’un email Outlook (OBO, lazy).
    """
    _require_scope(claims)

    if not message_id:
        raise HTTPException(status_code=400, detail="message_id manquant")

    # 🔐 OBO
    user_token = claims.get("raw_token")
    user_id = claims.get("oid") or claims.get("sub") or "unknown"

    graph_token = await get_graph_token_on_behalf_of(
        user_token=user_token,
        user_id=user_id,
    )

    attachments = await get_attachments_for_message(
        graph_token=graph_token,
        message_id=message_id,
    )

    return {"attachments": attachments}


@router.get("/api/aina/email/{message_id}/attachments/{attachment_id}/download")
async def download_attachment(
    message_id: str,
    attachment_id: str,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Télécharge une pièce jointe Outlook (OBO sécurisé).
    """
    _require_scope(claims)

    if not message_id or not attachment_id:
        raise HTTPException(
            status_code=400,
            detail="message_id ou attachment_id manquant",
        )

    # 🔐 OBO
    user_token = claims.get("raw_token")
    user_id = claims.get("oid") or claims.get("sub") or "unknown"

    graph_token = await get_graph_token_on_behalf_of(
        user_token=user_token,
        user_id=user_id,
    )

    file_bytes, content_type = await download_message_attachment(
        graph_token=graph_token,
        message_id=message_id,
        attachment_id=attachment_id,
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{attachment_id}"'
    }

    return StreamingResponse(
        iter([file_bytes]),
        media_type=content_type,
        headers=headers,
    )
