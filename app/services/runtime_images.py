import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, unquote

from azure.storage.blob import generate_blob_sas, BlobSasPermissions


def _extract_container_and_blob_from_azure_url(url: str) -> Optional[Tuple[str, str]]:
    """
    Extrait (container, blob_name) depuis une URL Azure Blob, même si SAS expiré.
    Exemple:
      https://<account>.blob.core.windows.net/auditimage/10_bourges_bourges_photo_1.png?<sas>
      -> ("auditimage", "10_bourges_bourges_photo_1.png")
    """
    if not url or not isinstance(url, str):
        return None

    try:
        p = urlparse(url.strip())
        # path = "/container/blobname"
        path = (p.path or "").lstrip("/")
        if not path:
            return None

        parts = path.split("/", 1)
        if len(parts) != 2:
            return None

        container = parts[0].strip()
        blob_name = unquote(parts[1].strip())

        if not container or not blob_name:
            return None

        return container, blob_name
    except Exception:
        return None


def _make_fresh_sas_url(
    storage_account: str,
    storage_key: str,
    container: str,
    blob_name: str,
    minutes: int = 60,
) -> str:
    """
    Génère une SAS URL fraîche pour lecture.
    """
    import datetime

    sas = generate_blob_sas(
        account_name=storage_account,
        container_name=container,
        blob_name=blob_name,
        account_key=storage_key,
        permission=BlobSasPermissions(read=True),
        expiry=datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes),
    )
    return f"https://{storage_account}.blob.core.windows.net/{container}/{blob_name}?{sas}"


def refresh_image_blob_urls(
    image_blob_urls: List[str],
    *,
    storage_account: str,
    storage_key: str,
    minutes: int = 60,
    limit: int = 12,
) -> List[str]:
    """
    Prend image_blob_urls (SAS expirées ok) -> retourne des URLs SAS fraîches.
    """
    if not image_blob_urls:
        return []

    out: List[str] = []
    seen: set = set()

    for u in image_blob_urls:
        parsed = _extract_container_and_blob_from_azure_url(u)
        if not parsed:
            continue

        container, blob_name = parsed
        key = (container, blob_name)
        if key in seen:
            continue
        seen.add(key)

        fresh = _make_fresh_sas_url(
            storage_account=storage_account,
            storage_key=storage_key,
            container=container,
            blob_name=blob_name,
            minutes=minutes,
        )
        out.append(fresh)

        if len(out) >= limit:
            break

    return out
