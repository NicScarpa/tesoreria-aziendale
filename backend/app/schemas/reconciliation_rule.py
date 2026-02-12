import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class ReconciliationRuleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    description: str | None = None
    match_amount: bool
    amount_tolerance: Decimal
    match_date: bool
    date_tolerance_days: int
    match_description: bool
    match_counterpart: bool
    auto_confirm: bool
    min_confidence: Decimal
    priority: int
    is_active: bool
    match_type: str = "exact_amount"
    action: str = "suggest"
    amount_tolerance_override: Decimal | None = None
    date_tolerance_override: int | None = None
    reference_pattern: str | None = None
    require_same_counterpart: bool = False
    times_applied: int = 0
    last_applied_at: datetime | None = None
    confirmation_rate: Decimal | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateReconciliationRuleRequest(BaseModel):
    name: str
    description: str | None = None
    match_amount: bool = True
    amount_tolerance: Decimal = Decimal("0.01")
    match_date: bool = True
    date_tolerance_days: int = 3
    match_description: bool = False
    match_counterpart: bool = True
    auto_confirm: bool = False
    min_confidence: Decimal = Decimal("0.80")
    priority: int = 0
    is_active: bool = True
    match_type: str = "exact_amount"
    action: str = "suggest"
    amount_tolerance_override: Decimal | None = None
    date_tolerance_override: int | None = None
    reference_pattern: str | None = None
    require_same_counterpart: bool = False


class UpdateReconciliationRuleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    match_amount: bool | None = None
    amount_tolerance: Decimal | None = None
    match_date: bool | None = None
    date_tolerance_days: int | None = None
    match_description: bool | None = None
    match_counterpart: bool | None = None
    auto_confirm: bool | None = None
    min_confidence: Decimal | None = None
    priority: int | None = None
    is_active: bool | None = None
    match_type: str | None = None
    action: str | None = None
    amount_tolerance_override: Decimal | None = None
    date_tolerance_override: int | None = None
    reference_pattern: str | None = None
    require_same_counterpart: bool | None = None


class TestRuleResult(BaseModel):
    matching_count: int
    sample_matches: list[dict] = []
