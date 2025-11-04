# app/routers/vision_attach.py
import io
from typing import Optional
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.core.security import _auth_dependency, _require_scope
from app.services.history_helpers import _save_chat_event
from app.services.history_helpers import get_last_vision_file_path
from app.services.blob_vision import put_temp, sas_url
from PIL import Image

router = APIRouter()

@router.post("/api/vision/attach")
async def vision_attach(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = Form(None),
    claims: dict = Depends(_auth_dependency),
):
    _require_scope(claims)
    content = await file.read()
    if not content:
        raise HTTPException(400, "Fichier vide.")

    conv_id = _save_chat_event(
        claims, conversation_id, role="user", route="vision",
        message=f"[ATTACH:{file.filename}]",
        meta={}
    )
    from app.services.history_helpers import _pk_from_claims
    pk = _pk_from_claims(claims)

    # Upload RAW tel quel
    path = put_temp(pk, conv_id, file.filename or "upload.bin", content)

    # Sauvegarde meta vision_file_path
    _save_chat_event(
        claims, conv_id, role="meta", route="vision",
        message="", meta={"vision_file_path": path}
    )

    return {
        "conversation_id": conv_id,
        "vision_file_path": path,
        "vision_file_sas": sas_url(path, minutes=120)
    }
