"""Payment template service.

CRUD and apply operations for payment templates.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.enums import PaymentOrderStatus, PaymentOrderType, PaymentPriority
from app.models.payment_order import PaymentOrder
from app.models.payment_template import PaymentTemplate
from app.services.payment_order_service import _generate_riferimento


def list_templates(
    db: Session,
    company_id: uuid.UUID,
    tipo: str | None = None,
) -> list[PaymentTemplate]:
    q = db.query(PaymentTemplate).filter(PaymentTemplate.company_id == company_id)
    if tipo:
        q = q.filter(PaymentTemplate.tipo == tipo)
    return q.order_by(PaymentTemplate.volte_utilizzato.desc()).all()


def get_template(
    db: Session, template_id: uuid.UUID, company_id: uuid.UUID,
) -> PaymentTemplate | None:
    return (
        db.query(PaymentTemplate)
        .filter(PaymentTemplate.id == template_id, PaymentTemplate.company_id == company_id)
        .first()
    )


def create_template(
    db: Session, company_id: uuid.UUID, data: dict,
) -> PaymentTemplate:
    template = PaymentTemplate(company_id=company_id, **data)
    db.add(template)
    db.commit()
    db.refresh(template)
    return template


def delete_template(
    db: Session, template_id: uuid.UUID, company_id: uuid.UUID,
) -> bool:
    template = get_template(db, template_id, company_id)
    if not template:
        return False
    db.delete(template)
    db.commit()
    return True


def apply_template(
    db: Session,
    template_id: uuid.UUID,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    data_esecuzione_richiesta,
    override_bank_account_id: uuid.UUID | None = None,
    override_priorita: str | None = None,
    override_note: str | None = None,
) -> PaymentOrder | None:
    template = get_template(db, template_id, company_id)
    if not template:
        return None

    dati = template.dati_template or {}
    riferimento = _generate_riferimento(db, company_id)

    bank_account_id = override_bank_account_id or template.bank_account_id
    priorita_str = override_priorita or dati.get("priorita", "normale")
    note = override_note or dati.get("note_default", "")

    order = PaymentOrder(
        company_id=company_id,
        creato_da_user_id=user_id,
        riferimento_interno=riferimento,
        tipo=template.tipo,
        stato=PaymentOrderStatus.BOZZA,
        bank_account_id=bank_account_id,
        data_esecuzione_richiesta=data_esecuzione_richiesta,
        valuta=dati.get("valuta", "EUR"),
        priorita=PaymentPriority(priorita_str),
        metadata_sepa=dati.get("metadata_sepa"),
        metadata_extra=dati.get("metadata_extra"),
        note=note,
    )
    db.add(order)

    # Update template usage stats
    template.volte_utilizzato += 1
    template.ultimo_utilizzo = datetime.now(timezone.utc)

    db.commit()
    db.refresh(order)
    return order
