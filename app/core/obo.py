# app/core/obo.py
from app.core.config import TENANT_ID, BACK_CLIENT_ID, BACK_SECRET_CLIENT
from app.core.http_client import get_http_client
from app.core.obo_cache import obo_cache

TOKEN_URL = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

def _cache_key(user_id: str) -> str:
    return f"obo:{user_id}"

async def get_graph_token_on_behalf_of(user_token: str, user_id: str) -> str:
    # 1) cache
    cached = obo_cache.get(_cache_key(user_id))
    if cached:
        return cached

    # 2) OBO
    data = {
        "client_id": BACK_CLIENT_ID,
        "client_secret": BACK_SECRET_CLIENT,
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": user_token,
        "requested_token_use": "on_behalf_of",
        "scope": "https://graph.microsoft.com/.default",
    }

    client = get_http_client()
    resp = await client.post(TOKEN_URL, data=data)

    if resp.status_code != 200:
        raise RuntimeError(f"OBO failed {resp.status_code}: {resp.text}")

    payload = resp.json()
    token = payload["access_token"]
    expires_in = int(payload.get("expires_in", 3600))

    obo_cache.set(_cache_key(user_id), token, expires_in)
    return token
