from fastapi import APIRouter, Query, Depends
from app.core.security import _auth_dependency, _require_scope
from app.services.blob_vision import sas_url

router = APIRouter()

@router.get("/api/vision/sas")
def vision_sas(
    path: str = Query(..., description="ex: pk/conv/file.jpg"),
    claims: dict = Depends(_auth_dependency),
):
    _require_scope(claims)
    return {"url": sas_url(path, minutes=180)}
