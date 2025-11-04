import time
from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "time": time.time()}
