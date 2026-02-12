"""Payment order service.

CRUD, workflow state machine, file generation, schedule integration.
"""
import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.enums import (
    PaymentLineStatus, PaymentOrderStatus, PaymentOrderType,
    PaymentPriority, ApprovalAction,
    ScheduleStatus, PaymentMethod,
)
from app.models.payment_approval import PaymentApproval
from app.models.payment_order import PaymentOrder
from app.models.payment_order_line import PaymentOrderLine
from app.models.schedule import Schedule
from app.models.schedule_payment import SchedulePayment

# --- State machine ---

ALLOWED_TRANSITIONS = {
    PaymentOrderStatus.BOZZA: [PaymentOrderStatus.DA_APPROVARE, PaymentOrderStatus.ANNULLATA],
    PaymentOrderStatus.DA_APPROVARE: [
        PaymentOrderStatus.APPROVATA, PaymentOrderStatus.BOZZA, PaymentOrderStatus.ANNULLATA,
    ],
    PaymentOrderStatus.APPROVATA: [PaymentOrderStatus.FILE_GENERATO, PaymentOrderStatus.ANNULLATA],
    PaymentOrderStatus.FILE_GENERATO: [
        PaymentOrderStatus.INVIATA_BANCA, PaymentOrderStatus.APPROVATA,
    ],
    PaymentOrderStatus.INVIATA_BANCA: [
        PaymentOrderStatus.ESEGUITA, PaymentOrderStatus.RIFIUTATA,
    ],
    # Terminal states
    PaymentOrderStatus.ESEGUITA: [],
    PaymentOrderStatus.RIFIUTATA: [],
    PaymentOrderStatus.ANNULLATA: [],
}

GENERATED_FILES_DIR = "generated_payments"


