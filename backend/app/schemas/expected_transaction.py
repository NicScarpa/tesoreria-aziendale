import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class ExpectedTransactionResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    bank_account_id: uuid.UUID | None = None
    counterpart_name: str | None = None
    counterpart_iban: str | None = None
    type: str
    expected_amount: Decimal
    currency: str
    due_date: date
    description: str | None = None
    reference_number: str | None = None
    document_type: str
    status: str
    matched_amount: Decimal
    schedule_id: uuid.UUID | None = None
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ExpectedTransactionListResponse(BaseModel):
    items: list[ExpectedTransactionResponse]
    total: int
    page: int
    page_size: int
    total_expected_amount: Decimal = Decimal("0")
    total_matched_amount: Decimal = Decimal("0")


class CreateExpectedTransactionRequest(BaseModel):
    bank_account_id: uuid.UUID | None = None
    counterpart_name: str | None = None
    counterpart_iban: str | None = None
    type: str
    expected_amount: Decimal = Field(gt=0)
    currency: str = "EUR"
    due_date: date
    description: str | None = None
    reference_number: str | None = None
    document_type: str = "other"
    source: str = "manual"


class UpdateExpectedTransactionRequest(BaseModel):
    bank_account_id: uuid.UUID | None = None
    counterpart_name: str | None = None
    counterpart_iban: str | None = None
    type: str | None = None
    expected_amount: Decimal | None = Field(None, gt=0)
    currency: str | None = None
    due_date: date | None = None
    description: str | None = None
    reference_number: str | None = None
    document_type: str | None = None
