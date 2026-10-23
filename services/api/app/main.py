from fastapi import FastAPI

from app.config import settings
from app.voice.router import router as voice_router

app = FastAPI(title="AICTE FDR Portal API")

app.include_router(voice_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}
