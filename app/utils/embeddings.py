from typing import Optional, List
import requests
from fastapi import HTTPException
from ..core.config import AOAI_ENDPOINT, AOAI_API_KEY, AOAI_EMBED_DEPLOYMENT, AOAI_API_VERSION

def _embed_text_aoai(text: str) -> Optional[list[float]]:
    """
    Calcule un embedding via Azure OpenAI (déploiement d'embeddings).
    Utilisé quand l'API Search ne supporte pas 'vectorizer' dans vectorQueries.
    """
    if not (AOAI_ENDPOINT and AOAI_API_KEY and AOAI_EMBED_DEPLOYMENT):
        return None
    url = f"{AOAI_ENDPOINT}/openai/deployments/{AOAI_EMBED_DEPLOYMENT}/embeddings?api-version={AOAI_API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        "api-key": AOAI_API_KEY
    }
    body = {"input": text}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=15)
        if r.status_code >= 300:
            # log soft, on retombera sur BM25/semantic
            print(f"[embed] AOAI embeddings error {r.status_code}: {r.text[:400]}")
            return None
        data = r.json()
        vec = data.get("data", [{}])[0].get("embedding")
        if isinstance(vec, list) and vec:
            return vec
    except Exception as e:
        print(f"[embed] AOAI embeddings exception: {e}")
    return None
