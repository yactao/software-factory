from __future__ import annotations

import json
from typing import Dict, Any

from fastapi import HTTPException

try:
    import google.generativeai as genai
except Exception as e:  # pragma: no cover
    genai = None


class GeminiClient:
    """
    Client Gemini simple (1.5-Flash/Pro).
    """

    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        if genai is None:
            raise HTTPException(500, "google-generativeai non installé.")
        if not api_key:
            raise HTTPException(500, "GEMINI_API_KEY manquant.")
        self.api_key = api_key
        self.model_name = model
        genai.configure(api_key=api_key)

    def _model(self, sys: str, max_tokens: int, temperature: float, mime: str):
        return genai.GenerativeModel(
            self.model_name,
            system_instruction=sys,
            generation_config={
                "temperature": float(temperature),
                "max_output_tokens": int(max_tokens),
                "response_mime_type": mime,
            },
        )

    def generate_json(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        m = self._model(sys, max_tokens, temperature, "application/json")
        r = m.generate_content([{"role": "user", "parts": [{"text": prompt}]}])
        txt = (r.text or "").strip()
        try:
            return json.loads(txt) if txt else {}
        except Exception:
            return {"answer": txt or "", "uses_context": False}

    def generate_text(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> str:
        m = self._model(sys, max_tokens, temperature, "text/plain")
        r = m.generate_content([{"role": "user", "parts": [{"text": prompt}]}])
        return (r.text or "").strip()
