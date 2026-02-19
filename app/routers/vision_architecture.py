import io
import json
import tempfile
from typing import List, Dict, Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from PIL import Image
from azure.storage.blob import BlobClient

from app.core.security import _auth_dependency, _require_scope
from app.services.history_helpers import (
    _save_chat_event,
    _pk_from_claims,
    get_last_architecture_file_path,
    _gen_conversation_id,
)
from app.utils.vision_analysis import VisionAnalyzer
from app.core.config import (
    CV_ENDPOINT,
    CV_PRED_KEY,
    CV_PROJECT_ID,
    CV_PUBLISHED_NAME,
    CV_MIN_CONFIDENCE,
)
from app.services.blob_architecture import (
    put_temp_arch,
    put_jpeg_arch,
    put_json_arch,
    sas_url_arch,
    prefix_from_blob_path,
    get_annotations_arch,
    download_arch,
)
from app.services.architecture_helpers import draw_architecture_annotations
from app.services.architecture_pipeline import run_architecture_auto
from app.utils.geometry_utils import adapt_bbox, calculate_surface, calculate_perimeter
from app.utils.plan_calibration import get_scale_ratio as calibration_scale_ratio


router = APIRouter()

architecture_vision_client = VisionAnalyzer(
    endpoint=CV_ENDPOINT,
    prediction_key=CV_PRED_KEY,
    project_id=CV_PROJECT_ID,
    model_name=CV_PUBLISHED_NAME,
    min_confidence=CV_MIN_CONFIDENCE,
)


class BBoxNorm(BaseModel):
    x: float = Field(..., ge=0.0, le=1.0)
    y: float = Field(..., ge=0.0, le=1.0)
    w: float = Field(..., ge=0.0, le=1.0)
    h: float = Field(..., ge=0.0, le=1.0)


class BBoxPx(BaseModel):
    """Coordonnées en pixels (float pour les vrais pixels, ex. 273.95)."""
    x: float
    y: float
    w: float
    h: float


class ArchitectureAnnotation(BaseModel):
    """Format aligné plan_annotator_pro / annotations.json : id, type, left/top/width/height, label, surface, perimeter."""
    id: str
    label: str
    bbox: BBoxNorm
    bbox_px: BBoxPx
    type: str = "rect"
    surface: Optional[float] = None  # m²
    perimeter: Optional[float] = None  # m
    # Champs pixels au même nom que annotations.json pour compatibilité AnnotationLoader / plan_annotator_pro
    left: Optional[float] = None
    top: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None


class ArchitectureAnalyzeResponse(BaseModel):
    image: str
    image_width: int
    image_height: int
    annotations: List[ArchitectureAnnotation]
    # Résultats analytiques comme dans pipeline_auto / test_pipeline_manual
    response_text: str
    intent: Optional[str] = None
    target: Optional[str] = None
    surfaces: Dict[str, float] = {}
    perimeters: Dict[str, float] = {}
    total_surface: Optional[float] = None
    total_perimeter: Optional[float] = None
    conversation_id: Optional[str] = None


class ArchitectureAnnotateRequest(BaseModel):
    image: str
    image_width: int
    image_height: int
    annotations: List[ArchitectureAnnotation]


class ArchitectureAnnotateResponse(BaseModel):
    annotated_image_url: str


