import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.expected_transaction import (
    CreateExpectedTransactionRequest,
    ExpectedTransactionListResponse,
    ExpectedTransactionResponse,
    UpdateExpectedTransactionRequest,
)
from app.services import expected_transaction_service

router = APIRouter(prefix="/expected-transactions", tags=["expected-transactions"])


@router.get("", response_model=ExpectedTransactionListResponse)
def list_expected_transactions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    status_filter: str | None = Query(None, alias="status"),
    type_filter: str | None = Query(None, alias="type"),
    counterpart: str | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    search: str | None = Query(None),
    amount_min: Decimal | None = Query(None),
    amount_max: Decimal | None = Query(None),
    document_type: str | None = Query(None),
    bank_account_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    company, _uc = company_data
    items, total, total_expected, total_matched = expected_transaction_service.list_expected_transactions(
        db, company.id,
        status=status_filter,
        type_=type_filter,
        counterpart=counterpart,
        date_from=date_from,
        date_to=date_to,
        search=search,
        amount_min=amount_min,
        amount_max=amount_max,
        document_type=document_type,
        bank_account_id=bank_account_id,
        page=page,
        page_size=page_size,
    )
    return ExpectedTransactionListResponse(
        items=[ExpectedTransactionResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_expected_amount=total_expected,
        total_matched_amount=total_matched,
    )


@router.get("/{et_id}", response_model=ExpectedTransactionResponse)
def get_expected_transaction(
    et_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    et = expected_transaction_service.get_expected_transaction(db, et_id, company.id)
    if not et:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transazione attesa non trovata")
    return ExpectedTransactionResponse.model_validate(et)


@router.post("", response_model=ExpectedTransactionResponse, status_code=status.HTTP_201_CREATED)
def create_expected_transaction(
    body: CreateExpectedTransactionRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    et = expected_transaction_service.create_expected_transaction(
        db, company.id, body.model_dump()
    )
    return ExpectedTransactionResponse.model_validate(et)


@router.patch("/{et_id}", response_model=ExpectedTransactionResponse)
def update_expected_transaction(
    et_id: uuid.UUID,
    body: UpdateExpectedTransactionRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_unset=True)
    et = expected_transaction_service.update_expected_transaction(db, et_id, company.id, data)
    if not et:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Transazione attesa non trovata o non modificabile")
    return ExpectedTransactionResponse.model_validate(et)


@router.delete("/{et_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_expected_transaction(
    et_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    if not expected_transaction_service.delete_expected_transaction(db, et_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Transazione attesa non trovata o non eliminabile")
