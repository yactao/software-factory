from typing import List, Dict, Any, Tuple

from app.utils.llm_interface import LLMInterface
from app.utils.geometry_utils import calculate_surface, calculate_perimeter, adapt_bbox
from app.utils.response_generator import ResponseGenerator
from app.core.config import (
    AZURE_OAI_ENDPOINT,
    AZURE_OAI_KEY,
    AZURE_OAI_DEPLOYMENT,
)


_llm_arch = LLMInterface(
    endpoint=AZURE_OAI_ENDPOINT,
    api_key=AZURE_OAI_KEY,
    deployment=AZURE_OAI_DEPLOYMENT,
)
_response_generator = ResponseGenerator(
    endpoint=AZURE_OAI_ENDPOINT,
    api_key=AZURE_OAI_KEY,
    deployment=AZURE_OAI_DEPLOYMENT,
)


def run_architecture_auto(
    prompt: str,
    detections: List[Dict[str, Any]],
    img_width: int,
    img_height: int,
    scale_ratio: float = 0.02,
) -> Tuple[str, str, str | None, Dict[str, float], Dict[str, float]]:
    """
    Reproduit la logique de pipeline_auto en mode 'auto' :
    - analyse LLM de la demande (intent + target)
    - calcul surfaces / périmètres à partir des détections
    - génération d'une réponse finale textuelle.
    """
    intent_data = _llm_arch.analyze_request(prompt)
    intent = (intent_data or {}).get("intent", "analyse_globale")
    target = (intent_data or {}).get("target")

    surfaces: Dict[str, float] = {}
    perimeters: Dict[str, float] = {}
    counts: Dict[str, int] = {}

    for idx, detection in enumerate(detections):
        bbox_raw = detection.get("bounding_box") or detection
        bbox = adapt_bbox(bbox_raw)

        s = float(calculate_surface(bbox, img_width, img_height, scale_ratio))
        p = float(calculate_perimeter(bbox, img_width, img_height, scale_ratio))

        tag_name = detection.get("tag_name") or f"obj{idx + 1}"

        surfaces[tag_name] = surfaces.get(tag_name, 0.0) + s
        perimeters[tag_name] = perimeters.get(tag_name, 0.0) + p
        counts[tag_name] = counts.get(tag_name, 0) + 1

    surfaces["total"] = sum(surfaces.values())
    perimeters["total"] = sum(perimeters.values())

    data = {
        "surfaces": surfaces,
        "perimeters": perimeters,
        "counts": counts,
    }
    response_text = _response_generator.generate_response(
        intent=intent,
        target=target,
        data=data,
    )

    return response_text, intent, target, surfaces, perimeters

