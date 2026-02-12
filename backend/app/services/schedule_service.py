"""Schedule management service.

CRUD operations, payment tracking, recurrence, aging, calendar views.
"""
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import Session

from app.models.enums import (
    RecurrenceType, SchedulePriority, ScheduleSource,
    ScheduleStatus, ScheduleType,
)
from app.models.schedule import Schedule
from app.models.schedule_attachment import ScheduleAttachment
from app.models.schedule_payment import SchedulePayment
from app.models.schedule_reminder import ScheduleReminder
from app.services.schedule_expected_service import (
    create_expected_from_schedule,
    delete_expected_for_schedule,
    sync_expected_with_schedule,
)

# Recurrence intervals
_RECURRENCE_DELTAS = {
    RecurrenceType.SETTIMANALE: relativedelta(weeks=1),
    RecurrenceType.MENSILE: relativedelta(months=1),
    RecurrenceType.BIMESTRALE: relativedelta(months=2),
    RecurrenceType.TRIMESTRALE: relativedelta(months=3),
    RecurrenceType.SEMESTRALE: relativedelta(months=6),
    RecurrenceType.ANNUALE: relativedelta(years=1),
}


# --- CRUD ---

def list_schedules(
    db: Session,
    company_id: uuid.UUID,
    *,
    stato: str | None = None,
    tipo: str | None = None,
    counterparty_id: uuid.UUID | None = None,
    bank_account_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    priorita: str | None = None,
    is_ricorrente: bool | None = None,
    importo_min: Decimal | None = None,
    importo_max: Decimal | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "data_scadenza",
    sort_order: str = "asc",
) -> tuple[list[Schedule], int, dict]:
    q = db.query(Schedule).filter(Schedule.company_id == company_id)

    if stato:
        q = q.filter(Schedule.stato == stato)
    if tipo:
        q = q.filter(Schedule.tipo == tipo)
    if counterparty_id:
        q = q.filter(Schedule.counterparty_id == counterparty_id)
    if bank_account_id:
        q = q.filter(Schedule.bank_account_id == bank_account_id)
    if date_from:
        q = q.filter(Schedule.data_scadenza >= date_from)
    if date_to:
        q = q.filter(Schedule.data_scadenza <= date_to)
    if priorita:
        q = q.filter(Schedule.priorita == priorita)
    if is_ricorrente is not None:
        q = q.filter(Schedule.is_ricorrente == is_ricorrente)
    if importo_min is not None:
        q = q.filter(Schedule.importo_totale >= importo_min)
    if importo_max is not None:
        q = q.filter(Schedule.importo_totale <= importo_max)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                Schedule.descrizione.ilike(pattern),
                Schedule.riferimento_documento.ilike(pattern),
                Schedule.controparte_nome.ilike(pattern),
                Schedule.numero_documento.ilike(pattern),
            )
        )

    total = q.count()

    # Totals
    totals = _compute_totals(db, company_id)

    # Sorting
    sort_col = getattr(Schedule, sort_by, Schedule.data_scadenza)
    if sort_order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, totals


def _compute_totals(db: Session, company_id: uuid.UUID) -> dict:
    rows = (
        db.query(
            Schedule.stato,
            Schedule.tipo,
            func.count(Schedule.id),
            func.coalesce(func.sum(Schedule.importo_totale - Schedule.importo_pagato), 0),
        )
        .filter(Schedule.company_id == company_id)
        .group_by(Schedule.stato, Schedule.tipo)
        .all()
    )

    totals = {
        "somma_attive_aperte": Decimal("0"),
        "somma_passive_aperte": Decimal("0"),
        "somma_scadute": Decimal("0"),
        "conteggio_aperte": 0,
        "conteggio_parziali": 0,
        "conteggio_pagate": 0,
        "conteggio_scadute": 0,
        "conteggio_annullate": 0,
    }

    for stato_val, tipo_val, count, residuo in rows:
        stato_str = stato_val.value if hasattr(stato_val, "value") else stato_val
        tipo_str = tipo_val.value if hasattr(tipo_val, "value") else tipo_val

        if stato_str == "aperta":
            totals["conteggio_aperte"] += count
            if tipo_str == "attiva":
                totals["somma_attive_aperte"] += residuo
            else:
                totals["somma_passive_aperte"] += residuo
        elif stato_str == "parzialmente_pagata":
            totals["conteggio_parziali"] += count
            if tipo_str == "attiva":
                totals["somma_attive_aperte"] += residuo
            else:
                totals["somma_passive_aperte"] += residuo
        elif stato_str == "pagata":
            totals["conteggio_pagate"] += count
        elif stato_str == "scaduta":
            totals["conteggio_scadute"] += count
            totals["somma_scadute"] += residuo
        elif stato_str == "annullata":
            totals["conteggio_annullate"] += count

    return totals


