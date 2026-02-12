import io
import datetime as _dt
from typing import Tuple

from azure.storage.blob import BlobServiceClient, BlobSasPermissions, generate_blob_sas

from app.core.config import (
    AZURE_STORAGE_CONNECTION_STRING,
    ACCOUNT_NAME,
    ACCOUNT_KEY,
    ARCHITECTURE_IMAGE_CONTAINER,
)

_CONTAINER = ARCHITECTURE_IMAGE_CONTAINER or "architecture-images"
_BLOB_SVC: BlobServiceClient | None = None
_CONT = None


def _blob_service() -> BlobServiceClient:
    global _BLOB_SVC
    if _BLOB_SVC:
        return _BLOB_SVC
    if AZURE_STORAGE_CONNECTION_STRING:
        _BLOB_SVC = BlobServiceClient.from_connection_string(
            AZURE_STORAGE_CONNECTION_STRING, logging_enable=False
        )
    elif ACCOUNT_NAME and ACCOUNT_KEY:
        _BLOB_SVC = BlobServiceClient(
            f"https://{ACCOUNT_NAME}.blob.core.windows.net",
            credential=ACCOUNT_KEY,
            logging_enable=False,
        )
    else:
        raise RuntimeError("Blob config manquante pour architecture-images.")
    return _BLOB_SVC


def _container():
    global _CONT
    if _CONT:
        return _CONT
    svc = _blob_service()
    _CONT = svc.get_container_client(_CONTAINER)
    try:
        _CONT.create_container()
    except Exception:
        # Container peut déjà exister, ce n'est pas bloquant
        pass
    return _CONT


def put_temp_arch(pk: str, conv_id: str, filename: str, data: bytes) -> str:
    """
    Upload binaire dans le conteneur architecture-images.
    Retourne le blob path ex: pk/conv_id/file.jpg
    """
    cont = _container()
    safe_name = filename.replace("\\", "_").replace("/", "_")
    blob_path = f"{pk}/{conv_id}/{safe_name}"
    cont.upload_blob(name=blob_path, data=data, overwrite=True)
    return blob_path


def put_jpeg_arch(pk: str, conv_id: str, name: str, pil_img) -> str:
    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=90)
    return put_temp_arch(pk, conv_id, name, buf.getvalue())


def put_json_arch(pk: str, conv_id: str, name: str, json_bytes: bytes) -> str:
    """
    Stocke un JSON (annotations, métadonnées) sous pk/conv_id/name.
    """
    cont = _container()
    safe_name = name.replace("\\", "_").replace("/", "_")
    blob_path = f"{pk}/{conv_id}/{safe_name}"
    cont.upload_blob(name=blob_path, data=json_bytes, overwrite=True)
    return blob_path


def download_arch(path: str) -> bytes:
    """Télécharge un blob architecture-images et renvoie son contenu binaire."""
    cont = _container()
    bc = cont.get_blob_client(path)
    return bc.download_blob().readall()


def get_annotations_arch(pk: str, conv_id: str) -> bytes | None:
    """
    Récupère le fichier annotations.json pour cette conversation si il existe.
    Retourne None si le blob n'existe pas (première analyse ou pas encore d'annotations).
    """
    try:
        path = f"{pk}/{conv_id}/annotations.json"
        return download_arch(path)
    except Exception:
        return None


def sas_url_arch(path: str, minutes: int = 120) -> str:
    """
    Génère une URL SAS en lecture seule pour un blob architecture-images.
    """
    svc = _blob_service()
    cont = _container()
    sas = generate_blob_sas(
        account_name=svc.account_name,
        container_name=cont.container_name,
        blob_name=path,
        account_key=ACCOUNT_KEY,
        permission=BlobSasPermissions(read=True),
        expiry=_dt.datetime.utcnow() + _dt.timedelta(minutes=minutes),
    )
    return f"{svc.primary_endpoint}{cont.container_name}/{path}?{sas}"


def prefix_from_blob_path(path: str) -> Tuple[str, str]:
    """
    Retourne (prefix, filename) à partir d'un blob path pk/conv_id/file.
    """
    parts = path.split("/")
    if len(parts) < 3:
        return "/".join(parts[:-1]), parts[-1]
    return "/".join(parts[:-1]), parts[-1]