def _can_transition(current: PaymentOrderStatus, target: PaymentOrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS.get(current, [])


def _generate_riferimento(db: Session, company_id: uuid.UUID) -> str:
    year = date.today().year
    count = (
        db.query(func.count(PaymentOrder.id))
        .filter(
            PaymentOrder.company_id == company_id,
            PaymentOrder.riferimento_interno.like(f"PAG-{year}-%"),
        )
        .scalar()
    ) or 0
    return f"PAG-{year}-{count + 1:05d}"


def _recalculate_totals(order: PaymentOrder) -> None:
    included = [l for l in order.lines if l.stato == PaymentLineStatus.INCLUSA]
    order.importo_totale = sum(l.importo for l in included) if included else Decimal("0")
    order.numero_disposizioni = len(included)


# --- CRUD ---

def list_payment_orders(
    db: Session,
    company_id: uuid.UUID,
    *,
    stato: str | None = None,
    tipo: str | None = None,
    bank_account_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    importo_min: Decimal | None = None,
    importo_max: Decimal | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> tuple[list[PaymentOrder], int, dict]:
    q = db.query(PaymentOrder).filter(PaymentOrder.company_id == company_id)

    if stato:
        q = q.filter(PaymentOrder.stato == stato)
    if tipo:
        q = q.filter(PaymentOrder.tipo == tipo)
    if bank_account_id:
        q = q.filter(PaymentOrder.bank_account_id == bank_account_id)
    if date_from:
        q = q.filter(PaymentOrder.data_esecuzione_richiesta >= date_from)
    if date_to:
        q = q.filter(PaymentOrder.data_esecuzione_richiesta <= date_to)
    if importo_min is not None:
        q = q.filter(PaymentOrder.importo_totale >= importo_min)
    if importo_max is not None:
        q = q.filter(PaymentOrder.importo_totale <= importo_max)
    if search:
        pattern = f"%{search}%"
        q = q.filter(
            or_(
                PaymentOrder.riferimento_interno.ilike(pattern),
                PaymentOrder.note.ilike(pattern),
            )
        )

    total = q.count()
    summary = _compute_summary(db, company_id)

    sort_col = getattr(PaymentOrder, sort_by, PaymentOrder.created_at)
    if sort_order == "desc":
        q = q.order_by(sort_col.desc())
    else:
        q = q.order_by(sort_col.asc())

    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return items, total, summary


def _compute_summary(db: Session, company_id: uuid.UUID) -> dict:
    rows = (
        db.query(
            PaymentOrder.stato,
            func.count(PaymentOrder.id),
            func.coalesce(func.sum(PaymentOrder.importo_totale), 0),
        )
        .filter(PaymentOrder.company_id == company_id)
        .group_by(PaymentOrder.stato)
        .all()
    )

    summary = {
        "totale_bozze": 0, "totale_da_approvare": 0,
        "totale_approvate": 0, "totale_eseguite": 0,
        "importo_bozze": Decimal("0"), "importo_da_approvare": Decimal("0"),
        "importo_approvate": Decimal("0"), "importo_eseguite": Decimal("0"),
    }

    for stato_val, count, importo in rows:
        stato_str = stato_val.value if hasattr(stato_val, "value") else stato_val
        if stato_str == "bozza":
            summary["totale_bozze"] = count
            summary["importo_bozze"] = importo
        elif stato_str == "da_approvare":
            summary["totale_da_approvare"] = count
            summary["importo_da_approvare"] = importo
        elif stato_str in ("approvata", "file_generato", "inviata_banca"):
            summary["totale_approvate"] += count
            summary["importo_approvate"] += importo
        elif stato_str == "eseguita":
            summary["totale_eseguite"] = count
            summary["importo_eseguite"] = importo

    return summary


def get_payment_order(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> PaymentOrder | None:
    return (
        db.query(PaymentOrder)
        .filter(PaymentOrder.id == order_id, PaymentOrder.company_id == company_id)
        .first()
    )


def create_payment_order(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
) -> PaymentOrder:
    riferimento = _generate_riferimento(db, company_id)
    order = PaymentOrder(
        company_id=company_id,
        creato_da_user_id=user_id,
        riferimento_interno=riferimento,
        stato=PaymentOrderStatus.BOZZA,
        **data,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def update_payment_order(
    db: Session,
    order_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if order.stato != PaymentOrderStatus.BOZZA:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(order, key, value)

    db.commit()
    db.refresh(order)
    return order


def delete_payment_order(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> bool:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return False
    if order.stato != PaymentOrderStatus.BOZZA:
        return False
    db.delete(order)
    db.commit()
    return True


# --- Lines ---

def add_line(
    db: Session,
    order_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> PaymentOrderLine | None:
    order = get_payment_order(db, order_id, company_id)
    if not order or order.stato != PaymentOrderStatus.BOZZA:
        return None

    line = PaymentOrderLine(payment_order_id=order_id, **data)
    db.add(line)
    db.flush()

    db.refresh(order)
    _recalculate_totals(order)
    db.commit()
    db.refresh(line)
    return line


def update_line(
    db: Session,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    company_id: uuid.UUID,
    data: dict,
) -> PaymentOrderLine | None:
    order = get_payment_order(db, order_id, company_id)
    if not order or order.stato != PaymentOrderStatus.BOZZA:
        return None

    line = db.query(PaymentOrderLine).filter(
        PaymentOrderLine.id == line_id,
        PaymentOrderLine.payment_order_id == order_id,
    ).first()
    if not line:
        return None

    for key, value in data.items():
        if value is not None:
            setattr(line, key, value)

    db.flush()
    db.refresh(order)
    _recalculate_totals(order)
    db.commit()
    db.refresh(line)
    return line


def delete_line(
    db: Session,
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    company_id: uuid.UUID,
) -> bool:
    order = get_payment_order(db, order_id, company_id)
    if not order or order.stato != PaymentOrderStatus.BOZZA:
        return False

    line = db.query(PaymentOrderLine).filter(
        PaymentOrderLine.id == line_id,
        PaymentOrderLine.payment_order_id == order_id,
    ).first()
    if not line:
        return False

    db.delete(line)
    db.flush()
    db.refresh(order)
    _recalculate_totals(order)
    db.commit()
    return True


# --- Workflow ---

def submit_order(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if not _can_transition(order.stato, PaymentOrderStatus.DA_APPROVARE):
        return None
    if not order.lines or order.numero_disposizioni == 0:
        return None

    order.stato = PaymentOrderStatus.DA_APPROVARE
    db.commit()
    db.refresh(order)
    return order


def approve_order(
    db: Session,
    order_id: uuid.UUID,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    commento: str | None = None,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if not _can_transition(order.stato, PaymentOrderStatus.APPROVATA):
        return None
    # Separation of duties
    if order.creato_da_user_id == user_id:
        return None

    now = datetime.now(timezone.utc)
    order.stato = PaymentOrderStatus.APPROVATA
    order.approvato_da_user_id = user_id
    order.data_approvazione = now

    approval = PaymentApproval(
        payment_order_id=order_id,
        user_id=user_id,
        azione=ApprovalAction.APPROVATA,
        commento=commento,
        data_azione=now,
    )
    db.add(approval)
    db.commit()
    db.refresh(order)
    return order


def reject_order(
    db: Session,
    order_id: uuid.UUID,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    commento: str,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if not _can_transition(order.stato, PaymentOrderStatus.BOZZA):
        return None

    order.stato = PaymentOrderStatus.BOZZA
    order.approvato_da_user_id = None
    order.data_approvazione = None

    approval = PaymentApproval(
        payment_order_id=order_id,
        user_id=user_id,
        azione=ApprovalAction.RIFIUTATA,
        commento=commento,
        data_azione=datetime.now(timezone.utc),
    )
    db.add(approval)
    db.commit()
    db.refresh(order)
    return order


def get_approvals(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> list[PaymentApproval]:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return []
    return (
        db.query(PaymentApproval)
        .filter(PaymentApproval.payment_order_id == order_id)
        .order_by(PaymentApproval.data_azione.desc())
        .all()
    )


# --- File generation ---

def generate_file(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if not _can_transition(order.stato, PaymentOrderStatus.FILE_GENERATO):
        return None

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        return None

    from app.services.generators import (
        generate_sepa_ct, generate_riba, generate_sdd, generate_f24,
    )

    tipo_val = order.tipo.value if hasattr(order.tipo, "value") else order.tipo

    if tipo_val == "sepa_credit_transfer":
        content = generate_sepa_ct(order, company)
        ext = "xml"
    elif tipo_val == "riba":
        content = generate_riba(order, company)
        ext = "txt"
    elif tipo_val == "sdd":
        content = generate_sdd(order, company)
        ext = "xml"
    elif tipo_val == "f24":
        content = generate_f24(order, company)
        ext = "txt"
    else:
        return None

    # Save file
    save_dir = os.path.join(GENERATED_FILES_DIR, str(company_id))
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{order.riferimento_interno}.{ext}"
    file_path = os.path.join(save_dir, filename)

    mode = "wb" if isinstance(content, bytes) else "w"
    encoding = None if isinstance(content, bytes) else "utf-8"
    with open(file_path, mode, encoding=encoding) as f:
        f.write(content)

    now = datetime.now(timezone.utc)
    order.stato = PaymentOrderStatus.FILE_GENERATO
    order.file_generato_path = file_path
    order.file_generato_nome = filename
    order.file_generato_at = now

    db.commit()
    db.refresh(order)
    return order


def get_file_path(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> tuple[str, str] | None:
    order = get_payment_order(db, order_id, company_id)
    if not order or not order.file_generato_path:
        return None
    if not os.path.exists(order.file_generato_path):
        return None
    return order.file_generato_path, order.file_generato_nome or "payment_file"


# --- Execution ---

def mark_sent(
    db: Session, order_id: uuid.UUID, company_id: uuid.UUID,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if not _can_transition(order.stato, PaymentOrderStatus.INVIATA_BANCA):
        return None

    order.stato = PaymentOrderStatus.INVIATA_BANCA
    db.commit()
    db.refresh(order)
    return order


def mark_executed(
    db: Session,
    order_id: uuid.UUID,
    company_id: uuid.UUID,
    data_esecuzione: date | None = None,
) -> PaymentOrder | None:
    order = get_payment_order(db, order_id, company_id)
    if not order:
        return None
    if not _can_transition(order.stato, PaymentOrderStatus.ESEGUITA):
        return None

    exec_date = data_esecuzione or date.today()
    order.stato = PaymentOrderStatus.ESEGUITA

    # Update lines and linked schedules
    for line in order.lines:
        if line.stato == PaymentLineStatus.INCLUSA:
            line.stato = PaymentLineStatus.ESEGUITA

            if line.schedule_id:
                schedule = db.query(Schedule).filter(Schedule.id == line.schedule_id).first()
                if schedule:
                    # Create SchedulePayment
                    sp = SchedulePayment(
                        schedule_id=schedule.id,
                        importo=line.importo,
                        data_pagamento=exec_date,
                        metodo=_map_tipo_to_payment_method(order.tipo),
                        riferimento=order.riferimento_interno,
                        note=f"Pagamento da ordine {order.riferimento_interno}",
                    )
                    db.add(sp)

                    # Update schedule amounts
                    schedule.importo_pagato += line.importo
                    if schedule.importo_pagato >= schedule.importo_totale:
                        schedule.stato = ScheduleStatus.PAGATA
                        schedule.data_pagamento = exec_date
                    elif schedule.importo_pagato > 0:
                        schedule.stato = ScheduleStatus.PARZIALMENTE_PAGATA

    db.commit()
    db.refresh(order)
    return order


def _map_tipo_to_payment_method(tipo: PaymentOrderType) -> PaymentMethod | None:
    tipo_val = tipo.value if hasattr(tipo, "value") else tipo
    mapping = {
        "sepa_credit_transfer": PaymentMethod.BONIFICO,
        "riba": PaymentMethod.RI_BA,
        "sdd": PaymentMethod.SDD,
        "f24": PaymentMethod.F24,
        "bonifico_estero": PaymentMethod.BONIFICO,
    }
    return mapping.get(tipo_val)


# --- From schedules ---

def create_from_schedules(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    schedule_ids: list[uuid.UUID],
    bank_account_id: uuid.UUID | None = None,
    data_esecuzione_richiesta: date | None = None,
    priorita: str = "normale",
    note: str | None = None,
) -> PaymentOrder | None:
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.id.in_(schedule_ids),
            Schedule.company_id == company_id,
            Schedule.tipo == "passiva",
            Schedule.stato.in_([ScheduleStatus.APERTA, ScheduleStatus.PARZIALMENTE_PAGATA]),
        )
        .all()
    )

    if not schedules:
        return None

    riferimento = _generate_riferimento(db, company_id)
    exec_date = data_esecuzione_richiesta or date.today()

    order = PaymentOrder(
        company_id=company_id,
        creato_da_user_id=user_id,
        riferimento_interno=riferimento,
        tipo=PaymentOrderType.SEPA_CREDIT_TRANSFER,
        stato=PaymentOrderStatus.BOZZA,
        bank_account_id=bank_account_id,
        data_esecuzione_richiesta=exec_date,
        valuta="EUR",
        priorita=PaymentPriority(priorita),
        note=note,
    )
    db.add(order)
    db.flush()

    for schedule in schedules:
        residuo = schedule.importo_totale - schedule.importo_pagato
        if residuo <= 0:
            continue

        line = PaymentOrderLine(
            payment_order_id=order.id,
            beneficiario_nome=schedule.controparte_nome or "N/D",
            beneficiario_iban=schedule.controparte_iban,
            importo=residuo,
            valuta=schedule.valuta or "EUR",
            causale=f"Pag. {schedule.numero_documento or schedule.descrizione}"[:140],
            schedule_id=schedule.id,
            counterparty_id=schedule.counterparty_id,
            stato=PaymentLineStatus.INCLUSA,
        )
        db.add(line)

    db.flush()
    db.refresh(order)
    _recalculate_totals(order)
    db.commit()
    db.refresh(order)
    return order


# --- Summary ---

def get_summary(db: Session, company_id: uuid.UUID) -> dict:
    return _compute_summary(db, company_id)
