import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import BankAccount, AccountStatus, BankAccountBalance, BalanceSource
from app.schemas.bank_account import (
    CreateBankAccountRequest,
    UpdateBankAccountRequest,
    UpdateBalanceRequest,
    BankAccountSummaryResponse,
)


def _extract_abi_cab(iban: str) -> tuple[str | None, str | None]:
    """Extract ABI and CAB from Italian IBAN."""
    cleaned = iban.replace(" ", "").upper()
    if cleaned[:2] == "IT" and len(cleaned) == 27:
        abi = cleaned[5:10]
        cab = cleaned[10:15]
        return abi, cab
    return None, None


def list_accounts(
    db: Session,
    company_id: uuid.UUID,
    status_filter: AccountStatus | None = None,
    include_hidden: bool = False,
) -> list[BankAccount]:
    q = db.query(BankAccount).filter(BankAccount.company_id == company_id)
    if status_filter:
        q = q.filter(BankAccount.status == status_filter)
    if not include_hidden:
        q = q.filter(BankAccount.hidden_at.is_(None))
    return q.order_by(BankAccount.is_default.desc(), BankAccount.nickname).all()


def get_account(db: Session, account_id: uuid.UUID, company_id: uuid.UUID) -> BankAccount:
    account = (
        db.query(BankAccount)
        .filter(BankAccount.id == account_id, BankAccount.company_id == company_id)
        .first()
    )
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conto non trovato")
    return account


def create_account(db: Session, company_id: uuid.UUID, data: CreateBankAccountRequest) -> BankAccount:
    bank_abi = None
    bank_cab = None
    if data.iban:
        bank_abi, bank_cab = _extract_abi_cab(data.iban)

    # If is_default, unset other defaults atomically
    if data.is_default:
        db.query(BankAccount).filter(
            BankAccount.company_id == company_id,
            BankAccount.is_default == True,  # noqa: E712
            BankAccount.status == AccountStatus.ACTIVE,
        ).update({"is_default": False})

    account = BankAccount(
        company_id=company_id,
        bank_connection_id=None,
        nickname=data.nickname,
        iban=data.iban,
        bic=data.bic,
        account_number=data.account_number,
        currency=data.currency,
        current_balance=data.current_balance,
        available_balance=data.available_balance,
        balance_date=datetime.now(timezone.utc) if data.current_balance is not None else None,
        credit_limit=data.credit_limit,
        status=AccountStatus.ACTIVE,
        account_type=data.account_type,
        color=data.color,
        notes=data.notes,
        is_default=data.is_default,
        bank_name=data.bank_name,
        bank_abi=bank_abi,
        bank_cab=bank_cab,
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


def update_account(
    db: Session, account_id: uuid.UUID, company_id: uuid.UUID, data: UpdateBankAccountRequest
) -> BankAccount:
    account = get_account(db, account_id, company_id)

    update_data = data.model_dump(exclude_unset=True)

    # If updating is_default to True, unset others
    if update_data.get("is_default") is True:
        db.query(BankAccount).filter(
            BankAccount.company_id == company_id,
            BankAccount.is_default == True,  # noqa: E712
            BankAccount.status == AccountStatus.ACTIVE,
            BankAccount.id != account_id,
        ).update({"is_default": False})

    # If updating IBAN, extract ABI/CAB
    if "iban" in update_data and update_data["iban"]:
        abi, cab = _extract_abi_cab(update_data["iban"])
        update_data["bank_abi"] = abi
        update_data["bank_cab"] = cab

    for key, value in update_data.items():
        setattr(account, key, value)

    db.commit()
    db.refresh(account)
    return account


def delete_account(db: Session, account_id: uuid.UUID, company_id: uuid.UUID) -> None:
    account = get_account(db, account_id, company_id)
    account.status = AccountStatus.CLOSED
    db.commit()


def update_balance(
    db: Session, account_id: uuid.UUID, company_id: uuid.UUID, data: UpdateBalanceRequest
) -> BankAccount:
    account = get_account(db, account_id, company_id)

    if not account.allow_balance_change:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Modifica saldo non consentita per questo conto",
        )

    now = datetime.now(timezone.utc)
    if data.current_balance is not None:
        account.current_balance = data.current_balance
    if data.available_balance is not None:
        account.available_balance = data.available_balance
    account.balance_date = now

    # Create balance history entry
    today = now.date()
    existing = (
        db.query(BankAccountBalance)
        .filter(
            BankAccountBalance.bank_account_id == account_id,
            BankAccountBalance.balance_date == today,
        )
        .first()
    )
    if existing:
        existing.current_balance = data.current_balance if data.current_balance is not None else existing.current_balance
        existing.available_balance = data.available_balance if data.available_balance is not None else existing.available_balance
        existing.notes = data.notes
    else:
        entry = BankAccountBalance(
            bank_account_id=account_id,
            company_id=company_id,
            balance_date=today,
            current_balance=data.current_balance or account.current_balance,
            available_balance=data.available_balance or account.available_balance,
            source=BalanceSource.MANUAL,
            notes=data.notes,
        )
        db.add(entry)

    db.commit()
    db.refresh(account)
    return account


def hide_account(db: Session, account_id: uuid.UUID, company_id: uuid.UUID) -> BankAccount:
    account = get_account(db, account_id, company_id)
    account.hidden_at = datetime.now(timezone.utc)
    account.status = AccountStatus.HIDDEN
    db.commit()
    db.refresh(account)
    return account


def unhide_account(db: Session, account_id: uuid.UUID, company_id: uuid.UUID) -> BankAccount:
    account = get_account(db, account_id, company_id)
    account.hidden_at = None
    account.status = AccountStatus.ACTIVE
    db.commit()
    db.refresh(account)
    return account


def get_summary(db: Session, company_id: uuid.UUID) -> BankAccountSummaryResponse:
    accounts = (
        db.query(BankAccount)
        .filter(
            BankAccount.company_id == company_id,
            BankAccount.status == AccountStatus.ACTIVE,
            BankAccount.ignore_balance == False,  # noqa: E712
            BankAccount.hidden_at.is_(None),
        )
        .all()
    )

    total_current = sum((a.current_balance or Decimal("0")) for a in accounts)
    total_available = sum((a.available_balance or Decimal("0")) for a in accounts)
    total_credit = sum((a.credit_limit or Decimal("0")) for a in accounts)

    return BankAccountSummaryResponse(
        count=len(accounts),
        total_current_balance=total_current,
        total_available_balance=total_available,
        difference=total_current - total_available,
        total_credit_limit=total_credit,
    )