def get_schedule(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> Schedule | None:
    return (
        db.query(Schedule)
        .filter(Schedule.id == schedule_id, Schedule.company_id == company_id)
        .first()
    )


def create_schedule(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
) -> Schedule:
    schedule = Schedule(
        company_id=company_id,
        created_by_user_id=user_id,
        **data,
    )
    db.add(schedule)
    db.flush()

    # Set up recurrence
    if schedule.is_ricorrente and schedule.ricorrenza_tipo:
        delta = _RECURRENCE_DELTAS.get(schedule.ricorrenza_tipo)
        if delta:
            schedule.ricorrenza_prossima_generazione = schedule.data_scadenza + delta

    # Create linked ExpectedTransaction
    create_expected_from_schedule(db, schedule)

    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(
    db: Session,
    schedule_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> Schedule | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(schedule, key, value)

    # Sync with ExpectedTransaction
    sync_expected_with_schedule(db, schedule)

    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return False

    delete_expected_for_schedule(db, schedule)
    db.delete(schedule)
    db.commit()
    return True


# --- Status ---

def update_schedule_status(
    db: Session,
    schedule_id: uuid.UUID,
    company_id: uuid.UUID,
    new_status: str,
) -> Schedule | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    schedule.stato = ScheduleStatus(new_status)
    if new_status == "annullata" and schedule.expected_transaction_id:
        from app.models.expected_transaction import ExpectedTransaction
        from app.models.enums import ExpectedTransactionStatus
        et = db.get(ExpectedTransaction, schedule.expected_transaction_id)
        if et:
            et.status = ExpectedTransactionStatus.CANCELLED

    db.commit()
    db.refresh(schedule)
    return schedule


# --- Payments ---

def list_payments(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> list[SchedulePayment]:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return []
    return (
        db.query(SchedulePayment)
        .filter(SchedulePayment.schedule_id == schedule_id)
        .order_by(SchedulePayment.data_pagamento.desc())
        .all()
    )


def create_payment(
    db: Session,
    schedule_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> SchedulePayment | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    payment = SchedulePayment(schedule_id=schedule_id, **data)
    db.add(payment)

    # Update schedule amounts
    schedule.importo_pagato += payment.importo
    if schedule.importo_pagato >= schedule.importo_totale:
        schedule.stato = ScheduleStatus.PAGATA
        schedule.data_pagamento = payment.data_pagamento
    elif schedule.importo_pagato > 0:
        schedule.stato = ScheduleStatus.PARZIALMENTE_PAGATA

    db.commit()
    db.refresh(payment)
    return payment


def delete_payment(db: Session, payment_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    payment = db.get(SchedulePayment, payment_id)
    if not payment:
        return False

    schedule = get_schedule(db, payment.schedule_id, company_id)
    if not schedule:
        return False

    # Recalculate
    schedule.importo_pagato -= payment.importo
    if schedule.importo_pagato <= 0:
        schedule.importo_pagato = Decimal("0")
        schedule.stato = ScheduleStatus.APERTA
        schedule.data_pagamento = None
    elif schedule.importo_pagato < schedule.importo_totale:
        schedule.stato = ScheduleStatus.PARZIALMENTE_PAGATA
        schedule.data_pagamento = None

    db.delete(payment)
    db.commit()
    return True


# --- Recurrence ---

def list_occurrences(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> list[Schedule]:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return []

    # Find parent: either this is the parent, or find the parent
    parent_id = schedule.ricorrenza_parent_id or schedule.id
    return (
        db.query(Schedule)
        .filter(
            Schedule.company_id == company_id,
            or_(
                Schedule.id == parent_id,
                Schedule.ricorrenza_parent_id == parent_id,
            ),
        )
        .order_by(Schedule.data_scadenza.asc())
        .all()
    )


def generate_next_occurrence(
    db: Session,
    schedule_id: uuid.UUID,
    company_id: uuid.UUID,
) -> Schedule | None:
    parent = get_schedule(db, schedule_id, company_id)
    if not parent or not parent.is_ricorrente or not parent.ricorrenza_tipo:
        return None
    if not parent.ricorrenza_attiva:
        return None

    delta = _RECURRENCE_DELTAS.get(parent.ricorrenza_tipo)
    if not delta:
        return None

    next_date = parent.ricorrenza_prossima_generazione or (parent.data_scadenza + delta)

    # Check end date
    if parent.ricorrenza_fine and next_date > parent.ricorrenza_fine:
        parent.ricorrenza_attiva = False
        db.commit()
        return None

    # Check for duplicate (idempotent)
    existing = (
        db.query(Schedule)
        .filter(
            Schedule.ricorrenza_parent_id == parent.id,
            Schedule.data_scadenza == next_date,
        )
        .first()
    )
    if existing:
        return existing

    child = Schedule(
        company_id=parent.company_id,
        tipo=parent.tipo,
        stato=ScheduleStatus.APERTA,
        descrizione=parent.descrizione,
        importo_totale=parent.importo_totale,
        importo_pagato=Decimal("0"),
        valuta=parent.valuta,
        data_scadenza=next_date,
        tipo_documento=parent.tipo_documento,
        numero_documento=None,
        riferimento_documento=parent.riferimento_documento,
        controparte_nome=parent.controparte_nome,
        controparte_iban=parent.controparte_iban,
        counterparty_id=parent.counterparty_id,
        bank_account_id=parent.bank_account_id,
        priorita=parent.priorita,
        metodo_pagamento=parent.metodo_pagamento,
        categoria_id=parent.categoria_id,
        source=ScheduleSource.RICORRENZA_AUTO,
        is_ricorrente=False,
        ricorrenza_parent_id=parent.id,
        created_by_user_id=parent.created_by_user_id,
    )
    db.add(child)
    db.flush()

    # Create linked ExpectedTransaction for child
    create_expected_from_schedule(db, child)

    # Update parent's next generation date
    parent.ricorrenza_prossima_generazione = next_date + delta
    if parent.ricorrenza_fine and parent.ricorrenza_prossima_generazione > parent.ricorrenza_fine:
        parent.ricorrenza_attiva = False

    db.commit()
    db.refresh(child)
    return child


def stop_recurrence(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> Schedule | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    schedule.ricorrenza_attiva = False
    schedule.ricorrenza_prossima_generazione = None
    db.commit()
    db.refresh(schedule)
    return schedule


def generate_all_recurring(db: Session, company_id: uuid.UUID) -> dict:
    """Generate next occurrence for all active recurring schedules. Idempotent."""
    today = date.today()
    parents = (
        db.query(Schedule)
        .filter(
            Schedule.company_id == company_id,
            Schedule.is_ricorrente == True,
            Schedule.ricorrenza_attiva == True,
            Schedule.ricorrenza_prossima_generazione <= today,
        )
        .all()
    )

    result = {"generati": 0, "errori": 0, "dettaglio": []}
    for parent in parents:
        try:
            child = generate_next_occurrence(db, parent.id, company_id)
            if child:
                result["generati"] += 1
                result["dettaglio"].append(f"Generata scadenza {child.descrizione} per {child.data_scadenza}")
        except Exception as e:
            result["errori"] += 1
            result["dettaglio"].append(f"Errore per {parent.descrizione}: {e}")

    return result


# --- Reminders ---

def list_reminders(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> list[ScheduleReminder]:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return []
    return (
        db.query(ScheduleReminder)
        .filter(ScheduleReminder.schedule_id == schedule_id)
        .order_by(ScheduleReminder.giorni_prima.asc())
        .all()
    )


def create_reminder(
    db: Session,
    schedule_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> ScheduleReminder | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    reminder = ScheduleReminder(schedule_id=schedule_id, **data)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    return reminder


def delete_reminder(db: Session, reminder_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    reminder = db.get(ScheduleReminder, reminder_id)
    if not reminder:
        return False

    schedule = get_schedule(db, reminder.schedule_id, company_id)
    if not schedule:
        return False

    db.delete(reminder)
    db.commit()
    return True


def check_reminders(db: Session, company_id: uuid.UUID) -> dict:
    """Check for reminders that should fire today."""
    today = date.today()
    reminders = (
        db.query(ScheduleReminder)
        .join(Schedule)
        .filter(
            Schedule.company_id == company_id,
            ScheduleReminder.inviato == False,
            Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA]),
        )
        .all()
    )

    triggered = []
    for rem in reminders:
        schedule = db.get(Schedule, rem.schedule_id)
        if not schedule:
            continue
        trigger_date = schedule.data_scadenza - timedelta(days=rem.giorni_prima)
        if today >= trigger_date:
            rem.inviato = True
            rem.data_invio = today
            triggered.append({
                "schedule_id": str(schedule.id),
                "descrizione": schedule.descrizione,
                "data_scadenza": str(schedule.data_scadenza),
                "giorni_prima": rem.giorni_prima,
            })

    db.commit()
    return {"triggered": len(triggered), "reminders": triggered}


# --- Attachments ---

def list_attachments(db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID) -> list[ScheduleAttachment]:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return []
    return (
        db.query(ScheduleAttachment)
        .filter(ScheduleAttachment.schedule_id == schedule_id)
        .order_by(ScheduleAttachment.created_at.desc())
        .all()
    )


def create_attachment(
    db: Session,
    schedule_id: uuid.UUID,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str,
    original_filename: str,
    content_type: str,
    file_size: int,
    file_path: str,
) -> ScheduleAttachment | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    attachment = ScheduleAttachment(
        schedule_id=schedule_id,
        filename=filename,
        original_filename=original_filename,
        content_type=content_type,
        file_size=file_size,
        file_path=file_path,
        uploaded_by_user_id=user_id,
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment


def download_attachment(db: Session, attachment_id: uuid.UUID, company_id: uuid.UUID) -> ScheduleAttachment | None:
    att = db.get(ScheduleAttachment, attachment_id)
    if not att:
        return None
    schedule = get_schedule(db, att.schedule_id, company_id)
    if not schedule:
        return None
    return att


def delete_attachment(db: Session, attachment_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    att = db.get(ScheduleAttachment, attachment_id)
    if not att:
        return False
    schedule = get_schedule(db, att.schedule_id, company_id)
    if not schedule:
        return False

    db.delete(att)
    db.commit()
    return True


# --- Aggregate views ---

def get_calendar(
    db: Session,
    company_id: uuid.UUID,
    month: int,
    year: int,
    tipo: str | None = None,
) -> list[dict]:
    """Return schedules grouped by day for a given month."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)

    q = (
        db.query(Schedule)
        .filter(
            Schedule.company_id == company_id,
            Schedule.data_scadenza >= first_day,
            Schedule.data_scadenza <= last_day,
            Schedule.stato != ScheduleStatus.ANNULLATA,
        )
    )
    if tipo:
        q = q.filter(Schedule.tipo == tipo)

    schedules = q.order_by(Schedule.data_scadenza.asc()).all()

    by_day: dict[date, list] = defaultdict(list)
    for s in schedules:
        by_day[s.data_scadenza].append(s)

    return [{"data": d, "scadenze": items} for d, items in sorted(by_day.items())]


def get_aging(db: Session, company_id: uuid.UUID) -> dict:
    """Calculate aging breakdown for open schedules."""
    today = date.today()
    open_statuses = [ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA, ScheduleStatus.SCADUTA]

    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.company_id == company_id,
            Schedule.stato.in_(open_statuses),
        )
        .all()
    )

    bands = [
        ("Scadute > 90gg", -999999, -90),
        ("Scadute 61-90gg", -90, -60),
        ("Scadute 31-60gg", -60, -30),
        ("Scadute 1-30gg", -30, 0),
        ("In scadenza 0-7gg", 0, 7),
        ("8-30gg", 7, 30),
        ("31-60gg", 30, 60),
        ("61-90gg", 60, 90),
        ("> 90gg", 90, 999999),
    ]

    result = {"attive": [], "passive": []}
    for tipo_key in ["attiva", "passiva"]:
        tipo_schedules = [s for s in schedules if s.tipo.value == tipo_key]
        for label, lower, upper in bands:
            band_items = []
            for s in tipo_schedules:
                days = (s.data_scadenza - today).days
                if lower < days <= upper or (lower == -999999 and days <= upper) or (upper == 999999 and days > lower):
                    band_items.append(s)

            if band_items:
                result["attive" if tipo_key == "attiva" else "passive"].append({
                    "fascia": label,
                    "conteggio": len(band_items),
                    "importo_totale": sum(s.importo_totale for s in band_items),
                    "importo_residuo": sum(s.importo_totale - s.importo_pagato for s in band_items),
                })

    return result


def get_summary(db: Session, company_id: uuid.UUID) -> dict:
    """Get summary stats for the dashboard."""
    today = date.today()
    prossimi_7gg = today + timedelta(days=7)

    # Base counts
    rows = (
        db.query(
            Schedule.tipo,
            Schedule.stato,
            func.count(Schedule.id),
            func.coalesce(func.sum(Schedule.importo_totale - Schedule.importo_pagato), 0),
        )
        .filter(Schedule.company_id == company_id)
        .group_by(Schedule.tipo, Schedule.stato)
        .all()
    )

    totale_attive = 0
    totale_passive = 0
    totale_aperte = 0
    totale_scadute = 0
    somma_attive_aperte = Decimal("0")
    somma_passive_aperte = Decimal("0")
    somma_scadute = Decimal("0")

    for tipo_val, stato_val, count, residuo in rows:
        tipo_str = tipo_val.value if hasattr(tipo_val, "value") else tipo_val
        stato_str = stato_val.value if hasattr(stato_val, "value") else stato_val

        if tipo_str == "attiva":
            totale_attive += count
        else:
            totale_passive += count

        if stato_str in ("aperta", "parzialmente_pagata"):
            totale_aperte += count
            if tipo_str == "attiva":
                somma_attive_aperte += residuo
            else:
                somma_passive_aperte += residuo
        elif stato_str == "scaduta":
            totale_scadute += count
            somma_scadute += residuo

    # Prossime 7 giorni
    prossime_count = (
        db.query(func.count(Schedule.id))
        .filter(
            Schedule.company_id == company_id,
            Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA]),
            Schedule.data_scadenza >= today,
            Schedule.data_scadenza <= prossimi_7gg,
        )
        .scalar()
    ) or 0

    # Ricorrenti attive
    ricorrenti_count = (
        db.query(func.count(Schedule.id))
        .filter(
            Schedule.company_id == company_id,
            Schedule.is_ricorrente == True,
            Schedule.ricorrenza_attiva == True,
        )
        .scalar()
    ) or 0

    return {
        "totale_attive": totale_attive,
        "totale_passive": totale_passive,
        "totale_aperte": totale_aperte,
        "totale_scadute": totale_scadute,
        "somma_attive_aperte": somma_attive_aperte,
        "somma_passive_aperte": somma_passive_aperte,
        "somma_scadute": somma_scadute,
        "prossime_7_giorni": prossime_count,
        "ricorrenti_attive": ricorrenti_count,
    }
