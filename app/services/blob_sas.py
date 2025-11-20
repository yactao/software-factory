from typing import Optional
import datetime
import urllib.parse
from azure.storage.blob import (
    generate_blob_sas, 
    BlobSasPermissions, 
    BlobServiceClient
)
from ..core.config import ACCOUNT_NAME, ACCOUNT_KEY, CONTAINER, CONTAINER_TRADING

_BLOB_SVC = None


def _blob_service_client_cached() -> BlobServiceClient:
    global _BLOB_SVC
    if _BLOB_SVC is None:
        url = f"https://{ACCOUNT_NAME}.blob.core.windows.net"
        _BLOB_SVC = BlobServiceClient(account_url=url, credential=ACCOUNT_KEY)
    return _BLOB_SVC


def _blob_exists(container: str, blob_path: str) -> bool:
    svc = _blob_service_client_cached()
    try:
        blob_client = svc.get_blob_client(container, blob_path)
        return blob_client.exists()
    except Exception as e:
        print(f"[ERROR] _blob_exists failed for {container}/{blob_path}: {e}")
        return False


def _make_sas_url(container: str, blob_path: str, minutes: int = 60) -> str:
    """
    Génère une URL SAS valide pour un blob
    Version simplifiée et robuste
    """
    svc = _blob_service_client_cached()
    
    if not _blob_exists(container, blob_path):
        print(f"[WARNING] Blob n'existe pas: {container}/{blob_path}")
        return ""
    
    now = datetime.datetime.now(datetime.timezone.utc)
    start = now - datetime.timedelta(minutes=5) 
    expiry = now + datetime.timedelta(minutes=minutes)
    
    try:

        sas_token = generate_blob_sas(
            account_name=ACCOUNT_NAME,
            container_name=container,
            blob_name=blob_path,
            account_key=ACCOUNT_KEY,
            permission=BlobSasPermissions(read=True),
            start=start,
            expiry=expiry,
        )
        
        base_url = f"https://{ACCOUNT_NAME}.blob.core.windows.net/{container}/{blob_path}"
        full_url = f"{base_url}?{sas_token}"
        
 
        if 'sv=' in sas_token:
            sv_value = sas_token.split('sv=')[1].split('&')[0]
        
        return full_url
        
    except Exception as e:
        print(f"[ERROR] Échec génération SAS: {type(e).__name__}: {e}")
        import traceback
        print(traceback.format_exc())
        return ""