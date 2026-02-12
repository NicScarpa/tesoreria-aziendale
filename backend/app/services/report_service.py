"""Report Service — CRUD for ReportDefinition, ReportExecution, ReportSchedule."""
import os
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.enums import (
    ReportExecutionStatus, ReportFormat, ReportFrequency, ReportType,
)
from app.models.report_definition import ReportDefinition
from app.models.report_execution import ReportExecution
from app.models.report_schedule import ReportSchedule


# --- ReportDefinition CRUD ---

def list_definitions(
    db: Session,
    company_id: uuid.UUID,
    *,
    tipo: str | None = None,
    is_preferito: bool | None = None,
    search: str | None = None,
) -> list[ReportDefinition]:
    q = db.query(ReportDefinition).filter(
        or_(
            ReportDefinition.company_id == company_id,
            ReportDefinition.company_id.is_(None),
        )
    )
    if tipo:
        q = q.filter(ReportDefinition.tipo == tipo)
    if is_preferito is not None:
        q = q.filter(ReportDefinition.is_preferito == is_preferito)
    if search:
        q = q.filter(ReportDefinition.nome.ilike(f"%{search}%"))

    return q.order_by(ReportDefinition.sort_order.asc()).all()


def get_definition(
    db: Session, definition_id: uuid.UUID, company_id: uuid.UUID
) -> ReportDefinition | None:
    return (
        db.query(ReportDefinition)
        .filter(
            ReportDefinition.id == definition_id,
            or_(
                ReportDefinition.company_id == company_id,
                ReportDefinition.company_id.is_(None),
            ),
        )
        .first()
    )


def create_definition(
    db: Session, company_id: uuid.UUID, data: dict
) -> ReportDefinition:
    definition = ReportDefinition(
        company_id=company_id,
        nome=data["nome"],
        descrizione=data.get("descrizione"),
        tipo=ReportType(data.get("tipo", "personalizzato")),
        formato_default=ReportFormat(data.get("formato_default", "pdf")),
        parametri_default=data.get("parametri_default"),
        layout=data.get("layout"),
        is_system=False,
    )
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return definition


def update_definition(
    db: Session, definition_id: uuid.UUID, company_id: uuid.UUID, data: dict
) -> ReportDefinition | None:
    definition = (
        db.query(ReportDefinition)
        .filter(
            ReportDefinition.id == definition_id,
            ReportDefinition.company_id == company_id,
            ReportDefinition.is_system == False,  # noqa: E712
        )
        .first()
    )
    if not definition:
        return None

    for key, value in data.items():
        if value is not None:
            if key == "formato_default":
                setattr(definition, key, ReportFormat(value))
            else:
                setattr(definition, key, value)

    db.commit()
    db.refresh(definition)
    return definition


def delete_definition(
    db: Session, definition_id: uuid.UUID, company_id: uuid.UUID
) -> bool:
    definition = (
        db.query(ReportDefinition)
        .filter(
            ReportDefinition.id == definition_id,
            ReportDefinition.company_id == company_id,
            ReportDefinition.is_system == False,  # noqa: E712
        )
        .first()
    )
    if not definition:
        return False
    db.delete(definition)
    db.commit()
    return True


def toggle_preferito(
    db: Session, definition_id: uuid.UUID, company_id: uuid.UUID
) -> ReportDefinition | None:
    definition = get_definition(db, definition_id, company_id)
    if not definition:
        return None
    definition.is_preferito = not definition.is_preferito
    db.commit()
    db.refresh(definition)
    return definition


# --- ReportExecution CRUD ---