@router.post(
    "/api/aina/vision/architecture/analyze",
    response_model=ArchitectureAnalyzeResponse,
)
async def architecture_analyze(
    file: Optional[UploadFile] = File(
        None, description="Image du plan (png, jpg, jpeg)"
    ),
    prompt: str = Form(..., description="Instruction utilisateur (texte libre)"),
    conversation_id: Optional[str] = Form(None),
    reference_length_m: float = Form(10.0, description="Longueur de référence en mètres pour la calibration (défaut: 10)"),
    claims: Dict = Depends(_auth_dependency),
):
    """
    API 1 – Analyse d'un plan d'architecture.

    - Entrée: image + prompt (pour historique, réservé à un usage futur)
    - Sortie: URL SAS de l'image originale, dimensions, et annotations normalisées.
    """
    _require_scope(claims)

    upload_info = f"[UPLOAD:{file.filename}]" if file else "[NO_UPLOAD]"
    try:
        conv_id = _save_chat_event(
            claims,
            conversation_id=conversation_id,
            role="user",
            route="vision_architecture",
            message=f"{upload_info} {prompt}",
            meta={},
        )
    except Exception:
        conv_id = conversation_id or _gen_conversation_id()

    pk = _pk_from_claims(claims)

    if file is not None:
        content = await file.read()
        if not content:
            raise HTTPException(400, "Fichier vide.")

        try:
            pil_img = Image.open(io.BytesIO(content)).convert("RGB")
        except Exception as e:
            raise HTTPException(400, f"Image invalide: {e}")

        W, H = pil_img.size

        # Upload de l'image originale dans le conteneur architecture-images
        image_blob_path = put_temp_arch(
            pk, conv_id, file.filename or "plan.jpg", content
        )

        # Sauvegarder le chemin du fichier dans l'historique (pour réutilisation)
        try:
            _save_chat_event(
                claims,
                conv_id,
                role="meta",
                route="vision_architecture",
                message="",
                meta={"architecture_file_path": image_blob_path},
            )
        except Exception:
            pass
    else:
        # Réutiliser la dernière image de cette conversation
        last_path = get_last_architecture_file_path(claims, conv_id)
        if not last_path:
            raise HTTPException(
                400,
                "Aucune image de plan trouvée pour cette conversation. Merci d'en uploader une.",
            )
        data = download_arch(last_path)
        try:
            pil_img = Image.open(io.BytesIO(data)).convert("RGB")
        except Exception as e:
            raise HTTPException(400, f"Image invalide: {e}")
        W, H = pil_img.size
        image_blob_path = last_path

    # Calibration : fallback = plus grand côté = reference_length_m ; si on a un fichier
    # temporaire plus tard, on utilisera plan_calibration (détection plus longue ligne, comme Calibration.py).
    ref = float(reference_length_m) if reference_length_m > 0 else 10.0
    try:
        base = float(max(W, H))
        scale_ratio = ref / base if base > 0 else 0.02
    except Exception:
        scale_ratio = 0.02

    # Mode manuel (comme pipeline_auto) : si des annotations ont été enregistrées
    # (après première analyse ou après "Réajuster les annotations"), on les utilise
    # pour répondre à la question suivante au lieu de relancer Custom Vision.
    detections: List[Dict] = []
    if file is None:
        ann_bytes = get_annotations_arch(pk, conv_id)
        if ann_bytes:
            try:
                ann_list = json.loads(ann_bytes.decode("utf-8"))
                if isinstance(ann_list, list) and len(ann_list) > 0:
                    for item in ann_list:
                        b = item.get("bbox") or {}
                        detections.append({
                            "tag_name": item.get("label", "zone"),
                            "bounding_box": {
                                "left": float(b.get("x", 0)),
                                "top": float(b.get("y", 0)),
                                "width": float(b.get("w", 0)),
                                "height": float(b.get("h", 0)),
                            },
                        })
            except (json.JSONDecodeError, TypeError, KeyError):
                pass

    if not detections:
        # Détection via Custom Vision (première fois ou pas d'annotations enregistrées)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            pil_img.save(tmp.name, format="JPEG")
            tmp_path = tmp.name
        try:
            # Calibration comme Calibration.py : plus longue ligne -> ratio m/pixel
            cal_ratio = calibration_scale_ratio(tmp_path, ref)
            if cal_ratio is not None and cal_ratio > 0:
                scale_ratio = cal_ratio
            detections = architecture_vision_client.detect_objects(tmp_path)
        finally:
            try:
                import os
                os.remove(tmp_path)
            except Exception:
                pass

    # === 3) Alignement avec pipeline_auto : analyse LLM + surfaces/périmètres ===
    # Detections est déjà au format {tag_name, probability, bounding_box}
    response_text, intent, target, surfaces, perimeters = run_architecture_auto(
        prompt, detections, W, H, scale_ratio
    )

    # === 4) Construction des annotations (format plan_annotator_pro / annotations.json) ===
    # toPixels: bbox normalisée -> left, top, width, height en pixels (float); surface/périmètre en pixels
    annotations: List[ArchitectureAnnotation] = []
    for idx, det in enumerate(detections):
        bb = det.get("bounding_box") or {}
        left_n = float(bb.get("left", 0.0))
        top_n = float(bb.get("top", 0.0))
        width_n = float(bb.get("width", 0.0))
        height_n = float(bb.get("height", 0.0))

        # toPixels(bbox, imageWidth, imageHeight) -> left, top, width, height en pixels (float)
        left_px = left_n * W
        top_px = top_n * H
        width_px = width_n * W
        height_px = height_n * H

        # Surface et périmètre en pixels (comme plan_annotator_pro / test_pipeline_manual)
        surface_px = width_px * height_px
        perimeter_px = 2.0 * (width_px + height_px)

        ann = ArchitectureAnnotation(
            id=f"ai-{idx}-{det.get('tag_name', 'zone')}",
            label=det.get("tag_name", "zone"),
            bbox=BBoxNorm(x=left_n, y=top_n, w=width_n, h=height_n),
            bbox_px=BBoxPx(x=round(left_px), y=round(top_px), w=round(width_px), h=round(height_px)),
            type="rect",
            surface=round(surface_px, 2),
            perimeter=round(perimeter_px, 2),
            left=round(left_px, 2),
            top=round(top_px, 2),
            width=round(width_px, 2),
            height=round(height_px, 2),
        )
        annotations.append(ann)

    # Stocker les annotations JSON pour ce plan
    annotations_bytes = json.dumps(
        [ann.model_dump() for ann in annotations], ensure_ascii=False, indent=2
    ).encode("utf-8")
    put_json_arch(pk, conv_id, "annotations.json", annotations_bytes)

    image_sas = sas_url_arch(image_blob_path, minutes=180)

    resp = ArchitectureAnalyzeResponse(
        image=image_sas,
        image_width=W,
        image_height=H,
        annotations=annotations,
        response_text=response_text,
        intent=intent,
        target=target,
        surfaces=surfaces,
        perimeters=perimeters,
        total_surface=round(surfaces.get("total", 0.0), 2),
        total_perimeter=round(perimeters.get("total", 0.0), 2),
        conversation_id=conv_id,
    )

    try:
        _save_chat_event(
            claims,
            conv_id,
            role="assistant",
            route="vision_architecture",
            message=response_text[:32000] if response_text else "Analyse de plan effectuée.",
            meta=resp.model_dump(),
        )
    except Exception:
        pass

    return resp


