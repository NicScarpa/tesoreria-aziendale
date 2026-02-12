import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import BankAccountAccess, User
from app.schemas.bank_account import (
    CreateBankAccountAccessRequest,
    UpdateBankAccountAccessRequest,
    BankAccountAccessResponse,
)


def list_accesses(
    db: Session, account_id: uuid.UUID, company_id: uuid.UUID
) -> list[BankAccountAccessResponse]:
    accesses = (
        db.query(BankAccountAccess)
        .filter(
            BankAccountAccess.bank_account_id == account_id,
            BankAccountAccess.company_id == company_id,
        )
        .all()
    )
    results = []
    for a in accesses:
        user = db.query(User).filter(User.id == a.user_id).first()
        results.append(
            BankAccountAccessResponse(
                id=a.id,
                bank_account_id=a.bank_account_id,
                user_id=a.user_id,
                user_email=user.email if user else None,
                user_name=f"{user.first_name} {user.last_name}" if user else None,
                access_level=a.access_level,
                granted_by=a.granted_by,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
    return results


def create_access(
    db: Session,
    account_id: uuid.UUID,
    company_id: uuid.UUID,
    data: CreateBankAccountAccessRequest,
    granted_by: uuid.UUID,
) -> BankAccountAccess:
    # Check user exists
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utente non trovato")

    # Check for duplicate
    existing = (
        db.query(BankAccountAccess)
        .filter(
            BankAccountAccess.bank_account_id == account_id,
            BankAccountAccess.user_id == data.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="L'utente ha già accesso a questo conto",
        )

    access = BankAccountAccess(
        bank_account_id=account_id,
        company_id=company_id,
        user_id=data.user_id,
        access_level=data.access_level,
        granted_by=granted_by,
    )
    db.add(access)
    db.commit()
    db.refresh(access)
    return BankAccountAccessResponse(
        id=access.id,
        bank_account_id=access.bank_account_id,
        user_id=access.user_id,
        user_email=user.email,
        user_name=f"{user.first_name} {user.last_name}",
        access_level=access.access_level,
        granted_by=access.granted_by,
        created_at=access.created_at,
        updated_at=access.updated_at,
    )


def update_access(
    db: Session,
    access_id: uuid.UUID,
    company_id: uuid.UUID,
    data: UpdateBankAccountAccessRequest,
) -> BankAccountAccess:
    access = (
        db.query(BankAccountAccess)
        .filter(
            BankAccountAccess.id == access_id,
            BankAccountAccess.company_id == company_id,
        )
        .first()
    )
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesso non trovato")

    access.access_level = data.access_level
    db.commit()
    db.refresh(access)
    user = db.query(User).filter(User.id == access.user_id).first()
    return BankAccountAccessResponse(
        id=access.id,
        bank_account_id=access.bank_account_id,
        user_id=access.user_id,
        user_email=user.email if user else None,
        user_name=f"{user.first_name} {user.last_name}" if user else None,
        access_level=access.access_level,
        granted_by=access.granted_by,
        created_at=access.created_at,
        updated_at=access.updated_at,
    )


def delete_access(db: Session, access_id: uuid.UUID, company_id: uuid.UUID) -> None:
    access = (
        db.query(BankAccountAccess)
        .filter(
            BankAccountAccess.id == access_id,
            BankAccountAccess.company_id == company_id,
        )
        .first()
    )
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Accesso non trovato")

    db.delete(access)
    db.commit()
