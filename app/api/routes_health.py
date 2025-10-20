from fastapi import APIRouter
import time

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "time": time.time()}
