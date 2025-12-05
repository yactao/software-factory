from fastapi import APIRouter, Depends, HTTPException, Query
from ..core.security import _auth_dependency, _require_scope
from ..core.config import ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER, CONTAINER_TRADING
from ..services.blob_sas import _blob_exists, _make_sas_url

router = APIRouter()

@router.get("/api/sas")
def get_sas(
    path: str,
    ttl: int = Query(60, ge=1, le=60, description="Durée du SAS en minutes"),
    claims: dict = Depends(_auth_dependency),
):
    _require_scope(claims)

    if not (ACCOUNT_NAME and ACCOUNT_KEY and CONTAINER):
        raise HTTPException(500, "Storage credentials manquants.")

    p = (path or "").strip().lstrip("/")
    if not p or p.endswith("/"):
        raise HTTPException(400, "Paramètre 'path' invalide (fichier requis).")

    candidates = [p]
    lower = p.lower()
    if lower.endswith(".pdf"): candidates.append(p[:-4] + "docx")
    elif lower.endswith(".docx"): candidates.append(p[:-5] + "pdf")

    containers = [CONTAINER] + ["vet-docs"] + ([CONTAINER_TRADING] if CONTAINER_TRADING and CONTAINER_TRADING != CONTAINER else [])

    for c in containers:
        for cand in candidates:
            if _blob_exists(c, cand):
                url = _make_sas_url(c, cand, minutes=ttl)
                return {"url": url, "container": c, "blob": cand, "expires_in_minutes": ttl}

    raise HTTPException(404, detail={"error": "Blob introuvable","tried_containers": containers,"tried_paths": candidates})
