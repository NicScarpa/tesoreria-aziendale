import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.transaction import (
    TransactionResponse,
    TransactionListResponse,
    TransactionMetadataResponse,
    UpdateTransactionRequest,
    CSVMappingRequest,
)
from app.schemas.allocation import CreateAllocationsRequest
from app.services import (
    transaction_service,
    allocation_service,
    transaction_import_service,
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


def _build_tx_response(tx) -> dict:
    """Build a transaction response dict with bank_account_nickname."""
    data = TransactionResponse.model_validate(tx).model_dump()
    data["bank_account_nickname"] = tx.bank_account.nickname if tx.bank_account else None
    return data


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    bank_account_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    amount_min: Decimal | None = Query(None),
    amount_max: Decimal | None = Query(None),
    direction: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    uncategorized: bool | None = Query(None),
    verified: bool | None = Query(None),
    counterpart_name: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    sort_by: str = Query("transaction_date"),
    sort_order: str = Query("desc"),
):
    company, _uc = company_data
    items, total = transaction_service.list_transactions(
        db, company.id,
        bank_account_id=bank_account_id,
        date_from=date_from,
        date_to=date_to,
        amount_min=amount_min,
        amount_max=amount_max,
        direction=direction,
        category_id=category_id,
        search=search,
        status_filter=status_filter,
        uncategorized=uncategorized,
        verified=verified,
        counterpart_name=counterpart_name,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return {
        "items": [_build_tx_response(tx) for tx in items],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/metadata", response_model=TransactionMetadataResponse)
def get_metadata(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    bank_account_id: uuid.UUID | None = Query(None),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    direction: str | None = Query(None),
    category_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
):
    company, _uc = company_data
    return transaction_service.get_metadata(
        db, company.id,
        bank_account_id=bank_account_id,
        date_from=date_from,
        date_to=date_to,
        direction=direction,
        category_id=category_id,
        search=search,
        status_filter=status_filter,
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    tx = transaction_service.get_transaction(db, transaction_id, company.id)
    return _build_tx_response(tx)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: uuid.UUID,
    body: UpdateTransactionRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    tx = transaction_service.update_transaction(db, transaction_id, company.id, body)
    return _build_tx_response(tx)


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    transaction_service.delete_transaction(db, transaction_id, company.id)


@router.patch("/{transaction_id}/verify", response_model=TransactionResponse)
def toggle_verified(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    tx = transaction_service.toggle_verified(db, transaction_id, company.id)
    return _build_tx_response(tx)


# --- Allocations ---

@router.post("/{transaction_id}/allocations", status_code=status.HTTP_201_CREATED)
def create_allocations(
    transaction_id: uuid.UUID,
    body: CreateAllocationsRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return allocation_service.create_allocations(db, transaction_id, company.id, body)


@router.put("/{transaction_id}/allocations")
def replace_allocations(
    transaction_id: uuid.UUID,
    body: CreateAllocationsRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return allocation_service.replace_allocations(db, transaction_id, company.id, body)


@router.delete("/{transaction_id}/allocations", status_code=status.HTTP_204_NO_CONTENT)
def delete_allocations(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    allocation_service.delete_allocations(db, transaction_id, company.id)


# --- Bulk operations ---

@router.post("/recategorize")
def recategorize_transactions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
    direction: str | None = Query(None),
):
    company, _uc = company_data
    count = transaction_service.recategorize_transactions(db, company.id, direction)
    return {"categorized_count": count}


# --- Import ---

@router.post("/import")
async def import_csv(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
    file: UploadFile = File(...),
    bank_account_id: uuid.UUID = Form(...),
    date_column: str = Form(...),
    amount_column: str = Form(...),
    description_column: str | None = Form(None),
    date_format: str = Form("%d/%m/%Y"),
    decimal_separator: str = Form(","),
    csv_separator: str = Form(";"),
):
    company, _uc = company_data
    mapping = CSVMappingRequest(
        date_column=date_column,
        amount_column=amount_column,
        description_column=description_column,
        date_format=date_format,
        decimal_separator=decimal_separator,
        csv_separator=csv_separator,
    )
    batch = await transaction_import_service.import_csv(
        db, company.id, current_user.id, bank_account_id, file, mapping
    )
    return {
        "id": batch.id,
        "status": batch.status.value,
        "total_records": batch.total_records,
        "imported_records": batch.imported_records,
        "skipped_records": batch.skipped_records,
        "error_records": batch.error_records,
        "errors": batch.errors,
    }


@router.get("/import/{batch_id}")
def get_import_batch(
    batch_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    batch = transaction_import_service.get_batch(db, batch_id, company.id)
    return {
        "id": batch.id,
        "status": batch.status.value,
        "filename": batch.filename,
        "total_records": batch.total_records,
        "imported_records": batch.imported_records,
        "skipped_records": batch.skipped_records,
        "error_records": batch.error_records,
        "errors": batch.errors,
        "started_at": batch.started_at,
        "completed_at": batch.completed_at,
    }
