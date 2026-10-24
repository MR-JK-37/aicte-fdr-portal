from __future__ import annotations

from fastapi import FastAPI
from sqlalchemy import text

from app.auth.router import router as auth_router
from app.config import settings
from app.core.prod_guard import enforce_production_guard
from app.correlation import CorrelationIdMiddleware
from app.db import SessionLocal
from app.discrepancies.router import router as discrepancies_router
from app.documents.router import router as documents_router
from app.idempotency.middleware import IdempotencyMiddleware
from app.institutions.router import router as institutions_router
from app.instruments.router import router as instruments_router
from app.notifications.router import router as notifications_router
from app.observations.router import router as observations_router
from app.policy.router import router as policy_router
from app.problem_json import register_exception_handlers
from app.queues.router import router as queues_router
from app.realtime.router import router as realtime_router
from app.receipts.router import router as receipts_router
from app.registry.router import router as registry_router
from app.release.router import router as release_router
from app.renewals.router import router as renewals_router
from app.statements.router import router as statements_router
from app.verification.router import router as verification_router

# Refuses to continue importing/starting this module at all if the
# environment is production and any simulation/demo/mock/fake flag is
# set (CLAUDE.md non-negotiable #10). No-op in non-production envs.
enforce_production_guard()

app = FastAPI(
    title="AICTE FDR Portal API",
    version="1.0.0",
    docs_url="/docs",
    openapi_url="/v1/openapi.json",
)

# Exception handlers map exceptions to RFC 9457 application/problem+json
register_exception_handlers(app)

# Middlewares stack in reverse order:
# IdempotencyMiddleware is added first, CorrelationIdMiddleware last (so it runs outermost).
app.add_middleware(IdempotencyMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# Wire versioned routers
app.include_router(auth_router, prefix="/v1")
app.include_router(registry_router)
app.include_router(receipts_router)
app.include_router(institutions_router)
app.include_router(instruments_router)
app.include_router(observations_router)
app.include_router(queues_router)
app.include_router(documents_router)
app.include_router(verification_router)
app.include_router(statements_router)
app.include_router(discrepancies_router)
app.include_router(policy_router)
app.include_router(renewals_router)
app.include_router(release_router)
app.include_router(notifications_router)
app.include_router(realtime_router)


@app.get("/health", tags=["system"])
@app.get("/healthz", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@app.get("/readyz", tags=["system"])
def readiness() -> dict[str, str]:
    """Readiness probe checking DB connectivity."""
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:  # noqa: BLE001
        return {"status": "degraded", "database": str(e)}
