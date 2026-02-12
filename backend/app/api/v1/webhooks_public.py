"""Public webhook receiver (no JWT auth)."""
from fastapi import APIRouter, Request, Response

from app.core.database import get_db
from app.services import webhook_service

router = APIRouter(prefix="/webhooks", tags=["webhooks-public"])


@router.post("/{url_path}")
async def receive_webhook(url_path: str, request: Request):
    """Receive incoming webhook. Always returns 200 to avoid retries."""
    payload = await request.body()
    signature = request.headers.get("X-Webhook-Signature", "")

    db = next(get_db())
    try:
        result = webhook_service.process_incoming(db, url_path, payload, signature)
        return Response(status_code=result.get("status", 200), content=result.get("message", "OK"))
    finally:
        db.close()
