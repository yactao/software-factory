"""
API api/vision/plan/analyse
Même logique que plan_annotator_pro + pipeline_auto (aina vision architecture) :
- avec image : détection Custom Vision -> annotations ; sans image : réutilisation dernière image + annotations (éventuellement modifiées)
- si prompt fourni : calibration, surfaces/périmètres m²/m, réponse à la question (LLM)
Retourne : image, image_width, image_height, annotations, response_text, surfaces, perimeters (total + par pièce).
"""
import io
import json
import tempfile
from typing import List, Dict, Any, Optional

from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from PIL import Image

from app.core.security import _auth_dependency
from app.core.config import (
    CV_ENDPOINT,
    CV_PRED_KEY,
    CV_PROJECT_ID,
    CV_PUBLISHED_NAME,
    CV_MIN_CONFIDENCE,
)
from app.routers.architecture.modules.vision_analysis import VisionAnalyzer
from app.utils.plan_calibration import get_scale_ratio as calibration_scale_ratio
from app.services.architecture_pipeline import run_architecture_auto
from app.services.history_helpers import _pk_from_claims, _gen_conversation_id
from app.services.blob_architecture import put_jpeg_arch, put_json_arch, sas_url_arch, download_arch, get_annotations_arch

router = APIRouter()

_vision_client: VisionAnalyzer | None = None


def _get_vision_client() -> VisionAnalyzer:
    global _vision_client
    if _vision_client is None:
        _vision_client = VisionAnalyzer(
            endpoint=CV_ENDPOINT,
            prediction_key=CV_PRED_KEY,
            model_name=CV_PUBLISHED_NAME,
            project_id=CV_PROJECT_ID,
            min_confidence=CV_MIN_CONFIDENCE,
        )
    return _vision_client


def _annotations_from_detections(
    detections: List[Dict], w: int, h: int
) -> List[dict]:
    """Construit la liste d'annotations (pixels) à partir des detections (bbox normalisées)."""
    annotations: List[dict] = []
    for idx, det in enumerate(detections):
        bb = det.get("bounding_box") or {}
        left = float(bb.get("left", 0)) * w
        top = float(bb.get("top", 0)) * h
        width = float(bb.get("width", 0)) * w
        height = float(bb.get("height", 0)) * h
        tag_name = det.get("tag_name", "zone")
        annotations.append({
            "id": f"ai-{idx}-{tag_name}",
            "type": "rect",
            "left": round(left, 2),
            "top": round(top, 2),
            "width": round(width, 2),
            "height": round(height, 2),
            "label": tag_name,
            "surface": round(width * height, 2),
            "perimeter": round(2 * (width + height), 2),
        })
    return annotations


def _run_plan_analyse(
    pil_image: Image.Image,
    prompt: str = "",
    reference_length_m: float = 10.0,
    detections: Optional[List[Dict]] = None,
) -> dict:
    """
    Si detections fourni : utilise ces détections (ex. chargées depuis blob après édition).
    Sinon : détection Custom Vision.
    Puis annotations (pixels) + si prompt : pipeline (calibration, surfaces m²/m, réponse user).
    """
    w, h = pil_image.size
    if detections is None:
        client = _get_vision_client()
        detections = client.detect_objects_pil(pil_image)

    annotations = _annotations_from_detections(detections, w, h)

    result: Dict[str, Any] = {
        "image_width": w,
        "image_height": h,
        "annotations": annotations,
        "response_text": "",
        "surfaces": {},
        "perimeters": {},
        "total_surface": 0.0,
        "total_perimeter": 0.0,
        "intent": None,
        "target": None,
    }

    if not prompt or not detections:
        return result

    # Calibration (comme pipeline_auto / test_pipeline_manual)
    ref = float(reference_length_m) if reference_length_m > 0 else 10.0
    scale_ratio = ref / float(max(w, h)) if max(w, h) > 0 else 0.02
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        pil_image.save(tmp.name, format="JPEG")
        tmp_path = tmp.name
    try:
        cal_ratio = calibration_scale_ratio(tmp_path, ref)
        if cal_ratio is not None and cal_ratio > 0:
            scale_ratio = cal_ratio
    finally:
        try:
            import os
            os.remove(tmp_path)
        except Exception:
            pass

    # Réponse à la question (comme plan_annotator_pro / pipeline_auto)
    response_text, intent, target, surfaces, perimeters = run_architecture_auto(
        prompt, detections, w, h, scale_ratio
    )
    result["response_text"] = response_text
    result["surfaces"] = surfaces
    result["perimeters"] = perimeters
    result["intent"] = intent
    result["target"] = target
    # Totaux explicites (comme test_pipeline_auto / test_pipeline_manual)
    result["total_surface"] = round(surfaces.get("total", 0.0), 2)
    result["total_perimeter"] = round(perimeters.get("total", 0.0), 2)
    return result


