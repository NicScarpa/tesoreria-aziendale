"""Corrispettivi import service (Agenzia Entrate)."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from dateutil import parser as date_parser
from sqlalchemy.orm import Session

from app.models.receipt_import import ReceiptImport


def _safe_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _make_idempotency_key(
    business_date: date,
    external_id: str | None,
    device_id: str | None,
) -> str:
    if external_id:
        return f"external:{external_id}"
    if device_id:
        return f"device:{device_id}:{business_date.isoformat()}"
    # Last resort: stable-ish hash on date only (may collide, but avoids null keys)
    h = hashlib.sha256(business_date.isoformat().encode()).hexdigest()[:16]
    return f"date:{business_date.isoformat()}:{h}"


def parse_receipt_raw(raw_bytes: bytes) -> dict[str, Any]:
    """
    Best-effort parser for raw technical attachment.

    Expected (based on reverse-engineering notes) a JSON with keys like:
    - idInvio
    - matricolaDispositivo
    - timeRilevazione
    - datiContabiliRT_MC (contains totals)
    """
    text = raw_bytes.lstrip()[:1]
    if text not in (b"{", b"["):
        return {}

    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except Exception:
        return {}

    if isinstance(payload, list):
        # Not sure of list shape; keep as-is.
        return {"items": payload}
    if isinstance(payload, dict):
        return payload
    return {}


def extract_receipt_fields(parsed: dict[str, Any]) -> dict[str, Any]:
    external_id = parsed.get("idInvio") or parsed.get("idinvio") or parsed.get("externalId")
    device_id = (
        parsed.get("matricolaDispositivo")
        or parsed.get("matricola")
        or parsed.get("deviceId")
        or parsed.get("matricola_dispositivo")
    )
    time_rilevazione_raw = parsed.get("timeRilevazione") or parsed.get("time_rilevazione") or parsed.get("timestamp")
    time_rilevazione: datetime | None = None
    if time_rilevazione_raw:
        try:
            time_rilevazione = date_parser.parse(str(time_rilevazione_raw))
        except Exception:
            time_rilevazione = None

    dati_contabili = parsed.get("datiContabiliRT_MC") or parsed.get("dati_contabili") or {}
    gross_total = None
    net_total = None
    vat_total = None

    if isinstance(dati_contabili, dict):
        gross_total = _safe_decimal(
            dati_contabili.get("totale") or dati_contabili.get("totaleGiornaliero") or dati_contabili.get("importoTotale")
        )
        net_total = _safe_decimal(dati_contabili.get("imponibile") or dati_contabili.get("netto"))
        vat_total = _safe_decimal(dati_contabili.get("iva") or dati_contabili.get("imposta"))

    return {
        "external_id": str(external_id) if external_id is not None else None,
        "device_id": str(device_id) if device_id is not None else None,
        "time_rilevazione": time_rilevazione,
        "gross_total": gross_total,
        "net_total": net_total,
        "vat_total": vat_total,
    }


def upsert_receipt(
    db: Session,
    company_id: uuid.UUID,
    business_date: date,
    external_id: str | None = None,
    device_id: str | None = None,
    time_rilevazione: datetime | None = None,
    gross_total: Decimal | None = None,
    net_total: Decimal | None = None,
    vat_total: Decimal | None = None,
    currency: str = "EUR",
    source: str = "agenzia_entrate",
    status: str = "imported",
    raw_attachment_path: str | None = None,
    metadata_extra: dict | None = None,
    errore_dettaglio: str | None = None,
) -> tuple[ReceiptImport, bool]:
    """Upsert a receipt. Returns (receipt, created)."""
    idempotency_key = _make_idempotency_key(business_date, external_id, device_id)

    existing = db.query(ReceiptImport).filter(
        ReceiptImport.company_id == company_id,
        ReceiptImport.idempotency_key == idempotency_key,
    ).first()

    if existing:
        # Update mutable fields
        existing.business_date = business_date
        existing.external_id = external_id
        existing.device_id = device_id
        existing.time_rilevazione = time_rilevazione
        existing.gross_total = gross_total
        existing.net_total = net_total
        existing.vat_total = vat_total
        existing.currency = currency
        existing.source = source
        existing.status = status
        if raw_attachment_path:
            existing.raw_attachment_path = raw_attachment_path
        if metadata_extra:
            existing.metadata_extra = {**(existing.metadata_extra or {}), **metadata_extra}
        if errore_dettaglio:
            existing.errore_dettaglio = errore_dettaglio
        db.flush()
        return existing, False

    item = ReceiptImport(
        company_id=company_id,
        business_date=business_date,
        idempotency_key=idempotency_key,
        external_id=external_id,
        device_id=device_id,
        time_rilevazione=time_rilevazione,
        gross_total=gross_total,
        net_total=net_total,
        vat_total=vat_total,
        currency=currency,
        source=source,
        status=status,
        raw_attachment_path=raw_attachment_path,
        metadata_extra=metadata_extra or {},
        errore_dettaglio=errore_dettaglio,
    )
    db.add(item)
    db.flush()
    return item, True


def list_receipts(
    db: Session,
    company_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ReceiptImport], int]:
    q = db.query(ReceiptImport).filter(ReceiptImport.company_id == company_id)
    if date_from:
        q = q.filter(ReceiptImport.business_date >= date_from)
    if date_to:
        q = q.filter(ReceiptImport.business_date <= date_to)

    q = q.order_by(ReceiptImport.business_date.desc(), ReceiptImport.created_at.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total


def get_receipt(db: Session, receipt_id: uuid.UUID, company_id: uuid.UUID) -> ReceiptImport | None:
    return db.query(ReceiptImport).filter(
        ReceiptImport.id == receipt_id,
        ReceiptImport.company_id == company_id,
    ).first()

