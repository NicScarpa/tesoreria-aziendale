import uuid
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import BankAccountBalance
from app.schemas.bank_account import (
    CreateBalanceEntryRequest,
    BalanceChartPointResponse,
)


def list_balances(
    db: Session,
    account_id: uuid.UUID,
    company_id: uuid.UUID,
    date_from: date | None = None,
    date_to: date | None = None,
    limit: int = 100,
) -> list[BankAccountBalance]:
    q = db.query(BankAccountBalance).filter(
        BankAccountBalance.bank_account_id == account_id,
        BankAccountBalance.company_id == company_id,
    )
    if date_from:
        q = q.filter(BankAccountBalance.balance_date >= date_from)
    if date_to:
        q = q.filter(BankAccountBalance.balance_date <= date_to)
    return q.order_by(BankAccountBalance.balance_date.desc()).limit(limit).all()


def create_balance(
    db: Session,
    account_id: uuid.UUID,
    company_id: uuid.UUID,
    data: CreateBalanceEntryRequest,
) -> BankAccountBalance:
    # Check for duplicate date
    existing = (
        db.query(BankAccountBalance)
        .filter(
            BankAccountBalance.bank_account_id == account_id,
            BankAccountBalance.balance_date == data.balance_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Esiste già un saldo per la data {data.balance_date}",
        )

    entry = BankAccountBalance(
        bank_account_id=account_id,
        company_id=company_id,
        balance_date=data.balance_date,
        current_balance=data.current_balance,
        available_balance=data.available_balance,
        source=data.source,
        notes=data.notes,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_balance_chart(
    db: Session,
    account_id: uuid.UUID,
    company_id: uuid.UUID,
    date_from: date,
    date_to: date,
) -> list[BalanceChartPointResponse]:
    entries = (
        db.query(BankAccountBalance)
        .filter(
            BankAccountBalance.bank_account_id == account_id,
            BankAccountBalance.company_id == company_id,
            BankAccountBalance.balance_date >= date_from,
            BankAccountBalance.balance_date <= date_to,
        )
        .order_by(BankAccountBalance.balance_date.asc())
        .all()
    )
    return [
        BalanceChartPointResponse(
            date=e.balance_date,
            current_balance=e.current_balance,
            available_balance=e.available_balance,
        )
        for e in entries
    ]
