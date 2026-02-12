import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ReconciliationLineResponse(BaseModel):
    id: uuid.UUID
    reconciliation_id: uuid.UUID
    transaction_id: uuid.UUID | None = None
    expected_transaction_id: uuid.UUID | None = None
    matched_amount: Decimal
    line_type: str
    notes: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ReconciliationResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    type: str
    status: str
    reconciliation_date: datetime
    confirmed_by_user_id: uuid.UUID | None = None
    confirmed_at: datetime | None = None
    notes: str | None = None
    matching_score: Decimal | None = None
    applied_rule: str | None = None
    lines: list[ReconciliationLineResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReconciliationListResponse(BaseModel):
    items: list[ReconciliationResponse]
    total: int
    page: int
    page_size: int


class CreateReconciliationRequest(BaseModel):
    transaction_ids: list[uuid.UUID]
    expected_transaction_ids: list[uuid.UUID]
    notes: str | None = None


class AutoMatchRequest(BaseModel):
    bank_account_id: uuid.UUID | None = None
    date_from: date | None = None
    date_to: date | None = None
    dry_run: bool = False


class AutoMatchResult(BaseModel):
    total_matches: int
    confirmed: int
    suggested: int
    matches: list[ReconciliationResponse] = []


class BulkActionRequest(BaseModel):
    reconciliation_ids: list[uuid.UUID]


class MatchSuggestion(BaseModel):
    transaction_id: uuid.UUID | None = None
    expected_transaction_id: uuid.UUID | None = None
    score: Decimal
    match_type: str
    matched_amount: Decimal


class FindMatchesResponse(BaseModel):
    matches: list[MatchSuggestion]


class DashboardResponse(BaseModel):
    unreconciled_transactions: int
    open_expected: int
    pending_suggestions: int
    reconciliation_rate: Decimal
    expired_expected: int
    total_unreconciled_amount: Decimal
    total_open_expected_amount: Decimal
