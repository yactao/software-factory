# app/services/blob_vision.py
import io, os, datetime as _dt
from typing import Optional, Tuple, List
from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

from app.core.config import AZURE_STORAGE_CONNECTION_STRING, ACCOUNT_NAME, ACCOUNT_KEY

_CONTAINER = "vision"
_BLOB_SVC = None
_CONT = None

def _blob_service():
    global _BLOB_SVC
    if _BLOB_SVC: return _BLOB_SVC
    if AZURE_STORAGE_CONNECTION_STRING:
        _BLOB_SVC = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING, logging_enable=False)
    elif ACCOUNT_NAME and ACCOUNT_KEY:
        _BLOB_SVC = BlobServiceClient(
            f"https://{ACCOUNT_NAME}.blob.core.windows.net",
            credential=ACCOUNT_KEY, logging_enable=False
        )
    else:
        raise RuntimeError("Blob config manquante (TABLE/Blob).")
    return _BLOB_SVC

def _container():
    global _CONT
    if _CONT: return _CONT
    svc = _blob_service()
    _CONT = svc.get_container_client(_CONTAINER)
    try:
        _CONT.create_container()  # idempotent
    except Exception:
        pass
    return _CONT

def put_temp(pk: str, conv_id: str, filename: str, data: bytes) -> str:
    """Upload binaire → retourne le blob path ex: pk/conv/file.jpg"""
    cont = _container()
    safe_name = filename.replace("\\", "_").replace("/", "_")
    blob_path = f"{pk}/{conv_id}/{safe_name}"
    cont.upload_blob(name=blob_path, data=data, overwrite=True)
    return blob_path

def put_jpeg(pk: str, conv_id: str, name: str, pil_img) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    return put_temp(pk, conv_id, name, buf.getvalue())

def sas_url(path: str, minutes: int = 120) -> str:
    svc = _blob_service()
    cont = _container()
    # permissions read only
    sas = generate_blob_sas(
        account_name=svc.account_name,
        container_name=cont.container_name,
        blob_name=path,
        account_key=ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=_dt.datetime.utcnow() + _dt.timedelta(minutes=minutes),
    )
    return f"{svc.primary_endpoint}{cont.container_name}/{path}?{sas}"

def delete_prefix(prefix: str) -> int:
    """Supprime tous les blobs sous un prefix. Retourne le nombre supprimé."""
    cont = _container()
    n = 0
    for b in cont.list_blobs(name_starts_with=prefix):
        cont.delete_blob(b.name)
        n += 1
    return n
