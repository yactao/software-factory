from typing import Optional
import datetime, urllib.parse
from azure.storage.blob import generate_blob_sas, BlobSasPermissions, BlobServiceClient
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
    except Exception:
        return False


def _make_sas_url(container: str, blob_path: str, minutes: int = 5) -> str:
    svc = _blob_service_client_cached()
    if not _blob_exists(container, blob_path):
        return ""
    expiry = datetime.datetime.utcnow() + datetime.timedelta(minutes=minutes)
    sas = generate_blob_sas(
        account_name=ACCOUNT_NAME,
        container_name=container,
        blob_name=blob_path,
        account_key=ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=expiry,
    )
    return f"https://{ACCOUNT_NAME}.blob.core.windows.net/{container}/{urllib.parse.quote(blob_path)}?{sas}"
