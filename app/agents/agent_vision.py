from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.storage.tables import list_conversation_events
from app.utils.text import clean_markdown


class VisionAgent:
    route_name = "vision"

    def _chat_history_block(self, claims, conversation_id, max_turns: int = 6, max_chars: int = 1200) -> str:
        if not conversation_id:
            return ""
        events = list_conversation_events(claims, conversation_id, select=["RowKey", "role", "route", "message"])
        msgs = [(e["role"], e["message"]) for e in events if e.get("route") == self.route_name]
        lines = []
        for role, msg in msgs[-12:]:
            tag = "U" if role == "user" else "A"
            lines.append(f"{tag}: {clean_markdown(msg or '')}")
        text = "\n".join(lines).strip()
        if len(text) > max_chars:
            text = text[-max_chars:]
        return text

    def handle(self, req):
        """
        Squelette. Ici, tu pourras:
        - recevoir une image (URL/SAS) via req.filters["image_url"]
        - faire l’OCR (Azure Computer Vision / Tesseract)
        - renvoyer la synthèse.
        """
        _ = self._chat_history_block(req.claims, req.conversation_id)
        return {
            "answer": "Vision/OCR n’est pas encore implémenté dans cet agent.",
            "uses_context": False,
            "used_docs": [],
            "citations": [],
            "conversation_id": req.conversation_id,
        }
