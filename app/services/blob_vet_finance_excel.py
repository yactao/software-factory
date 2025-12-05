# app/services/blob_vet_finance_excel.py
import os
import tempfile
from pathlib import Path

import requests
from fastapi import HTTPException

from app.core.config import VET_FINANCE_CONTAINER, VET_FINANCE_BLOB_PATH
from app.services.blob_sas import _make_sas_url


def download_vet_finance_excel_to_temp() -> Path:
    """
    Télécharge le fichier Excel Vet Finance depuis Azure Blob dans un fichier temporaire
    et retourne le Path vers ce fichier.
    """
    container = VET_FINANCE_CONTAINER
    blob_path = VET_FINANCE_BLOB_PATH

    if not container or not blob_path:
        raise HTTPException(
            500,
            "VET_FINANCE_CONTAINER ou VET_FINANCE_BLOB_PATH non configurés."
        )

    sas_url = _make_sas_url(container, blob_path, minutes=60)
    if not sas_url:
        raise HTTPException(
            500,
            f"Impossible de générer une URL SAS pour le blob Vet Finance {container}/{blob_path}."
        )

    try:
        resp = requests.get(sas_url, timeout=120)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(502, f"Erreur lors du téléchargement du fichier Vet Finance: {e}")

    # Extension .ods si ton fichier est au format LibreOffice
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".ods")
    with os.fdopen(tmp_fd, "wb") as f:
        f.write(resp.content)

    return Path(tmp_path)
