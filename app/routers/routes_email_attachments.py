# app/routers/routes_email_attachments.py

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import _auth_dependency, _require_scope
from app.services.agent_email import (
    list_email_attachments,
    download_email_attachment,
)

router = APIRouter()

@router.get("/api/aina/email/{message_id}/attachments")
def get_email_attachments(
    message_id: str,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Liste les pièces jointes d’un email Outlook.
    """
    _require_scope(claims)

    if not message_id:
        raise HTTPException(status_code=400, detail="message_id manquant")

    return {
        "attachments": list_email_attachments(
            message_id=message_id,
            claims=claims,
        )
    }

@router.get(
    "/api/aina/email/{message_id}/attachments/{attachment_id}/download"
)
def download_attachment(
    message_id: str,
    attachment_id: str,
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    """
    Télécharge une pièce jointe Outlook (stream).
    """
    _require_scope(claims)

    if not message_id or not attachment_id:
        raise HTTPException(
            status_code=400,
            detail="message_id ou attachment_id manquant",
        )

    file_bytes, content_type, filename = download_email_attachment(
        message_id=message_id,
        attachment_id=attachment_id,
        claims=claims,
    )

    headers = {}
    if filename:
        headers["Content-Disposition"] = (
            f'attachment; filename="{filename}"'
        )

    return StreamingResponse(
        iter([file_bytes]),
        media_type=content_type,
        headers=headers,
    )
