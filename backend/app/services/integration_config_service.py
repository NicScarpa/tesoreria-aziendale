"""Integration configuration service."""
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.encryption import encrypt_value
from app.models.enums import (
    IntegrationConnectionStatus, IntegrationType,
    OpenBankingConnectionStatus, InvoiceStatus,
)
from app.models.integration_config import IntegrationConfig
from app.models.open_banking_connection import OpenBankingConnection
from app.models.invoice_import import InvoiceImport

logger = logging.getLogger(__name__)

INTEGRATION_META = {
    IntegrationType.OPEN_BANKING: {
        "label": "Open Banking (PSD2)",
        "description": "Connessione diretta ai conti bancari per sincronizzazione automatica movimenti e saldi.",
    },
    IntegrationType.FATTURE_ELETTRONICHE: {
        "label": "Fatture Elettroniche",
        "description": "Import e elaborazione fatture elettroniche FatturaPA (XML/P7M) con creazione automatica scadenze.",
    },
    IntegrationType.CBI_CORPORATE_BANKING: {
        "label": "CBI / SEPA",
        "description": "Import ed export file CBI e SEPA (camt.053, pain.001/002, rendicontazione).",
    },
}


def get_overview(db: Session, company_id: uuid.UUID) -> list[dict]:
    configs = db.query(IntegrationConfig).filter(
        IntegrationConfig.company_id == company_id
    ).all()

    config_map = {c.integration_type: c for c in configs}
    result = []

    for it in IntegrationType:
        meta = INTEGRATION_META.get(it, {})
        cfg = config_map.get(it)
        result.append({
            "integration_type": it,
            "status": cfg.status if cfg else IntegrationConnectionStatus.NON_CONFIGURATA,
            "is_enabled": cfg.is_enabled if cfg else False,
            "label": meta.get("label", it.value),
            "description": meta.get("description", ""),
        })

    return result


def get_config(db: Session, company_id: uuid.UUID, tipo: IntegrationType) -> IntegrationConfig:
    cfg = db.query(IntegrationConfig).filter(
        IntegrationConfig.company_id == company_id,
        IntegrationConfig.integration_type == tipo,
    ).first()

    if not cfg:
        cfg = IntegrationConfig(
            company_id=company_id,
            integration_type=tipo,
            status=IntegrationConnectionStatus.NON_CONFIGURATA,
            is_enabled=False,
        )
        db.add(cfg)
        db.flush()

    return cfg


def update_config(
    db: Session, company_id: uuid.UUID, tipo: IntegrationType, data: dict
) -> IntegrationConfig:
    cfg = get_config(db, company_id, tipo)

    if "credentials" in data and data["credentials"]:
        import json
        cfg.encrypted_credentials = encrypt_value(json.dumps(data["credentials"]))
        cfg.status = IntegrationConnectionStatus.CONFIGURATA

    if "config" in data and data["config"]:
        cfg.config = {**(cfg.config or {}), **data["config"]}

    db.flush()
    db.commit()
    db.refresh(cfg)
    return cfg


def test_connection(db: Session, company_id: uuid.UUID, tipo: IntegrationType) -> dict:
    cfg = get_config(db, company_id, tipo)
    cfg.last_test_at = datetime.now(timezone.utc)

    # Mock test - always succeeds for now
    cfg.status = IntegrationConnectionStatus.CONNESSA
    db.flush()
    db.commit()

    return {"success": True, "message": "Connessione riuscita"}


def toggle(db: Session, company_id: uuid.UUID, tipo: IntegrationType, enabled: bool) -> IntegrationConfig:
    cfg = get_config(db, company_id, tipo)
    cfg.is_enabled = enabled
    db.flush()
    db.commit()
    db.refresh(cfg)
    return cfg


def get_alerts_count(db: Session, company_id: uuid.UUID) -> dict:
    """Count alerts for sidebar badge."""
    # Consents expiring within 14 days
    from datetime import timedelta
    threshold = datetime.now(timezone.utc) + timedelta(days=14)
    consents_expiring = db.query(OpenBankingConnection).filter(
        OpenBankingConnection.company_id == company_id,
        OpenBankingConnection.stato == OpenBankingConnectionStatus.ATTIVA,
        OpenBankingConnection.consenso_scadenza <= threshold,
    ).count()

    # Invoices pending elaboration
    invoices_pending = db.query(InvoiceImport).filter(
        InvoiceImport.company_id == company_id,
        InvoiceImport.stato == InvoiceStatus.IMPORTATA,
    ).count()

    # Sync errors
    sync_errors = db.query(OpenBankingConnection).filter(
        OpenBankingConnection.company_id == company_id,
        OpenBankingConnection.errore_conteggio > 0,
    ).count()

    total = consents_expiring + invoices_pending + sync_errors
    return {
        "consents_expiring": consents_expiring,
        "invoices_pending": invoices_pending,
        "sync_errors": sync_errors,
        "total": total,
    }
