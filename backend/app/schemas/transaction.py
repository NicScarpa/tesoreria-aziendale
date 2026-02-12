import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel

from app.schemas.category import CategoryResponse, SubcategoryResponse


class AllocationResponse(BaseModel):
    id: uuid.UUID
    transaction_id: uuid.UUID
    category_id: uuid.UUID
    subcategory_id: uuid.UUID | None = None
    amount: Decimal
    currency: str
    percentage: Decimal | None = None
    category: CategoryResponse | None = None
    subcategory: SubcategoryResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    bank_account_id: uuid.UUID
    amount: Decimal
    currency: str
    direction: str
    transaction_date: date
    value_date: date | None = None
    description: str | None = None
    remittance_info: str | None = None
    transaction_type: str
    category_id: uuid.UUID | None = None
    subcategory_id: uuid.UUID | None = None
    categorization_source: str | None = None
    counterpart_id: uuid.UUID | None = None
    counterpart_name: str | None = None
    counterpart_iban: str | None = None
    status: str
    verified: bool
    provider_transaction_id: str | None = None
    hidden_at: datetime | None = None
    notes: str | None = None
    reconciliation_status: str = "unreconciled"
    reconciliation_id: uuid.UUID | None = None
    import_batch_id: uuid.UUID | None = None
    category: CategoryResponse | None = None
    subcategory: SubcategoryResponse | None = None
    allocations: list[AllocationResponse] = []
    bank_account_nickname: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int


class TransactionTotals(BaseModel):
    positive: Decimal
    negative: Decimal


class TransactionMetadataResponse(BaseModel):
    total: int
    totals: TransactionTotals
    total_uncategorized: int


class UpdateTransactionRequest(BaseModel):
    category_id: uuid.UUID | None = None
    subcategory_id: uuid.UUID | None = None
    notes: str | None = None
    verified: bool | None = None
    counterpart_name: str | None = None


class CSVMappingRequest(BaseModel):
    date_column: str
    amount_column: str
    description_column: str | None = None
    date_format: str = "%d/%m/%Y"
    decimal_separator: str = ","
    csv_separator: str = ";"
