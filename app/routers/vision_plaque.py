import io
from typing import Optional

from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

from app.core.security import _auth_dependency, _require_scope
from app.services.history_helpers import _save_chat_event
from app.services.plaque_agent import run_plaque_agent_on_bytes
from app.services.blob_vision import put_temp, sas_url
from app.services.history_helpers import _pk_from_claims

router = APIRouter()


@router.post("/api/vision/plaque")
async def analyze_plaque(
    file: UploadFile = File(..., description="Image de la plaque (jpg, png, heic, pdf converti en image avant)"),
    prompt: str = Form(..., description="Instruction utilisateur"),
    conversation_id: Optional[str] = Form(None),
    claims: dict = Depends(_auth_dependency),
):
    """
    Analyse d'une plaque signalétique :
    - Sauvegarde de l'image dans Blob Storage (comme /api/vision)
    - Enregistrement dans l'historique (chat events)
    - Appel de l'agent plaques (OCR + GPT) sans changer le traitement
    """
    _require_scope(claims)

    content = await file.read()
    if not content:
        raise HTTPException(400, "Fichier vide.")

    # 1) Enregistrer l'événement utilisateur
    conv_id = _save_chat_event(
        claims,
        conversation_id=conversation_id,
        role="user",
        route="vision_plaque",
        message=f"[PLAQUE_UPLOAD:{file.filename}] {prompt}",
        meta={},
    )

    # 2) Sauvegarde de l'image brute sur Blob Storage (comme vision_attach)
    pk = _pk_from_claims(claims)
    blob_path = put_temp(pk, conv_id, file.filename or "plaque_upload.bin", content)

    _save_chat_event(
        claims,
        conv_id,
        role="meta",
        route="vision_plaque",
        message="",
        meta={"vision_plaque_file_path": blob_path},
    )

    # 3) Appel de ton agent plaques en gardant ta logique d'analyse
    try:
        agent_reply = run_plaque_agent_on_bytes(content, file.filename or "plaque.jpg", prompt)
    except Exception as e:
        raise HTTPException(500, f"Erreur traitement plaque: {e}")

    # 4) Sauvegarde de la réponse dans l'historique
    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="vision_plaque",
        message=agent_reply,
        meta={"vision_plaque_file_path": blob_path},
    )

    # 5) Réponse API (JSON) + SAS pour l’UI
    out = {
        "conversation_id": conv_id,
        "response_text": agent_reply,
        "vision_plaque_file_path": blob_path,
        "vision_plaque_file_sas": sas_url(blob_path, minutes=180),
    }
    return JSONResponse(status_code=200, content=out)
