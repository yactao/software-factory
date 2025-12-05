# app/models/schemas.py
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

# === COLLE ICI SANS MODIFIER: toutes tes classes Pydantic ===
class RAGRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = 8
    conversation_id: Optional[str] = None


class FinanceRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None
class FinanceQuery(BaseModel):
    query: str = ""
    ville: Optional[str] = None
    client: Optional[str] = None
    top: Optional[int] = 20
    conversation_id: Optional[str] = None

class WebCitation(BaseModel):
    title: Optional[str] = None
    url: Optional[str] = None

class WebSearchIn(BaseModel):
    question: str
    context: Optional[str] = None
    force_grounding: Optional[bool] = None
    legacy_15: Optional[bool] = False
    conversation_id: Optional[str] = None

class WebSearchOut(BaseModel):
    answer: str
    citations: List[WebCitation]
    model: str
    grounded: bool
    conversation_id: Optional[str] = None

class TradingRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, Any]] = None
    top_k: Optional[int] = 8
    conversation_id: Optional[str] = None

class RenameBody(BaseModel):
    conversation_id: str
    title: str

class ClearAllResult(BaseModel):
    route: str
    conversations_affected: int
    entities_deleted: int
    purge_entire_conversation: bool
    
class Detection(BaseModel):
    tag_name: str
    probability: float
    bounding_box: Dict[str, float]

class AnalyzeResponse(BaseModel):
    intent: str
    target: Optional[str]
    surfaces: Dict[str, float]
    perimeters: Dict[str, float]
    response_text: str
    detections: List[Detection]
    annotated_image_b64: Optional[str] = None
    meta: Dict[str, Any] = {}
    conversation_id: Optional[str] = None  
    
class VetFinanceRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None