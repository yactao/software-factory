import os, io, tempfile
from typing import Optional, Tuple
from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from PIL import Image

from app.core.security import _auth_dependency, _require_scope
from app.models.schemas import AnalyzeResponse, Detection
from app.services.history_helpers import _save_chat_event
from app.services.vision_helpers import (
    _annotate_image,
    _normalize_target,
    _parse_scale,
    _pdf_to_image,
    _pil_to_base64,  # gardé si besoin du legacy
)
from app.utils.llm_interface import LLMInterface
from app.utils.vision_analysis import VisionAnalyzer
from app.utils.geometry_utils import (
    calculate_surface,
    calculate_perimeter,
    adapt_bbox,
    analyze_global,
)
from app.utils.response_generator import generate_response
from app.core.config import (
    AZURE_OAI_ENDPOINT,
    AZURE_OAI_KEY,
    AZURE_OAI_DEPLOYMENT,
    CV_ENDPOINT,
    CV_PRED_KEY,
    CV_PROJECT_ID,
    CV_PUBLISHED_NAME,
    CV_MIN_CONFIDENCE,
)

router = APIRouter()

# --- Clients globaux ---
llm_client = LLMInterface(
    endpoint=AZURE_OAI_ENDPOINT,
    api_key=AZURE_OAI_KEY,
    deployment=AZURE_OAI_DEPLOYMENT,
)

vision_client = VisionAnalyzer(
    endpoint=CV_ENDPOINT,
    prediction_key=CV_PRED_KEY,
    project_id=CV_PROJECT_ID,
    model_name=CV_PUBLISHED_NAME,
    min_confidence=CV_MIN_CONFIDENCE,
)


def _safe_float(x) -> float:
    """
    Convertit n'importe quoi en float de manière sûre.
    Si x est déjà un nombre, renvoie tel quel, sinon tente un cast.
    Lève HTTPException 500 si impossible.
    """
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip())
    except Exception:
        raise HTTPException(500, f"Valeur numérique attendue, reçu: {x!r}")


