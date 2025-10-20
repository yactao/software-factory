from __future__ import annotations

import json
import os
import re
from typing import Dict, Any, Optional, Tuple

import requests
from fastapi import HTTPException

# Managed Identity / AAD (facultatif)
try:
    from azure.identity import DefaultAzureCredential
except Exception:  # pragma: no cover
    DefaultAzureCredential = None


class AzureOpenAIClient:
    """
    Client Azure OpenAI (Chat Completions) via REST.

    - Supporte api-key OU Managed Identity (AAD) si AZURE_OPENAI_API_KEY absent.
    - Expose generate_json() (avec response_format JSON + fallback compatible) et generate_text().
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_connect: int = 10,
        timeout_read: int = 30,
    ):
        self.endpoint = endpoint or os.getenv("AZURE_OPENAI_ENDPOINT", "").rstrip("/")
        self.deployment = deployment or os.getenv("AZURE_OPENAI_DEPLOYMENT")
        self.api_version = api_version or os.getenv("AZURE_OPENAI_API_VERSION", "2024-06-01")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_API_KEY")
        self.timeout = (timeout_connect, timeout_read)

        if not self.endpoint:
            raise HTTPException(500, "AZURE_OPENAI_ENDPOINT manquant.")
        if not self.deployment:
            raise HTTPException(500, "AZURE_OPENAI_DEPLOYMENT manquant.")

        self.url = f"{self.endpoint}/openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"

    # ---- Auth helpers ----

    def _get_bearer_from_msi(self) -> Optional[str]:
        """
        Récupère un bearer AAD via Managed Identity si possible.
        Scope: https://cognitiveservices.azure.com/.default
        """
        if DefaultAzureCredential is None:
            return None
        try:
            cred = DefaultAzureCredential()
            token = cred.get_token("https://cognitiveservices.azure.com/.default")
            return token.token
        except Exception:
            return None

    def _headers(self, prefer_json: bool = True) -> Dict[str, str]:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["api-key"] = self.api_key
            return h
        bearer = self._get_bearer_from_msi()
        if bearer:
            h["Authorization"] = f"Bearer {bearer}"
            return h
        # Si aucune auth fournie
        raise HTTPException(500, "Fournis AZURE_OPENAI_API_KEY ou active Managed Identity.")

    # ---- Core call ----

    def _call(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            r = requests.post(self.url, headers=self._headers(), json=payload, timeout=self.timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.Timeout:
            raise HTTPException(504, "Azure OpenAI: délai dépassé.")
        except requests.exceptions.ConnectionError:
            raise HTTPException(502, "Azure OpenAI: connexion impossible.")
        except requests.exceptions.HTTPError as e:
            body = ""
            try:
                body = e.response.text
            except Exception:
                pass
            # Fallback: certains déploiements refusent response_format JSON → on ré-essaie sans
            if e.response is not None and e.response.status_code == 400 and "response_format" in (body or "").lower():
                payload2 = dict(payload)
                payload2.pop("response_format", None)
                r2 = requests.post(self.url, headers=self._headers(), json=payload2, timeout=self.timeout)
                try:
                    r2.raise_for_status()
                    return r2.json()
                except Exception:
                    pass
            status = e.response.status_code if e.response is not None else "unknown"
            snippet = (body or "")[:500]
            raise HTTPException(502, f"Azure OpenAI erreur HTTP {status}: {snippet}")
        except requests.exceptions.RequestException as e:
            raise HTTPException(502, f"Azure OpenAI erreur réseau: {e}")

    # ---- Public API ----

    def _build_messages(self, sys: str, user: str):
        return [
            {"role": "system", "content": sys or ""},
            {"role": "user", "content": user or ""},
        ]

    def _extract_first_text(self, j: Dict[str, Any]) -> str:
        try:
            return (j["choices"][0]["message"]["content"] or "").strip()
        except Exception:
            return ""

    def generate_json(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> Dict[str, Any]:
        """
        Appel JSON “robuste”:
        - tente response_format={"type": "json_object"}
        - fallback si non supporté
        - si le modèle renvoie un texte non JSON, on encapsule dans {"answer": "...", "uses_context": <heuristique>}
        """
        payload = {
            "messages": self._build_messages(sys, prompt),
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
            "response_format": {"type": "json_object"},
        }
        data = self._call(payload)
        content = self._extract_first_text(data)
        try:
            return json.loads(content) if content else {}
        except Exception:
            uses = bool(re.search(r"\[\d+\]", content or ""))  # heuristique si citations [n]
            return {"answer": content or "", "uses_context": uses}

    def generate_text(self, prompt: str, sys: str, max_tokens: int, temperature: float) -> str:
        payload = {
            "messages": self._build_messages(sys, prompt),
            "temperature": float(temperature),
            "max_tokens": int(max_tokens),
        }
        data = self._call(payload)
        return self._extract_first_text(data)
