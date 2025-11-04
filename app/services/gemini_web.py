from google import genai as genai_web
from google.genai import types as gtypes
from typing import List
from ..models.schemas import WebCitation
from ..core.config import GEMINI_API_KEY, GEMINI_MODEL_WEB

_gemini_web_client = genai_web.Client(api_key=GEMINI_API_KEY)
 

def _build_web_tools(legacy_15: bool):
    if legacy_15:
        retrieval_tool = gtypes.Tool(
            google_search_retrieval=gtypes.GoogleSearchRetrieval(
                dynamic_retrieval_config=gtypes.DynamicRetrievalConfig(
                    mode=gtypes.DynamicRetrievalConfigMode.MODE_DYNAMIC,
                    dynamic_threshold=0.7,
                )
            )
        )
        return [retrieval_tool]
    # Outil Google Search natif des modèles 2.0+
    return [gtypes.Tool(google_search=gtypes.GoogleSearch())]


def _extract_web_citations(resp) -> List[WebCitation]:
    cites: List[WebCitation] = []
    try:
        cand = resp.candidates[0]
        gm = getattr(cand, "grounding_metadata", None)
        if not gm or not gm.grounding_chunks:
            return cites
        seen = set()
        for ch in gm.grounding_chunks:
            web = getattr(ch, "web", None)
            if not web:
                continue
            uri = getattr(web, "uri", None)
            title = getattr(web, "title", None)
            if uri and uri not in seen:
                cites.append(WebCitation(title=title, url=uri))
                seen.add(uri)
    except Exception:
        pass
    return cites

def get_web_client():
    return _gemini_web_client
