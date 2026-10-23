from fastapi import FastAPI

from app.config import settings
from app.core.prod_guard import enforce_production_guard

# Refuses to continue importing/starting this module at all if the
# environment is production and any simulation/demo/mock/fake flag is
# set (CLAUDE.md non-negotiable #10). No-op in non-production envs.
enforce_production_guard()

app = FastAPI(title="AICTE FDR Portal API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}
