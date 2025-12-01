# app/services/blob_global_pdf.py

import os
import tempfile
from pathlib import Path
from typing import Tuple

import requests
from fastapi import HTTPException

from app.core.config import GLOBAL_AUDIT_CONTAINER, GLOBAL_AUDIT_BLOB_PATH
from app.services.blob_sas import _make_sas_url
# adapte l’import ci-dessus au fichier où se trouvent _make_sas_url, _blob_exists...


def download_global_audit_pdf_to_temp() -> Path:
    """
    Télécharge le PDF global depuis Azure Blob dans un fichier temporaire
    et retourne le Path vers ce fichier.
    """
    container = GLOBAL_AUDIT_CONTAINER
    blob_path = GLOBAL_AUDIT_BLOB_PATH

    if not container or not blob_path:
        raise HTTPException(
            500, "GLOBAL_AUDIT_CONTAINER ou GLOBAL_AUDIT_BLOB_PATH non configurés."
        )

    sas_url = _make_sas_url(container, blob_path, minutes=60)
    if not sas_url:
        raise HTTPException(
            500,
            f"Impossible de générer une URL SAS pour le blob global {container}/{blob_path}.",
        )

    try:
        resp = requests.get(sas_url, timeout=120)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(502, f"Erreur lors du téléchargement du PDF global: {e}")

    # Ecrit le contenu dans un fichier temporaire .pdf
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(tmp_fd, "wb") as f:
        f.write(resp.content)

    return Path(tmp_path)