def _load_detections_from_annotations_json(
    ann_bytes: bytes, img_width: int, img_height: int
) -> List[Dict]:
    """
    Convertit le JSON d'annotations (sauvegardé après première analyse ou après édition)
    en liste de detections au format attendu par run_architecture_auto (bounding_box normalisée).
    """
    detections: List[Dict] = []
    try:
        ann_list = json.loads(ann_bytes.decode("utf-8"))
        if not isinstance(ann_list, list):
            return detections
        for item in ann_list:
            bbox = item.get("bbox") or {}
            left_n = bbox.get("x")
            top_n = bbox.get("y")
            width_n = bbox.get("w")
            height_n = bbox.get("h")
            if left_n is None and "left" in item:
                left_n = float(item["left"]) / img_width
                top_n = float(item["top"]) / img_height
                width_n = float(item["width"]) / img_width
                height_n = float(item["height"]) / img_height
            else:
                left_n = float(left_n) if left_n is not None else 0.0
                top_n = float(top_n) if top_n is not None else 0.0
                width_n = float(width_n) if width_n is not None else 0.0
                height_n = float(height_n) if height_n is not None else 0.0
            detections.append({
                "tag_name": item.get("label", "zone"),
                "bounding_box": {
                    "left": left_n,
                    "top": top_n,
                    "width": width_n,
                    "height": height_n,
                },
            })
    except (json.JSONDecodeError, TypeError, KeyError):
        pass
    return detections


@router.post("/api/vision/plan/analyse")
async def plan_analyse(
    file: Optional[UploadFile] = File(None),
    prompt: str = Form(""),
    conversation_id: str | None = Form(None),
    reference_length_m: float = Form(10.0),
    claims: dict = Depends(_auth_dependency),
) -> dict:
    """
    Analyse d'un plan :
    - Avec image : détection Custom Vision -> annotations ; sauvegarde image + annotations en blob.
    - Sans image (conversation_id requis) : réutilise la dernière image et les annotations (éventuellement modifiées).
    - Si prompt fourni : calibration, surfaces/périmètres, réponse à la question.
    """
    pk = _pk_from_claims(claims)
    conv_id = conversation_id or _gen_conversation_id()

    if file is not None and file.filename:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(400, "Fichier image requis (jpg, png, ...).")
        content = await file.read()
        if not content:
            raise HTTPException(400, "Fichier vide.")
        try:
            pil_image = Image.open(io.BytesIO(content)).convert("RGB")
        except Exception as e:
            raise HTTPException(400, f"Image invalide: {e}")
        result = _run_plan_analyse(
            pil_image, prompt=prompt, reference_length_m=reference_length_m
        )
        try:
            blob_path = put_jpeg_arch(pk, conv_id, "image.png", pil_image)
            result["image"] = sas_url_arch(blob_path, minutes=180)
            result["conversation_id"] = conv_id
            annotations_bytes = json.dumps(
                result["annotations"], ensure_ascii=False, indent=2
            ).encode("utf-8")
            put_json_arch(pk, conv_id, "annotations.json", annotations_bytes)
        except Exception:
            result["image"] = result.get("image") or ""
            result["conversation_id"] = conv_id
        return result

    # Sans fichier : réutiliser dernière image + annotations (comme api/aina/vision/architecture/analyze)
    if not conversation_id:
        raise HTTPException(
            400,
            "Sans nouvelle image, conversation_id est requis pour réutiliser le plan.",
        )
    blob_path = f"{pk}/{conv_id}/image.png"
    try:
        data = download_arch(blob_path)
    except Exception:
        raise HTTPException(
            400,
            "Aucune image de plan pour cette conversation. Uploadez une image.",
        )
    try:
        pil_image = Image.open(io.BytesIO(data)).convert("RGB")
    except Exception as e:
        raise HTTPException(400, f"Image invalide: {e}")
    w, h = pil_image.size

    detections: List[Dict] = []
    ann_bytes = get_annotations_arch(pk, conv_id)
    if ann_bytes:
        detections = _load_detections_from_annotations_json(ann_bytes, w, h)
    if not detections:
        client = _get_vision_client()
        detections = client.detect_objects_pil(pil_image)
        if detections:
            annotations_bytes = json.dumps(
                _annotations_from_detections(detections, w, h),
                ensure_ascii=False,
                indent=2,
            ).encode("utf-8")
            put_json_arch(pk, conv_id, "annotations.json", annotations_bytes)

    result = _run_plan_analyse(
        pil_image,
        prompt=prompt,
        reference_length_m=reference_length_m,
        detections=detections,
    )
    try:
        result["image"] = sas_url_arch(blob_path, minutes=180)
    except Exception:
        result["image"] = ""
    result["conversation_id"] = conv_id
    return result
