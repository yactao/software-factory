from fastapi import APIRouter, Depends, HTTPException
from ..core.security import _auth_dependency, _require_scope
from ..core.config import USE_GROUNDING, GEMINI_MODEL_WEB
from ..models.schemas import WebSearchIn, WebSearchOut
from ..services.history_helpers import _save_chat_event
from ..services.gemini_web import _build_web_tools, _extract_web_citations, get_web_client
from google.genai import types as gtypes

router = APIRouter()

@router.post("/api/search", response_model=WebSearchOut)
def search_web(body: WebSearchIn, claims: dict = Depends(_auth_dependency)):
    _require_scope(claims)
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(400, "Le champ 'question' est requis et ne doit pas être vide.")

    # Log USER
    conv_id = _save_chat_event(
        claims,
        conversation_id=body.conversation_id,
        role="user",
        route="search",
        message=question if not body.context else f"{question}\n\n[CTX]\n{body.context}",
        meta={"type": "search_user", "force_grounding": body.force_grounding, "legacy_15": body.legacy_15}
    )

    use_grounding = body.force_grounding if body.force_grounding is not None else USE_GROUNDING
    config = None
    if use_grounding:
        tools = _build_web_tools(legacy_15=bool(body.legacy_15))
        config = gtypes.GenerateContentConfig(tools=tools)

    system = (
        "Tu es un assistant qui répond avec des faits exacts. "
        "Si le grounding est activé, cite uniquement les sources renvoyées. "
        "Structure la réponse en paragraphes courts."
    )
    contents = [gtypes.Content(role="user", parts=[gtypes.Part(text=f"{system}\n\nQuestion: {question}\nContexte: {body.context or 'N/A'}")])]

    client = get_web_client()
    try:
        resp = client.models.generate_content(model=GEMINI_MODEL_WEB, contents=contents, config=config)
    except Exception as e:
        err_txt = f"Erreur Gemini: {e}"
        payload_err = WebSearchOut(answer=err_txt, citations=[], model=GEMINI_MODEL_WEB, grounded=False, conversation_id=conv_id)
        _save_chat_event(claims, conv_id, role="assistant", route="search", message=err_txt, meta=payload_err.dict())
        raise HTTPException(502, err_txt)

    text = getattr(resp, "text", "") or ""
    citations = _extract_web_citations(resp)
    grounded = len(citations) > 0
    if use_grounding and not grounded:
        text = f"{text}\n\n[Note] Aucune source explicite renvoyée par le grounding."

    payload = WebSearchOut(answer=text.strip(), citations=citations, model=GEMINI_MODEL_WEB, grounded=grounded, conversation_id=conv_id)
    _save_chat_event(claims, conv_id, role="assistant", route="search", message=payload.answer, meta=payload.dict())
    return payload
