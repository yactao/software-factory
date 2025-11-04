from typing import Optional
from fastapi import APIRouter, Query, Depends
from app.core.security import _auth_dependency, _require_scope
from app.services.history_helpers import delete_vision_for_conversation

router = APIRouter()

@router.delete("/api/vision/cleanup")
def vision_cleanup(
    conversation_id: str = Query(...),
    claims: dict = Depends(_auth_dependency),
):
    _require_scope(claims)
    n = delete_vision_for_conversation(claims, conversation_id)
    return {"deleted": n}