@router.post(
    "/api/aina/vision/architecture/annotate",
    response_model=ArchitectureAnnotateResponse,
)
async def architecture_annotate(
    body: ArchitectureAnnotateRequest,
    claims: Dict = Depends(_auth_dependency),
):
    """
    API 2 – Génération d'une image annotée personnalisée.

    - Entrée: JSON (image, dimensions, annotations ajustées par l'utilisateur)
    - Sortie: URL SAS de l'image annotée enregistrée dans architecture-images.
    """
    _require_scope(claims)

    if not body.image:
        raise HTTPException(400, "Champ 'image' obligatoire.")

    # Télécharger l'image source depuis l'URL SAS fournie
    try:
        blob_client = BlobClient.from_blob_url(body.image)
        data = blob_client.download_blob().readall()
        pil_img = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"Impossible de télécharger l'image source: {e}")

    # Dessiner les annotations mises à jour
    ann_dicts: List[Dict] = [ann.model_dump() for ann in body.annotations]
    annotated_img = draw_architecture_annotations(pil_img, ann_dicts)

    # Extraire le blob path (sans le compte / container) pour retrouver le prefix
    # URL attendue : https://account.blob.core.windows.net/container/path?SAS
    after_account = body.image.split(".net/", 1)[-1]
    container_and_blob = after_account.split("?", 1)[0]
    parts = container_and_blob.split("/", 1)
    blob_path = parts[1] if len(parts) == 2 else parts[0]

    prefix, _ = prefix_from_blob_path(blob_path)
    pk = _pk_from_claims(claims)
    # On réutilise le même conv_id/prefix si possible; à défaut, on stocke sous pk/prefix
    conv_id = prefix.split("/", 1)[1] if "/" in prefix else "arch"

    # Sauvegarder la nouvelle image annotée
    annotated_blob_path = put_jpeg_arch(pk, conv_id, "annotated.jpg", annotated_img)
    annotated_sas = sas_url_arch(annotated_blob_path, minutes=180)

    # Mettre à jour le JSON d'annotations pour ce plan
    annotations_bytes = json.dumps(ann_dicts, ensure_ascii=False, indent=2).encode(
        "utf-8"
    )
    put_json_arch(pk, conv_id, "annotations.json", annotations_bytes)

    return ArchitectureAnnotateResponse(annotated_image_url=annotated_sas)

