# app/routers/dev.py
import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException

from app.core.security import _auth_dependency, _require_scope
from app.models.schemas import DevRequest
from app.services.history_helpers import _save_chat_event
from app.services.agents_dev import generate_and_test_code

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/api/dev")
def aina_software_factory(req: DevRequest, claims: Dict[str, Any] = Depends(_auth_dependency)):
    _require_scope(claims)

    question = (req.question or "").strip()
    if not question:
        raise HTTPException(400, "La question (le besoin de code) est vide.")

    conv_id = req.conversation_id or str(uuid.uuid4())

    # 1. Save user event
    _save_chat_event(
        claims,
        conv_id,
        role="user",
        route="dev",
        message=question,
        meta={"language": req.language}
    )

    # 2. Invoke Foundry LLM & Azure Sandbox 
    try:
        code_str, execution_output, sas_url = generate_and_test_code(question, req.language)
    except Exception as e:
        logger.error(f"Dev agent failed: {e}")
        raise HTTPException(502, f"Erreur dans le broker de l'usine logicielle: {e}")

    # 3. Format response
    has_error = "Erreur" in execution_output or "Error" in execution_output
    status_text = "tests en échec" if has_error else "tests au vert"

    final_answer = (
        f"J'ai généré ton code en {req.language}. L'exécution dans la Sandbox Azure a donné des {status_text}.\n\n"
        f"**Sortie de la compilation :**\n{execution_output}\n\n"
        f"Ton archive prête au téléchargement : {sas_url}"
    )

    payload = {
        "answer": final_answer,
        "repo_file_sas": sas_url,
        "conversation_id": conv_id,
        "model": "Aïna-Coder-Foundry"
    }

    # 4. Save response event
    _save_chat_event(
        claims,
        conv_id,
        role="assistant",
        route="dev",
        message=final_answer,
        meta=payload
    )

    return payload
