import uuid
from datetime import date
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.transaction_allocation import TransactionAllocation
from app.models.enums import FlowDirection, CategorizationSource
from app.schemas.transaction import UpdateTransactionRequest
from app.services import categorization_rule_service


def list_transactions(
    db: Session,
    company_id: uuid.UUID,
    *,
    bank_account_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    amount_min: Decimal | None = None,
    amount_max: Decimal | None = None,
    direction: str | None = None,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    status_filter: str | None = None,
    uncategorized: bool | None = None,
    verified: bool | None = None,
    counterpart_name: str | None = None,
    page: int = 1,
    page_size: int = 50,
    sort_by: str = "transaction_date",
    sort_order: str = "desc",
) -> tuple[list[Transaction], int]:
    q = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.hidden_at.is_(None),
    )

    if bank_account_id:
        q = q.filter(Transaction.bank_account_id == bank_account_id)
    if date_from:
        q = q.filter(Transaction.transaction_date >= date_from)
    if date_to:
        q = q.filter(Transaction.transaction_date <= date_to)
    if amount_min is not None:
        q = q.filter(func.abs(Transaction.amount) >= amount_min)
    if amount_max is not None:
        q = q.filter(func.abs(Transaction.amount) <= amount_max)
    if direction:
        q = q.filter(Transaction.direction == direction)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if status_filter:
        q = q.filter(Transaction.status == status_filter)
    if uncategorized:
        q = q.filter(Transaction.category_id.is_(None))
    if verified is not None:
        q = q.filter(Transaction.verified == verified)
    if counterpart_name:
        q = q.filter(Transaction.counterpart_name.ilike(f"%{counterpart_name}%"))
    if search:
        q = q.filter(
            text(
                "to_tsvector('italian', COALESCE(transactions.description,'') || ' ' || "
                "COALESCE(transactions.remittance_info,'') || ' ' || "
                "COALESCE(transactions.notes,'')) @@ plainto_tsquery('italian', :search)"
            ).bindparams(search=search)
        )

    total = q.count()

    # Sort
    sort_col = getattr(Transaction, sort_by, Transaction.transaction_date)
    if sort_order == "asc":
        q = q.order_by(sort_col.asc())
    else:
        q = q.order_by(sort_col.desc())

    offset = (page - 1) * page_size
    items = q.offset(offset).limit(page_size).all()

    return items, total


def get_transaction(db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID) -> Transaction:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.company_id == company_id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimento non trovato")
    return tx


def get_metadata(
    db: Session,
    company_id: uuid.UUID,
    *,
    bank_account_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    direction: str | None = None,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    status_filter: str | None = None,
) -> dict:
    q = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.hidden_at.is_(None),
    )

    if bank_account_id:
        q = q.filter(Transaction.bank_account_id == bank_account_id)
    if date_from:
        q = q.filter(Transaction.transaction_date >= date_from)
    if date_to:
        q = q.filter(Transaction.transaction_date <= date_to)
    if direction:
        q = q.filter(Transaction.direction == direction)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if status_filter:
        q = q.filter(Transaction.status == status_filter)
    if search:
        q = q.filter(
            text(
                "to_tsvector('italian', COALESCE(transactions.description,'') || ' ' || "
                "COALESCE(transactions.remittance_info,'') || ' ' || "
                "COALESCE(transactions.notes,'')) @@ plainto_tsquery('italian', :search)"
            ).bindparams(search=search)
        )

    total = q.count()

    # Aggregate sums
    positive = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.id.in_(q.with_entities(Transaction.id)),
        Transaction.amount > 0,
    ).scalar()

    negative = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(
        Transaction.id.in_(q.with_entities(Transaction.id)),
        Transaction.amount < 0,
    ).scalar()

    uncategorized = q.filter(Transaction.category_id.is_(None)).count()

    return {
        "total": total,
        "totals": {"positive": positive, "negative": negative},
        "total_uncategorized": uncategorized,
    }


def update_transaction(
    db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID, data: UpdateTransactionRequest
) -> Transaction:
    tx = get_transaction(db, transaction_id, company_id)
    update_data = data.model_dump(exclude_unset=True)

    if "category_id" in update_data:
        update_data["categorization_source"] = CategorizationSource.MANUAL

    for key, value in update_data.items():
        setattr(tx, key, value)

    db.commit()
    db.refresh(tx)
    return tx


def delete_transaction(db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID) -> None:
    tx = get_transaction(db, transaction_id, company_id)
    db.delete(tx)
    db.commit()


def toggle_verified(db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID) -> Transaction:
    tx = get_transaction(db, transaction_id, company_id)
    tx.verified = not tx.verified
    db.commit()
    db.refresh(tx)
    return tx


def recategorize_transactions(
    db: Session, company_id: uuid.UUID, direction: str | None = None
) -> int:
    return categorization_rule_service.apply_rules_bulk(db, company_id, direction)
