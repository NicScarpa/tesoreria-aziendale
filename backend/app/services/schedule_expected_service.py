"""Integration service between Schedule and ExpectedTransaction.

Handles:
- Auto-creation of ExpectedTransaction when a Schedule is created
- Sync updates when Schedule is modified
- Reconciliation callback to update Schedule payment status
"""
import logging
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.enums import (
    ExpectedDocumentType, ExpectedTransactionSource,
    ExpectedTransactionStatus, ExpectedTransactionType,
    ScheduleStatus, ScheduleType,
)
from app.models.expected_transaction import ExpectedTransaction
from app.models.schedule import Schedule
from app.models.schedule_payment import SchedulePayment

logger = logging.getLogger(__name__)

# Mapping schedule document types to expected document types
_DOC_TYPE_MAP = {
    "fattura_vendita": ExpectedDocumentType.SALES_INVOICE,
    "fattura_acquisto": ExpectedDocumentType.PURCHASE_INVOICE,
    "nota_credito": ExpectedDocumentType.CREDIT_NOTE,
    "nota_debito": ExpectedDocumentType.DEBIT_NOTE,
    "stipendio": ExpectedDocumentType.SALARY,
    "tassa_f24": ExpectedDocumentType.TAX,
    "contributo": ExpectedDocumentType.OTHER,
    "affitto": ExpectedDocumentType.OTHER,
    "utenza": ExpectedDocumentType.OTHER,
    "rata_prestito": ExpectedDocumentType.OTHER,
    "altro": ExpectedDocumentType.OTHER,
}


def create_expected_from_schedule(db: Session, schedule: Schedule) -> ExpectedTransaction:
    """Create an ExpectedTransaction linked to a Schedule."""
    et_type = (
        ExpectedTransactionType.EXPECTED_INFLOW
        if schedule.tipo == ScheduleType.ATTIVA
        else ExpectedTransactionType.EXPECTED_OUTFLOW
    )
    doc_value = getattr(schedule.tipo_documento, 'value', schedule.tipo_documento)
    doc_type = _DOC_TYPE_MAP.get(doc_value, ExpectedDocumentType.OTHER)

    et = ExpectedTransaction(
        company_id=schedule.company_id,
        bank_account_id=schedule.bank_account_id,
        counterpart_name=schedule.controparte_nome,
        counterpart_iban=schedule.controparte_iban,
        type=et_type,
        expected_amount=schedule.importo_totale,
        currency=schedule.valuta,
        due_date=schedule.data_scadenza,
        description=schedule.descrizione,
        reference_number=schedule.riferimento_documento,
        document_type=doc_type,
        status=ExpectedTransactionStatus.OPEN,
        matched_amount=Decimal("0"),
        schedule_id=schedule.id,
        source=ExpectedTransactionSource.SCHEDULE,
    )
    db.add(et)
    db.flush()

    # Link back
    schedule.expected_transaction_id = et.id
    db.flush()

    return et


def sync_expected_with_schedule(db: Session, schedule: Schedule) -> None:
    """Update the linked ExpectedTransaction when schedule changes."""
    if not schedule.expected_transaction_id:
        return

    et = db.get(ExpectedTransaction, schedule.expected_transaction_id)
    if not et:
        return

    et_type = (
        ExpectedTransactionType.EXPECTED_INFLOW
        if schedule.tipo == ScheduleType.ATTIVA
        else ExpectedTransactionType.EXPECTED_OUTFLOW
    )

    et.type = et_type
    et.expected_amount = schedule.importo_totale
    et.due_date = schedule.data_scadenza
    et.counterpart_name = schedule.controparte_nome
    et.counterpart_iban = schedule.controparte_iban
    et.bank_account_id = schedule.bank_account_id
    et.description = schedule.descrizione
    et.reference_number = schedule.riferimento_documento
    doc_value = getattr(schedule.tipo_documento, 'value', schedule.tipo_documento)
    et.document_type = _DOC_TYPE_MAP.get(doc_value, ExpectedDocumentType.OTHER)

    db.flush()


def delete_expected_for_schedule(db: Session, schedule: Schedule) -> None:
    """Delete the linked ExpectedTransaction when schedule is deleted."""
    if not schedule.expected_transaction_id:
        return

    et = db.get(ExpectedTransaction, schedule.expected_transaction_id)
    if et:
        db.delete(et)
        db.flush()


def on_reconciliation_confirmed(db: Session, reconciliation) -> None:
    """Callback when a reconciliation is confirmed.

    For each line with an expected_transaction that has schedule_id:
    - Find the Schedule
    - Create a SchedulePayment
    - Update importo_pagato
    - Update stato
    """
    for line in reconciliation.lines:
        if not line.expected_transaction_id:
            continue

        et = db.get(ExpectedTransaction, line.expected_transaction_id)
        if not et or not et.schedule_id:
            continue

        try:
            schedule = db.get(Schedule, et.schedule_id)
            if not schedule:
                continue

            # Create payment record
            payment = SchedulePayment(
                schedule_id=schedule.id,
                importo=line.matched_amount,
                data_pagamento=date.today(),
                riferimento=f"Riconciliazione #{str(reconciliation.id)[:8]}",
                note="Pagamento da riconciliazione automatica",
                reconciliation_id=reconciliation.id,
            )
            db.add(payment)

            # Update schedule amounts
            schedule.importo_pagato += line.matched_amount

            # Update status
            if schedule.importo_pagato >= schedule.importo_totale:
                schedule.stato = ScheduleStatus.PAGATA
                schedule.data_pagamento = date.today()
            elif schedule.importo_pagato > 0:
                schedule.stato = ScheduleStatus.PARZIALMENTE_PAGATA

            db.flush()

        except Exception as e:
            logger.error(f"Schedule callback error for schedule {et.schedule_id}: {e}")
            # Don't rollback - the reconciliation remains valid
