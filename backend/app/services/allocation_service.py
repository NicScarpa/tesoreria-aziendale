import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.models.transaction_allocation import TransactionAllocation
from app.models.enums import CategorizationSource
from app.schemas.allocation import CreateAllocationsRequest


def _get_transaction(db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID) -> Transaction:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id, Transaction.company_id == company_id)
        .first()
    )
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimento non trovato")
    return tx


def create_allocations(
    db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID, data: CreateAllocationsRequest
) -> list[TransactionAllocation]:
    tx = _get_transaction(db, transaction_id, company_id)

    # Validate sum of allocations equals abs(amount)
    total = sum(a.amount for a in data.allocations)
    if total != abs(tx.amount):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"La somma delle allocazioni ({total}) deve essere uguale all'importo assoluto ({abs(tx.amount)})",
        )

    # Remove existing allocations
    db.query(TransactionAllocation).filter(TransactionAllocation.transaction_id == transaction_id).delete()

    # Create new allocations
    allocations = []
    for alloc_input in data.allocations:
        alloc = TransactionAllocation(
            transaction_id=transaction_id,
            category_id=alloc_input.category_id,
            subcategory_id=alloc_input.subcategory_id,
            amount=alloc_input.amount,
            currency=tx.currency,
            percentage=alloc_input.percentage,
        )
        db.add(alloc)
        allocations.append(alloc)

    # Clear category from transaction (split takes priority)
    tx.category_id = None
    tx.subcategory_id = None
    tx.categorization_source = CategorizationSource.MANUAL

    db.commit()
    for alloc in allocations:
        db.refresh(alloc)
    return allocations


def replace_allocations(
    db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID, data: CreateAllocationsRequest
) -> list[TransactionAllocation]:
    return create_allocations(db, transaction_id, company_id, data)


def delete_allocations(db: Session, transaction_id: uuid.UUID, company_id: uuid.UUID) -> None:
    tx = _get_transaction(db, transaction_id, company_id)
    db.query(TransactionAllocation).filter(TransactionAllocation.transaction_id == transaction_id).delete()
    db.commit()
