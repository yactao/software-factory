from __future__ import annotations
from dotenv import load_dotenv; load_dotenv()  # <-- charge .env en local

import uvicorn
from app.container import build_app

# Application ASGI attendue par App Service / gunicorn
app = build_app()

if __name__ == "__main__":
    # Exécution locale: uvicorn app.main:app --reload
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        factory=False,
    )
