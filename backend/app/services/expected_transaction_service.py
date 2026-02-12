import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.expected_transaction import ExpectedTransaction
from app.models.enums import (
    ExpectedTransactionType, ExpectedDocumentType,
    ExpectedTransactionStatus, ExpectedTransactionSource,
)


def list_expected_transactions(
    db: Session,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
    type_: str | None = None,
    counterpart: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    search: str | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    document_type: str | None = None,
    bank_account_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[ExpectedTransaction], int, Decimal, Decimal]:
    q = db.query(ExpectedTransaction).filter(ExpectedTransaction.company_id == company_id)

    if status:
        q = q.filter(ExpectedTransaction.status == ExpectedTransactionStatus(status))
    if type_:
        q = q.filter(ExpectedTransaction.type == ExpectedTransactionType(type_))
    if counterpart:
        q = q.filter(
            or_(
                ExpectedTransaction.counterpart_name.ilike(f"%{counterpart}%"),
                ExpectedTransaction.counterpart_iban.ilike(f"%{counterpart}%"),
            )
        )
    if date_from:
        q = q.filter(ExpectedTransaction.due_date >= date_from)
    if date_to:
        q = q.filter(ExpectedTransaction.due_date <= date_to)
    if search:
        q = q.filter(
            or_(
                ExpectedTransaction.description.ilike(f"%{search}%"),
                ExpectedTransaction.reference_number.ilike(f"%{search}%"),
                ExpectedTransaction.counterpart_name.ilike(f"%{search}%"),
            )
        )
    if amount_min is not None:
        q = q.filter(ExpectedTransaction.expected_amount >= amount_min)
    if amount_max is not None:
        q = q.filter(ExpectedTransaction.expected_amount <= amount_max)
    if document_type:
        q = q.filter(ExpectedTransaction.document_type == ExpectedDocumentType(document_type))
    if bank_account_id:
        q = q.filter(ExpectedTransaction.bank_account_id == bank_account_id)

    total = q.count()

    # Totals
    totals_q = q.with_entities(
        func.coalesce(func.sum(ExpectedTransaction.expected_amount), 0),
        func.coalesce(func.sum(ExpectedTransaction.matched_amount), 0),
    ).first()
    total_expected = totals_q[0] if totals_q else Decimal("0")
    total_matched = totals_q[1] if totals_q else Decimal("0")

    items = (
        q.order_by(ExpectedTransaction.due_date.asc(), ExpectedTransaction.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total, total_expected, total_matched


def get_expected_transaction(
    db: Session, et_id: uuid.UUID, company_id: uuid.UUID
) -> ExpectedTransaction | None:
    return (
        db.query(ExpectedTransaction)
        .filter(ExpectedTransaction.id == et_id, ExpectedTransaction.company_id == company_id)
        .first()
    )


def create_expected_transaction(
    db: Session, company_id: uuid.UUID, data: dict
) -> ExpectedTransaction:
    # Convert string enum values
    if "type" in data and isinstance(data["type"], str):
        data["type"] = ExpectedTransactionType(data["type"])
    if "document_type" in data and isinstance(data["document_type"], str):
        data["document_type"] = ExpectedDocumentType(data["document_type"])
    if "source" in data and isinstance(data["source"], str):
        data["source"] = ExpectedTransactionSource(data["source"])

    et = ExpectedTransaction(company_id=company_id, **data)
    db.add(et)
    db.commit()
    db.refresh(et)
    return et


def update_expected_transaction(
    db: Session, et_id: uuid.UUID, company_id: uuid.UUID, data: dict
) -> ExpectedTransaction | None:
    et = get_expected_transaction(db, et_id, company_id)
    if not et:
        return None
    if et.status != ExpectedTransactionStatus.OPEN:
        return None

    if "type" in data and isinstance(data["type"], str):
        data["type"] = ExpectedTransactionType(data["type"])
    if "document_type" in data and isinstance(data["document_type"], str):
        data["document_type"] = ExpectedDocumentType(data["document_type"])

    for key, value in data.items():
        setattr(et, key, value)
    db.commit()
    db.refresh(et)
    return et


def delete_expected_transaction(
    db: Session, et_id: uuid.UUID, company_id: uuid.UUID
) -> bool:
    et = get_expected_transaction(db, et_id, company_id)
    if not et:
        return False
    if et.status != ExpectedTransactionStatus.OPEN:
        return False
    db.delete(et)
    db.commit()
    return True
