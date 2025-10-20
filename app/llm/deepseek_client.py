from __future__ import annotations

import json
import os
from typing import Dict, Any, Optional

import requests
from fastapi import HTTPException


class DeepSeekClient:
    """
    Client DeepSeek via REST (https://api.deepseek.com).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "deepseek-chat"):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise HTTPException(500, "DEEPSEEK_API_KEY manquant.")
        self.model = model
        self.url = "https://api.deepseek.com/chat/completions"
        self.timeout = (10, 30)

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        h = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            r = requests.post(self.url, headers=h, json=payload, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            raise HTTPException(504, "DeepSeek: délai dépassé.")
        except requests.exceptions.ConnectionError:
            raise HTTPException(502, "DeepSeek: connexion impossible.")
        except requests.exceptions.HTTPError as e:
            body = ""
            try:
                body = e.response.text
            except Exception:
                pass
            raise HTTPException(502, f"DeepSeek erreur HTTP {e.response.status_code if e.response else 'unknown'}: {body[:400]}")
        except requests.exceptions.RequestException as e:
            raise HTTPException(502, f"DeepSeek erreur réseau: {e}")

    def generate_json(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys or ""},
                {"role": "user", "content": prompt or ""},
            ],
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "response_format": {"type": "json_object"},
        }
        j = self._post(data)
        content = (j.get("choices", [{}])[0].get("message", {}) or {}).get("content", "")
        try:
            return json.loads(content) if content else {}
        except Exception:
            return {"answer": content or "", "uses_context": False}

    def generate_text(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> str:
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys or ""},
                {"role": "user", "content": prompt or ""},
            ],
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        j = self._post(data)
        return (j.get("choices", [{}])[0].get("message", {}) or {}).get("content", "").strip()
