"""Schedule management API endpoints."""
import os
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.schedule import (
    GenerateRecurringResponse,
    ScheduleAgingResponse,
    ScheduleAttachmentResponse,
    ScheduleCalendarDay,
    ScheduleCreateRequest,
    ScheduleListResponse,
    SchedulePaymentCreateRequest,
    SchedulePaymentResponse,
    ScheduleReminderCreateRequest,
    ScheduleReminderResponse,
    ScheduleResponse,
    ScheduleStatusUpdateRequest,
    ScheduleSummaryResponse,
    ScheduleSummaryTotals,
    ScheduleUpdateRequest,
)
from app.services import schedule_service

router = APIRouter(prefix="/schedules", tags=["schedules"])

UPLOAD_DIR = "uploads/schedules"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "application/xml",
    "text/xml",
}


def _build_response(s) -> dict:
    data = ScheduleResponse.model_validate(s).model_dump()
    data["bank_account_nickname"] = s.bank_account.nickname if s.bank_account else None
    return data


# --- Fixed-path endpoints (BEFORE {id}) ---

@router.get("/calendar", response_model=list[ScheduleCalendarDay])
def get_calendar(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020, le=2100),
    tipo: str | None = Query(None),
):
    company, _uc = company_data
    days = schedule_service.get_calendar(db, company.id, month, year, tipo)
    result = []
    for day in days:
        result.append({
            "data": day["data"],
            "scadenze": [_build_response(s) for s in day["scadenze"]],
        })
    return result


