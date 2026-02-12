"""Payment management API endpoints."""
import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.payment import (
    IbanValidationRequest,
    IbanValidationResponse,
    MarkExecutedRequest,
    PaymentApprovalRequest,
    PaymentApprovalResponse,
    PaymentFromSchedulesRequest,
    PaymentOrderCreateRequest,
    PaymentOrderLineCreateRequest,
    PaymentOrderLineResponse,
    PaymentOrderLineUpdateRequest,
    PaymentOrderListResponse,
    PaymentOrderResponse,
    PaymentOrderSummaryResponse,
    PaymentOrderUpdateRequest,
    PaymentRejectRequest,
    PaymentTemplateApplyRequest,
    PaymentTemplateCreateRequest,
    PaymentTemplateResponse,
)
from app.services import payment_order_service, payment_template_service

router = APIRouter(prefix="/payments", tags=["payments"])


def _build_order_response(o) -> dict:
    data = PaymentOrderResponse.model_validate(o).model_dump()
    data["bank_account_nickname"] = o.bank_account.nickname if o.bank_account else None
    if o.created_by_user:
        data["creato_da_user_name"] = f"{o.created_by_user.first_name} {o.created_by_user.last_name}"
    return data


def _build_approval_response(a) -> dict:
    data = PaymentApprovalResponse.model_validate(a).model_dump()
    if a.user:
        data["user_name"] = f"{a.user.first_name} {a.user.last_name}"
    return data


# --- Fixed-path endpoints (BEFORE {id}) ---

