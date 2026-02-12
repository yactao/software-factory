# app/routers/trading_doc_sas.py
"""
SAS pour les documents de trading uniquement (conteneur aina-trading-docs).
Ne modifie pas la logique /api/sas existante.
"""

import os
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query

from ..core.security import _auth_dependency, _require_scope
from ..services.blob_sas import _blob_exists, _make_sas_url

# Conteneur dédié aux DOCX de trading (env: DOCX_CONTAINER)
DOCX_CONTAINER = os.getenv("DOCX_CONTAINER", "aina-trading-docs")

router = APIRouter()


@router.get("/api/trading/doc/sas")
def get_trading_doc_sas(
    path: str = Query(..., description="Nom du blob (ex: fichier.docx)"),
    ttl: int = Query(60, ge=1, le=60, description="Durée du SAS en minutes"),
    claims: Dict[str, Any] = Depends(_auth_dependency),
):
    _require_scope(claims)

    blob_path = (path or "").strip().lstrip("/")
    if not blob_path or blob_path.endswith("/"):
        raise HTTPException(400, "Paramètre 'path' invalide (fichier requis).")

    if not DOCX_CONTAINER:
        raise HTTPException(500, "DOCX_CONTAINER non configuré.")

    if not _blob_exists(DOCX_CONTAINER, blob_path):
        raise HTTPException(
            404,
            detail={
                "error": "Blob introuvable dans le conteneur trading doc",
                "container": DOCX_CONTAINER,
                "path": blob_path,
            },
        )

    url = _make_sas_url(DOCX_CONTAINER, blob_path, minutes=ttl)
    if not url:
        raise HTTPException(500, "Impossible de générer l'URL SAS.")

    return {
        "url": url,
        "container": DOCX_CONTAINER,
        "blob": blob_path,
        "expires_in_minutes": ttl,
    }