@router.get("/aging", response_model=ScheduleAgingResponse)
def get_aging(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return schedule_service.get_aging(db, company.id)


@router.get("/summary", response_model=ScheduleSummaryResponse)
def get_summary(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return schedule_service.get_summary(db, company.id)


@router.post("/generate-recurring", response_model=GenerateRecurringResponse)
def generate_all_recurring(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return schedule_service.generate_all_recurring(db, company.id)


@router.post("/check-reminders")
def check_reminders(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return schedule_service.check_reminders(db, company.id)


# --- CRUD ---

@router.get("", response_model=ScheduleListResponse)
def list_schedules(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    stato: str | None = Query(None),
    tipo: str | None = Query(None),
    counterparty_id: uuid.UUID | None = Query(None),
    bank_account_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    priorita: str | None = Query(None),
    is_ricorrente: bool | None = Query(None),
    importo_min: Decimal | None = Query(None),
    importo_max: Decimal | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("data_scadenza"),
    sort_order: str = Query("asc"),
):
    company, _uc = company_data
    items, total, totals = schedule_service.list_schedules(
        db, company.id,
        stato=stato, tipo=tipo,
        counterparty_id=counterparty_id,
        bank_account_id=bank_account_id,
        date_from=date_from, date_to=date_to,
        search=search, priorita=priorita,
        is_ricorrente=is_ricorrente,
        importo_min=importo_min, importo_max=importo_max,
        page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order,
    )
    return ScheduleListResponse(
        items=[_build_response(s) for s in items],
        total=total,
        page=page,
        page_size=page_size,
        totals=ScheduleSummaryTotals(**totals),
    )


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    s = schedule_service.get_schedule(db, schedule_id, company.id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")
    return _build_response(s)


@router.post("", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def create_schedule(
    body: ScheduleCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    s = schedule_service.create_schedule(db, company.id, current_user.id, data)
    return _build_response(s)


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: uuid.UUID,
    body: ScheduleUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_unset=True)
    s = schedule_service.update_schedule(db, schedule_id, company.id, data)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")
    return _build_response(s)


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_schedule(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    if not schedule_service.delete_schedule(db, schedule_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")


@router.put("/{schedule_id}/stato", response_model=ScheduleResponse)
def update_status(
    schedule_id: uuid.UUID,
    body: ScheduleStatusUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    s = schedule_service.update_schedule_status(db, schedule_id, company.id, body.stato)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")
    return _build_response(s)


# --- Payments ---

@router.get("/{schedule_id}/payments", response_model=list[SchedulePaymentResponse])
def list_payments(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return [SchedulePaymentResponse.model_validate(p) for p in schedule_service.list_payments(db, schedule_id, company.id)]


@router.post("/{schedule_id}/payments", response_model=SchedulePaymentResponse, status_code=status.HTTP_201_CREATED)
def create_payment(
    schedule_id: uuid.UUID,
    body: SchedulePaymentCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    p = schedule_service.create_payment(db, schedule_id, company.id, data)
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")
    return SchedulePaymentResponse.model_validate(p)


@router.delete("/{schedule_id}/payments/{payment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment(
    schedule_id: uuid.UUID,
    payment_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not schedule_service.delete_payment(db, payment_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pagamento non trovato")


# --- Recurrence ---

@router.get("/{schedule_id}/occurrences", response_model=list[ScheduleResponse])
def list_occurrences(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return [_build_response(s) for s in schedule_service.list_occurrences(db, schedule_id, company.id)]


@router.post("/{schedule_id}/generate-next", response_model=ScheduleResponse, status_code=status.HTTP_201_CREATED)
def generate_next(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    s = schedule_service.generate_next_occurrence(db, schedule_id, company.id)
    if not s:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Impossibile generare: scadenza non ricorrente o ricorrenza disattivata")
    return _build_response(s)


@router.put("/{schedule_id}/stop-recurrence", response_model=ScheduleResponse)
def stop_recurrence(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    s = schedule_service.stop_recurrence(db, schedule_id, company.id)
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")
    return _build_response(s)


# --- Reminders ---

@router.get("/{schedule_id}/reminders", response_model=list[ScheduleReminderResponse])
def list_reminders(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return [ScheduleReminderResponse.model_validate(r) for r in schedule_service.list_reminders(db, schedule_id, company.id)]


@router.post("/{schedule_id}/reminders", response_model=ScheduleReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(
    schedule_id: uuid.UUID,
    body: ScheduleReminderCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    r = schedule_service.create_reminder(db, schedule_id, company.id, data)
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")
    return ScheduleReminderResponse.model_validate(r)


@router.delete("/{schedule_id}/reminders/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(
    schedule_id: uuid.UUID,
    reminder_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not schedule_service.delete_reminder(db, reminder_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promemoria non trovato")


# --- Attachments ---

@router.get("/{schedule_id}/attachments", response_model=list[ScheduleAttachmentResponse])
def list_attachments(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return [ScheduleAttachmentResponse.model_validate(a) for a in schedule_service.list_attachments(db, schedule_id, company.id)]


@router.post("/{schedule_id}/attachments", response_model=ScheduleAttachmentResponse, status_code=status.HTTP_201_CREATED)
def upload_attachment(
    schedule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
    file: UploadFile = File(...),
):
    company, _uc = company_data

    # Validate
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Tipo file non ammesso: {file.content_type}")

    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="File troppo grande (max 10MB)")

    # Save file
    save_dir = os.path.join(UPLOAD_DIR, str(company.id), str(schedule_id))
    os.makedirs(save_dir, exist_ok=True)
    filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = os.path.join(save_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    att = schedule_service.create_attachment(
        db, schedule_id, company.id, current_user.id,
        filename=filename,
        original_filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        file_path=file_path,
    )
    if not att:
        os.remove(file_path)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scadenza non trovata")

    return ScheduleAttachmentResponse.model_validate(att)


@router.get("/attachments/{attachment_id}/download")
def download_attachment(
    attachment_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    att = schedule_service.download_attachment(db, attachment_id, company.id)
    if not att:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allegato non trovato")
    if not os.path.exists(att.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato su disco")
    return FileResponse(
        att.file_path,
        media_type=att.content_type,
        filename=att.original_filename,
    )


@router.delete("/attachments/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(
    attachment_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    att = schedule_service.download_attachment(db, attachment_id, company.id)
    if att and os.path.exists(att.file_path):
        os.remove(att.file_path)
    if not schedule_service.delete_attachment(db, attachment_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Allegato non trovato")