def list_executions(
    db: Session,
    company_id: uuid.UUID,
    *,
    tipo: str | None = None,
    stato: str | None = None,
    report_definition_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ReportExecution], int]:
    q = db.query(ReportExecution).filter(ReportExecution.company_id == company_id)

    if tipo:
        q = q.filter(ReportExecution.tipo == tipo)
    if stato:
        q = q.filter(ReportExecution.stato == stato)
    if report_definition_id:
        q = q.filter(ReportExecution.report_definition_id == report_definition_id)

    total = q.count()
    items = (
        q.order_by(ReportExecution.data_generazione.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_execution(
    db: Session, execution_id: uuid.UUID, company_id: uuid.UUID
) -> ReportExecution | None:
    return (
        db.query(ReportExecution)
        .filter(
            ReportExecution.id == execution_id,
            ReportExecution.company_id == company_id,
        )
        .first()
    )


def create_execution(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    nome: str,
    tipo: str,
    formato: str,
    parametri: dict | None = None,
    report_definition_id: uuid.UUID | None = None,
) -> ReportExecution:
    execution = ReportExecution(
        company_id=company_id,
        report_definition_id=report_definition_id,
        generato_da_user_id=user_id,
        nome=nome,
        tipo=tipo,
        formato=ReportFormat(formato),
        stato=ReportExecutionStatus.IN_CODA,
        parametri=parametri,
        data_scadenza_file=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)
    return execution


def complete_execution(
    db: Session,
    execution: ReportExecution,
    file_path: str,
    file_size: int,
    righe_totali: int,
    risultato: dict | None = None,
) -> ReportExecution:
    execution.stato = ReportExecutionStatus.COMPLETATO
    execution.file_path = file_path
    execution.file_size = file_size
    execution.righe_totali = righe_totali
    execution.risultato = risultato
    execution.data_completamento = datetime.now(timezone.utc)
    db.commit()
    db.refresh(execution)
    return execution


def fail_execution(
    db: Session, execution: ReportExecution, errore: str
) -> ReportExecution:
    execution.stato = ReportExecutionStatus.ERRORE
    execution.errore = errore
    execution.data_completamento = datetime.now(timezone.utc)
    db.commit()
    db.refresh(execution)
    return execution


def delete_execution(
    db: Session, execution_id: uuid.UUID, company_id: uuid.UUID
) -> bool:
    execution = get_execution(db, execution_id, company_id)
    if not execution:
        return False
    # Delete file if exists
    if execution.file_path and os.path.exists(execution.file_path):
        os.remove(execution.file_path)
    db.delete(execution)
    db.commit()
    return True


# --- ReportSchedule CRUD ---

def list_schedules(
    db: Session, company_id: uuid.UUID
) -> list[ReportSchedule]:
    return (
        db.query(ReportSchedule)
        .filter(ReportSchedule.company_id == company_id)
        .order_by(ReportSchedule.created_at.desc())
        .all()
    )


def get_schedule(
    db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID
) -> ReportSchedule | None:
    return (
        db.query(ReportSchedule)
        .filter(
            ReportSchedule.id == schedule_id,
            ReportSchedule.company_id == company_id,
        )
        .first()
    )


def create_schedule(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    data: dict,
) -> ReportSchedule:
    frequenza = ReportFrequency(data["frequenza"])
    prossima = _calcola_prossima_esecuzione(frequenza)

    schedule = ReportSchedule(
        company_id=company_id,
        report_definition_id=data["report_definition_id"],
        creato_da_user_id=user_id,
        nome=data["nome"],
        frequenza=frequenza,
        formato=ReportFormat(data.get("formato", "pdf")),
        parametri=data.get("parametri"),
        attivo=True,
        prossima_esecuzione=prossima,
    )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return schedule


def update_schedule(
    db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID, data: dict
) -> ReportSchedule | None:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return None

    for key, value in data.items():
        if value is not None:
            if key == "frequenza":
                setattr(schedule, key, ReportFrequency(value))
                schedule.prossima_esecuzione = _calcola_prossima_esecuzione(
                    ReportFrequency(value)
                )
            elif key == "formato":
                setattr(schedule, key, ReportFormat(value))
            else:
                setattr(schedule, key, value)

    db.commit()
    db.refresh(schedule)
    return schedule


def delete_schedule(
    db: Session, schedule_id: uuid.UUID, company_id: uuid.UUID
) -> bool:
    schedule = get_schedule(db, schedule_id, company_id)
    if not schedule:
        return False
    db.delete(schedule)
    db.commit()
    return True


def _calcola_prossima_esecuzione(frequenza: ReportFrequency) -> datetime:
    now = datetime.now(timezone.utc)
    if frequenza == ReportFrequency.GIORNALIERO:
        return now + timedelta(days=1)
    elif frequenza == ReportFrequency.SETTIMANALE:
        return now + timedelta(weeks=1)
    elif frequenza == ReportFrequency.MENSILE:
        return now + timedelta(days=30)
    elif frequenza == ReportFrequency.TRIMESTRALE:
        return now + timedelta(days=90)
    return now + timedelta(days=30)
