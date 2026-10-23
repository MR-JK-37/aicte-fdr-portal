from fastapi import FastAPI

from app.config import settings

app = FastAPI(title="AICTE FDR Portal API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}
