# app/services/blob_finance_excel.py

import os
import tempfile
from pathlib import Path

import requests
from fastapi import HTTPException

from app.core.config import FINANCE_CONTAINER, FINANCE_BLOB_PATH
from app.services.blob_sas import _make_sas_url


def download_finance_excel_to_temp() -> Path:
    """
    Télécharge le fichier Excel finance depuis Azure Blob dans un fichier temporaire
    et retourne le Path vers ce fichier.
    """
    container = FINANCE_CONTAINER
    blob_path = FINANCE_BLOB_PATH

    if not container or not blob_path:
        raise HTTPException(
            500,
            "FINANCE_CONTAINER ou FINANCE_BLOB_PATH non configurés."
        )

    sas_url = _make_sas_url(container, blob_path, minutes=60)
    if not sas_url:
        raise HTTPException(
            500,
            f"Impossible de générer une URL SAS pour le blob finance {container}/{blob_path}."
        )

    try:
        resp = requests.get(sas_url, timeout=120)
        resp.raise_for_status()
    except Exception as e:
        raise HTTPException(502, f"Erreur lors du téléchargement du fichier Excel finance: {e}")

    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx")
    with os.fdopen(tmp_fd, "wb") as f:
        f.write(resp.content)

    return Path(tmp_path)
