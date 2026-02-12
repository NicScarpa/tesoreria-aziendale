"""Webhook management service."""
import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import WebhookType
from app.models.webhook_endpoint import WebhookEndpoint

logger = logging.getLogger(__name__)


def generate_secret() -> str:
    """Generate a random HMAC-SHA256 secret."""
    return secrets.token_hex(32)


def validate_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
    """Validate HMAC-SHA256 signature."""
    expected = hmac.new(
        secret.encode(), payload_bytes, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def list_webhooks(db: Session, company_id: uuid.UUID) -> list[WebhookEndpoint]:
    return db.query(WebhookEndpoint).filter(
        WebhookEndpoint.company_id == company_id,
    ).order_by(WebhookEndpoint.created_at.desc()).all()


def create_webhook(db: Session, company_id: uuid.UUID, tipo: WebhookType) -> WebhookEndpoint:
    wh = WebhookEndpoint(
        company_id=company_id,
        tipo=tipo,
        url_path=str(uuid.uuid4()),
        secret=generate_secret(),
    )
    db.add(wh)
    db.flush()
    db.commit()
    db.refresh(wh)
    return wh


def delete_webhook(db: Session, webhook_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    wh = db.query(WebhookEndpoint).filter(
        WebhookEndpoint.id == webhook_id,
        WebhookEndpoint.company_id == company_id,
    ).first()
    if not wh:
        return False
    db.delete(wh)
    db.flush()
    db.commit()
    return True


def get_by_url_path(db: Session, url_path: str) -> WebhookEndpoint | None:
    return db.query(WebhookEndpoint).filter(
        WebhookEndpoint.url_path == url_path,
        WebhookEndpoint.is_active == True,
    ).first()


def process_incoming(db: Session, url_path: str, payload: bytes, signature: str) -> dict:
    """Process incoming webhook request."""
    wh = get_by_url_path(db, url_path)
    if not wh:
        return {"error": "Webhook non trovato", "status": 404}

    if not validate_signature(payload, signature, wh.secret):
        wh.failure_count += 1
        db.flush()
        db.commit()
        return {"error": "Firma non valida", "status": 401}

    wh.trigger_count += 1
    wh.last_triggered_at = datetime.now(timezone.utc)
    db.flush()
    db.commit()

    # Dispatch based on type
    logger.info(f"Webhook received: type={wh.tipo.value}, path={url_path}")

    return {"status": 200, "message": "OK"}