@router.post("/api/vision", response_model=AnalyzeResponse)
async def analyze_plan(
    file: Optional[UploadFile] = File(None, description="Image du plan png, jpg, jpeg, pdf"),
    prompt: str = Form(..., description="Instruction utilisateur"),
    m_per_pixel: Optional[float] = Form(0.02, description="Échelle m/pixel, ex 0.02"),
    # ⚠️ mettre une chaîne ici pour éviter que FastAPI n'évalue 1/100 → 0.01 float dans un champ str
    ratio: Optional[str] = Form("1/100", description="Échelle 1/n, ex 1/100"),
    return_image: bool = Form(True, description="Si vrai, renvoie une image annotée (SAS URL)"),
    conversation_id: Optional[str] = Form(None),
    claims: dict = Depends(_auth_dependency),
):
    _require_scope(claims)

    # Enregistrement de l’événement utilisateur
    conv_id = _save_chat_event(
        claims,
        conversation_id=conversation_id,
        role="user",
        route="vision",
        message=(f"[UPLOAD:{file.filename}] {prompt}" if file else prompt),
        meta={"return_image": return_image, "m_per_pixel": m_per_pixel, "ratio": ratio},
    )

    # Imports locaux pour éviter les cycles
    from app.services.history_helpers import _pk_from_claims, get_last_vision_file_path
    from app.services.blob_vision import put_temp, put_jpeg, sas_url, _container

    pk = _pk_from_claims(claims)

    # ------------------------------------------------------------------
    # 1) Récupération / upload du fichier source
    # ------------------------------------------------------------------
    pil_img = None
    vision_file_path: Optional[str] = None

    if file is not None:
        content = await file.read()
        if not content:
            raise HTTPException(400, "Fichier vide.")
        name = (file.filename or "upload").lower()

        if name.endswith(".pdf"):
            pil_img = _pdf_to_image(content)
            # on convertit en JPEG et on enregistre direct (source.jpg)
            vision_file_path = put_jpeg(pk, conv_id, "source.jpg", pil_img)
        else:
            # on stocke le binaire tel quel et on ouvre en PIL
            vision_file_path = put_temp(pk, conv_id, name, content)
            try:
                pil_img = Image.open(io.BytesIO(content)).convert("RGB")
            except Exception as e:
                raise HTTPException(400, f"Image invalide: {e}")

        _save_chat_event(
            claims,
            conv_id,
            role="meta",
            route="vision",
            message="",
            meta={"vision_file_path": vision_file_path},
        )
    else:
        # réutiliser le dernier fichier lié à cette conversation
        vision_file_path = get_last_vision_file_path(claims, conv_id)
        if not vision_file_path:
            raise HTTPException(400, "Aucun fichier image attaché à cette conversation.")
        # téléchargement depuis Blob
        from azure.storage.blob import BlobClient

        cont = _container()
        bc: BlobClient = cont.get_blob_client(vision_file_path)
        data = bc.download_blob().readall()
        name = vision_file_path.lower()
        if name.endswith(".pdf"):
            pil_img = _pdf_to_image(data)
        else:
            pil_img = Image.open(io.BytesIO(data)).convert("RGB")

    # ------------------------------------------------------------------
    # 2) Échelle & intention
    # ------------------------------------------------------------------
    scale_ratio = _parse_scale(m_per_pixel, ratio)

    try:
        intent_data = llm_client.analyze_request(prompt)
        intent = intent_data.get("intent", "analyse_globale")
        target = _normalize_target(intent_data.get("target"))
        _save_chat_event(
            claims,
            conv_id,
            role="meta",
            route="vision",
            message="",
            meta={"type": "vision_intent", "raw": intent_data},
        )
    except Exception:
        intent, target = "analyse_globale", None

    # ------------------------------------------------------------------
    # 3) Détection via Custom Vision
    # ------------------------------------------------------------------
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        pil_img.save(tmp.name, format="JPEG")
        tmp_path = tmp.name
    try:
        detections = vision_client.detect_objects(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

    W, H = pil_img.size

    if not detections:
        ans = AnalyzeResponse(
            intent=intent,
            target=target,
            surfaces={},
            perimeters={},
            response_text="Aucune détection trouvée sur l’image.",
            detections=[],
            annotated_image_b64=None,
            meta={
                "scale_ratio_m_per_px": scale_ratio,
                "image_size": {"width": W, "height": H},
                "return_image": return_image,
                "vision_file_path": vision_file_path,
            },
            conversation_id=conv_id,
        )
        _save_chat_event(
            claims, conv_id, role="assistant", route="vision",
            message=ans.response_text, meta=ans.model_dump()
        )
        out = ans.model_dump()
        if vision_file_path:
            out["vision_file_sas"] = sas_url(vision_file_path, minutes=180)
        return JSONResponse(status_code=200, content=out)

    # ------------------------------------------------------------------
    # 4) Post-traitement (surfaces / périmètres + image annotée)
    # ------------------------------------------------------------------
    surfaces, perimeters = {}, {}
    for d in detections:
        tag = d["tag_name"]
        bbox = adapt_bbox(d["bounding_box"])
        surfaces[tag] = calculate_surface(bbox, W, H, scale_ratio)
        perimeters[tag] = calculate_perimeter(bbox, W, H, scale_ratio)

    if target and isinstance(target, str):
        f_surfaces = {k: v for k, v in surfaces.items() if k.lower() == target.lower()}
        f_perimeters = {k: v for k, v in perimeters.items() if k.lower() == target.lower()}
    else:
        f_surfaces, f_perimeters = surfaces, perimeters

    if intent == "surface":
        response_text = "\n".join([f"{k} : {float(v):.2f} m²" for k, v in f_surfaces.items()]) or "Aucune surface trouvée."
    elif intent == "perimetre":
        response_text = "\n".join([f"{k} : {float(v):.2f} m" for k, v in f_perimeters.items()]) or "Aucun périmètre trouvé."
    elif intent == "detection_objets":
        counts = {}
        for d in detections:
            counts[d["tag_name"]] = counts.get(d["tag_name"], 0) + 1
        response_text = "Objets détectés:\n" + "\n".join([f"{k} : {v}" for k, v in counts.items()])
    else:
        total_surface, total_perimeter = analyze_global(f_surfaces, f_perimeters)
        total_surface = _safe_float(total_surface)
        total_perimeter = _safe_float(total_perimeter)
        response_text = f"Surface totale : {total_surface:.2f} m²\nPérimètre total : {total_perimeter:.2f} m"

    # Optionnel : LLM qui reformule la réponse avec contexte
    try:
        response_text = generate_response(intent, detections, f_surfaces, f_perimeters) or response_text
    except Exception:
        pass

    det_for_model = [
        Detection(
            tag_name=d["tag_name"],
            probability=float(d["probability"]),
            bounding_box=d["bounding_box"],
        ).model_dump()
        for d in detections
    ]

    # Image annotée → Blob (éviter base64 volumineux)
    from app.services.blob_vision import sas_url, put_jpeg  # reimport local
    annotated_blob_path: Optional[str] = None
    if return_image:
        annotated = _annotate_image(pil_img.copy(), detections)
        annotated_blob_path = put_jpeg(pk, conv_id, "annotated.jpg", annotated)

    payload = AnalyzeResponse(
        intent=intent,
        target=target,
        surfaces=f_surfaces,
        perimeters=f_perimeters,
        response_text=response_text,
        detections=det_for_model,
        annotated_image_b64=None,
        meta={
            "scale_ratio_m_per_px": scale_ratio,
            "image_size": {"width": W, "height": H},
            "return_image": return_image,
            "vision_file_path": vision_file_path,
            "vision_annotated_blob_path": annotated_blob_path,
        },
        conversation_id=conv_id,
    )

    _save_chat_event(
        claims, conv_id, role="assistant", route="vision",
        message=payload.response_text, meta=payload.model_dump()
    )

    # URLs SAS pour l’UI (source + annoté)
    out = payload.model_dump()
    if vision_file_path:
        out["vision_file_sas"] = sas_url(vision_file_path, minutes=180)
    if annotated_blob_path:
        out["vision_annotated_sas"] = sas_url(annotated_blob_path, minutes=180)

    return JSONResponse(status_code=200, content=out)
