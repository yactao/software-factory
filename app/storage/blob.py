from __future__ import annotations

import datetime
import urllib.parse
from functools import lru_cache
from typing import Iterable, Optional

from fastapi import HTTPException
from azure.storage.blob import (
    BlobServiceClient,
    BlobSasPermissions,
    generate_blob_sas,
)

from app.settings import get_settings


@lru_cache
def get_blob_service() -> BlobServiceClient:
    """
    Client Blob Storage singleton basé sur account/key (ou connection string si souhaité plus tard).
    """
    s = get_settings()
    if not s.storage_account or not s.storage_key:
        raise HTTPException(500, "Storage credentials manquants (AZURE_STORAGE_ACCOUNT/_KEY).")
    url = f"https://{s.storage_account}.blob.core.windows.net"
    return BlobServiceClient(account_url=url, credential=s.storage_key)


def _normalize_path(path: str) -> str:
    p = (path or "").strip().lstrip("/")
    if not p or p.endswith("/"):
        raise HTTPException(400, "Chemin de blob invalide (fichier requis).")
    return p


def blob_exists(container: str, blob_path: str) -> bool:
    """
    Teste l'existence d'un blob.
    """
    bsc = get_blob_service()
    try:
        return bsc.get_blob_client(container=container, blob=blob_path).exists()
    except Exception:
        return False


def make_sas_url(container: str, blob_path: str, minutes: int = 5) -> str:
    """
    Génère une URL SAS lecture courte (par défaut 5 min).
    """
    s = get_settings()
    if minutes < 1 or minutes > 60:
        raise HTTPException(400, "TTL SAS invalide (1..60 min).")
    if not s.storage_account or not s.storage_key:
        raise HTTPException(500, "Storage credentials manquants pour SAS.")

    blob_path = _normalize_path(blob_path)
    sas = generate_blob_sas(
        account_name=s.storage_account,
        container_name=container,
        blob_name=blob_path,
        account_key=s.storage_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes),
    )
    return (
        f"https://{s.storage_account}.blob.core.windows.net/"
        f"{container}/{urllib.parse.quote(blob_path)}?{sas}"
    )


def resolve_blob_with_fallbacks(
    path: str,
    containers: Optional[Iterable[str]] = None,
    try_docx_pdf: bool = True,
) -> tuple[str, str]:
    """
    Cherche le premier blob existant parmi une liste de conteneurs et variantes d’extension.
    Retourne (container, blob_path) si trouvé, sinon lève 404.

    - try_docx_pdf=True essaie la variante .pdf <-> .docx.
    - Si containers est None, teste d’abord CONTAINER_DOCS puis CONTAINER_TRADING.
    """
    s = get_settings()
    path = _normalize_path(path)

    cands = [path]
    low = path.lower()
    if try_docx_pdf:
        if low.endswith(".pdf"):
            cands.append(path[:-4] + "docx")
        elif low.endswith(".docx"):
            cands.append(path[:-5] + "pdf")

    conts = list(containers) if containers else []
    if not conts:
        conts = [s.container_docs]
        if s.container_trading and s.container_trading not in conts:
            conts.append(s.container_trading)

    for c in conts:
        for p in cands:
            if blob_exists(c, p):
                return c, p

    raise HTTPException(
        status_code=404,
        detail={"error": "Blob introuvable", "containers": conts, "tried": cands},
    )