@router.get("/summary", response_model=PaymentOrderSummaryResponse)
def get_summary(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return payment_order_service.get_summary(db, company.id)


@router.post("/validate-iban", response_model=IbanValidationResponse)
def validate_iban(
    body: IbanValidationRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    from app.services.generators.iban_validator import validate_iban as _validate
    valid, error = _validate(body.iban)
    return IbanValidationResponse(
        valid=valid,
        iban_formatted=body.iban.replace(" ", "").upper() if valid else None,
        error=error if not valid else None,
    )


@router.post("/from-schedules", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
def create_from_schedules(
    body: PaymentFromSchedulesRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    order = payment_order_service.create_from_schedules(
        db, company.id, current_user.id,
        schedule_ids=body.schedule_ids,
        bank_account_id=body.bank_account_id,
        data_esecuzione_richiesta=body.data_esecuzione_richiesta,
        priorita=body.priorita,
        note=body.note,
    )
    if not order:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nessuna scadenza valida trovata (tipo=passiva, stato=aperta/parzialmente_pagata)",
        )
    return _build_order_response(order)


# --- Templates ---

@router.get("/templates", response_model=list[PaymentTemplateResponse])
def list_templates(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    tipo: str | None = Query(None),
):
    company, _uc = company_data
    return [PaymentTemplateResponse.model_validate(t) for t in
            payment_template_service.list_templates(db, company.id, tipo)]


@router.post("/templates", response_model=PaymentTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    body: PaymentTemplateCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    t = payment_template_service.create_template(db, company.id, data)
    return PaymentTemplateResponse.model_validate(t)


@router.post("/templates/{template_id}/apply", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
def apply_template(
    template_id: uuid.UUID,
    body: PaymentTemplateApplyRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    order = payment_template_service.apply_template(
        db, template_id, company.id, current_user.id,
        data_esecuzione_richiesta=body.data_esecuzione_richiesta,
        override_bank_account_id=body.override_bank_account_id,
        override_priorita=body.override_priorita,
        override_note=body.override_note,
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template non trovato")
    return _build_order_response(order)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    if not payment_template_service.delete_template(db, template_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template non trovato")


# --- CRUD ---

@router.get("", response_model=PaymentOrderListResponse)
def list_payment_orders(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    stato: str | None = Query(None),
    tipo: str | None = Query(None),
    bank_account_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    importo_min: Decimal | None = Query(None),
    importo_max: Decimal | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc"),
):
    company, _uc = company_data
    items, total, summary = payment_order_service.list_payment_orders(
        db, company.id,
        stato=stato, tipo=tipo,
        bank_account_id=bank_account_id,
        date_from=date_from, date_to=date_to,
        search=search,
        importo_min=importo_min, importo_max=importo_max,
        page=page, page_size=page_size,
        sort_by=sort_by, sort_order=sort_order,
    )
    return PaymentOrderListResponse(
        items=[_build_order_response(o) for o in items],
        total=total,
        page=page,
        page_size=page_size,
        summary=PaymentOrderSummaryResponse(**summary),
    )


@router.post("", response_model=PaymentOrderResponse, status_code=status.HTTP_201_CREATED)
def create_payment_order(
    body: PaymentOrderCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    o = payment_order_service.create_payment_order(db, company.id, current_user.id, data)
    return _build_order_response(o)


@router.get("/{order_id}", response_model=PaymentOrderResponse)
def get_payment_order(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.get_payment_order(db, order_id, company.id)
    if not o:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ordine di pagamento non trovato")
    return _build_order_response(o)


@router.put("/{order_id}", response_model=PaymentOrderResponse)
def update_payment_order(
    order_id: uuid.UUID,
    body: PaymentOrderUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_unset=True)
    o = payment_order_service.update_payment_order(db, order_id, company.id, data)
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ordine non trovato o non modificabile (solo bozze)",
        )
    return _build_order_response(o)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_payment_order(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    if not payment_order_service.delete_payment_order(db, order_id, company.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ordine non trovato o non eliminabile (solo bozze)",
        )


# --- Lines ---

@router.post("/{order_id}/lines", response_model=PaymentOrderLineResponse, status_code=status.HTTP_201_CREATED)
def add_line(
    order_id: uuid.UUID,
    body: PaymentOrderLineCreateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_none=True)
    line = payment_order_service.add_line(db, order_id, company.id, data)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ordine non trovato o non modificabile (solo bozze)",
        )
    return PaymentOrderLineResponse.model_validate(line)


@router.put("/{order_id}/lines/{line_id}", response_model=PaymentOrderLineResponse)
def update_line(
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    body: PaymentOrderLineUpdateRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_unset=True)
    line = payment_order_service.update_line(db, order_id, line_id, company.id, data)
    if not line:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Riga non trovata o ordine non modificabile",
        )
    return PaymentOrderLineResponse.model_validate(line)


@router.delete("/{order_id}/lines/{line_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_line(
    order_id: uuid.UUID,
    line_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    if not payment_order_service.delete_line(db, order_id, line_id, company.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Riga non trovata o ordine non modificabile",
        )


# --- Workflow ---

@router.post("/{order_id}/submit", response_model=PaymentOrderResponse)
def submit_order(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.submit_order(db, order_id, company.id)
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile inviare: ordine non trovato, non in bozza, o senza righe",
        )
    return _build_order_response(o)


@router.post("/{order_id}/approve", response_model=PaymentOrderResponse)
def approve_order(
    order_id: uuid.UUID,
    body: PaymentApprovalRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.approve_order(
        db, order_id, company.id, current_user.id, body.commento,
    )
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile approvare: ordine non trovato, stato non valido, o stesso utente creatore",
        )
    return _build_order_response(o)


@router.post("/{order_id}/reject", response_model=PaymentOrderResponse)
def reject_order(
    order_id: uuid.UUID,
    body: PaymentRejectRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.reject_order(
        db, order_id, company.id, current_user.id, body.commento,
    )
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile rifiutare: ordine non trovato o stato non valido",
        )
    return _build_order_response(o)


@router.get("/{order_id}/approvals", response_model=list[PaymentApprovalResponse])
def get_approvals(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    approvals = payment_order_service.get_approvals(db, order_id, company.id)
    return [_build_approval_response(a) for a in approvals]


# --- File & execution ---

@router.post("/{order_id}/generate-file", response_model=PaymentOrderResponse)
def generate_file(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.generate_file(db, order_id, company.id)
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile generare file: ordine non trovato o stato non valido",
        )
    return _build_order_response(o)


@router.get("/{order_id}/download-file")
def download_file(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    result = payment_order_service.get_file_path(db, order_id, company.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File non trovato")
    file_path, filename = result
    media_type = "application/xml" if filename.endswith(".xml") else "text/plain"
    return FileResponse(file_path, media_type=media_type, filename=filename)


@router.post("/{order_id}/mark-sent", response_model=PaymentOrderResponse)
def mark_sent(
    order_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.mark_sent(db, order_id, company.id)
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile segnare come inviato: ordine non trovato o stato non valido",
        )
    return _build_order_response(o)


@router.post("/{order_id}/mark-executed", response_model=PaymentOrderResponse)
def mark_executed(
    order_id: uuid.UUID,
    body: MarkExecutedRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    o = payment_order_service.mark_executed(db, order_id, company.id, body.data_esecuzione)
    if not o:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossibile segnare come eseguito: ordine non trovato o stato non valido",
        )
    return _build_order_response(o)
