import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole, AccountStatus
from app.schemas.bank_account import (
    BankAccountResponse,
    BankAccountSummaryResponse,
    BankAccountBalanceResponse,
    BalanceChartPointResponse,
    BankAccountAccessResponse,
    CreateBankAccountRequest,
    UpdateBankAccountRequest,
    UpdateBalanceRequest,
    CreateBalanceEntryRequest,
    CreateBankAccountAccessRequest,
    UpdateBankAccountAccessRequest,
)
from app.services import bank_account_service, bank_account_balance_service, bank_account_access_service

router = APIRouter(prefix="/bank-accounts", tags=["bank-accounts"])


# --- Bank Accounts ---

@router.get("", response_model=list[BankAccountResponse])
def list_accounts(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    status_filter: AccountStatus | None = Query(None, alias="status"),
    include_hidden: bool = Query(False),
):
    company, _uc = company_data
    return bank_account_service.list_accounts(db, company.id, status_filter, include_hidden)


@router.get("/summary", response_model=BankAccountSummaryResponse)
def get_summary(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.get_summary(db, company.id)


@router.post("", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
def create_account(
    body: CreateBankAccountRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.create_account(db, company.id, body)


@router.get("/{account_id}", response_model=BankAccountResponse)
def get_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.get_account(db, account_id, company.id)


@router.patch("/{account_id}", response_model=BankAccountResponse)
def update_account(
    account_id: uuid.UUID,
    body: UpdateBankAccountRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.update_account(db, account_id, company.id, body)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    bank_account_service.delete_account(db, account_id, company.id)


@router.patch("/{account_id}/balance", response_model=BankAccountResponse)
def update_balance(
    account_id: uuid.UUID,
    body: UpdateBalanceRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.update_balance(db, account_id, company.id, body)


@router.post("/{account_id}/hide", response_model=BankAccountResponse)
def hide_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.hide_account(db, account_id, company.id)


@router.post("/{account_id}/unhide", response_model=BankAccountResponse)
def unhide_account(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_service.unhide_account(db, account_id, company.id)


# --- Balances ---

@router.get("/{account_id}/balances", response_model=list[BankAccountBalanceResponse])
def list_balances(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(100, le=500),
):
    company, _uc = company_data
    return bank_account_balance_service.list_balances(db, account_id, company.id, date_from, date_to, limit)


@router.post("/{account_id}/balances", response_model=BankAccountBalanceResponse, status_code=status.HTTP_201_CREATED)
def create_balance(
    account_id: uuid.UUID,
    body: CreateBalanceEntryRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_balance_service.create_balance(db, account_id, company.id, body)


@router.get("/{account_id}/balance-chart", response_model=list[BalanceChartPointResponse])
def get_balance_chart(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    date_from: date = Query(...),
    date_to: date = Query(...),
):
    company, _uc = company_data
    return bank_account_balance_service.get_balance_chart(db, account_id, company.id, date_from, date_to)


# --- Accesses ---

@router.get("/{account_id}/accesses", response_model=list[BankAccountAccessResponse])
def list_accesses(
    account_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_access_service.list_accesses(db, account_id, company.id)


@router.post("/{account_id}/accesses", response_model=BankAccountAccessResponse, status_code=status.HTTP_201_CREATED)
def create_access(
    account_id: uuid.UUID,
    body: CreateBankAccountAccessRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_access_service.create_access(db, account_id, company.id, body, current_user.id)


@router.patch("/{account_id}/accesses/{access_id}", response_model=BankAccountAccessResponse)
def update_access(
    account_id: uuid.UUID,
    access_id: uuid.UUID,
    body: UpdateBankAccountAccessRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    return bank_account_access_service.update_access(db, access_id, company.id, body)


@router.delete("/{account_id}/accesses/{access_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_access(
    account_id: uuid.UUID,
    access_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    bank_account_access_service.delete_access(db, access_id, company.id)
