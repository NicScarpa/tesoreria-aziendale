from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import router as v1_router
from app.api.v1.webhooks_public import router as webhooks_public_router
from app.core.config import settings
from app.services.ade_auto_sync_scheduler import (
    start_ade_auto_sync_scheduler,
    stop_ade_auto_sync_scheduler,
)

app = FastAPI(title="Gestionale Tesoreria API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api/v1")
app.include_router(webhooks_public_router)


@app.on_event("startup")
def _startup() -> None:
    # Runs only for enabled integrations (IntegrationConfig.is_enabled).
    start_ade_auto_sync_scheduler()


@app.on_event("shutdown")
def _shutdown() -> None:
    stop_ade_auto_sync_scheduler()


@app.get("/health")
def health():
    return {"status": "ok"}
