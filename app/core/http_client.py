# app/core/http_client.py
import httpx

_graph_client: httpx.AsyncClient | None = None

def get_http_client() -> httpx.AsyncClient:
    global _graph_client
    if _graph_client is None:
        _graph_client = httpx.AsyncClient(timeout=httpx.Timeout(10.0))
    return _graph_client

async def close_http_client() -> None:
    global _graph_client
    if _graph_client is not None:
        await _graph_client.aclose()
        _graph_client = None
