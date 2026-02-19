# app/services/blob_trading_finance_excel.py
"""
List and download Excel (.xlsx) blobs from a single Azure Blob container.
Used by the trading-finance multi-Excel agent. Does not require FINANCE_BLOB_PATH.
"""

import os
import tempfile
from pathlib import Path
from typing import List

from azure.storage.blob import BlobServiceClient
from fastapi import HTTPException

from app.core.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    ACCOUNT_NAME,
    ACCOUNT_KEY,
)


def _blob_service_client() -> BlobServiceClient:
    """Create a BlobServiceClient from config. No global cache."""
    conn = (AZURE_STORAGE_CONNECTION_STRING or "").strip()
    if conn:
        return BlobServiceClient.from_connection_string(conn)
    if not (ACCOUNT_NAME and ACCOUNT_KEY):
        raise HTTPException(
            500,
            "Storage non configuré: définir AZURE_STORAGE_CONNECTION_STRING ou "
            "AZURE_STORAGE_ACCOUNT + AZURE_STORAGE_ACCOUNT_KEY.",
        )
    url = f"https://{ACCOUNT_NAME}.blob.core.windows.net"
    return BlobServiceClient(account_url=url, credential=ACCOUNT_KEY)


def list_excel_blobs_in_container(container: str) -> List[str]:
    """
    List all blob names in the container that are .xlsx and not temporary Office files.
    Returns a list of blob paths (names) suitable for download_excel_blob_to_temp.
    """
    if not (container or str(container).strip()):
        raise HTTPException(500, "Nom de container vide.")

    container = str(container).strip()
    try:
        client = _blob_service_client()
        container_client = client.get_container_client(container)
        if not container_client.exists():
            raise HTTPException(500, f"Le container Azure Blob '{container}' n'existe pas.")

        out: List[str] = []
        for blob in container_client.list_blobs():
            name = (blob.name or "").strip()
            if not name:
                continue
            # Skip Office lock files
            if name.startswith("~$"):
                continue
            # Only .xlsx
            if not name.lower().endswith(".xlsx"):
                continue
            # Skip zero-size if metadata available
            size = getattr(blob, "size", None)
            if size is not None and size == 0:
                continue
            out.append(name)

        return sorted(out)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            500,
            f"Erreur lors de la liste des blobs Excel dans '{container}': {e}",
        )


def download_excel_blob_to_temp(container: str, blob_path: str) -> Path:
    """
    Download the given blob to a temporary .xlsx file and return its Path.
    Caller is responsible for cleaning up the temp file when done.
    """
    if not (container or str(container).strip()):
        raise HTTPException(500, "Nom de container vide.")
    if not (blob_path or str(blob_path).strip()):
        raise HTTPException(500, "Chemin du blob vide.")

    container = str(container).strip()
    blob_path = str(blob_path).strip()

    try:
        client = _blob_service_client()
        blob_client = client.get_blob_client(container=container, blob=blob_path)
        if not blob_client.exists():
            raise HTTPException(
                404,
                f"Blob introuvable: {container}/{blob_path}",
            )

        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".xlsx", prefix="finance_")
        try:
            with os.fdopen(tmp_fd, "wb") as f:
                download = blob_client.download_blob()
                f.write(download.readall())
        except Exception:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
            raise

        return Path(tmp_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            500,
            f"Erreur lors du téléchargement du blob {container}/{blob_path}: {e}",
        )
