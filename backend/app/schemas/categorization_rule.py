import uuid
from datetime import datetime
from pydantic import BaseModel

from app.schemas.category import CategoryResponse, SubcategoryResponse


class ConditionSchema(BaseModel):
    type: str  # ACCOUNT, KEYWORDS, TRANSACTION_TYPE
    value: list[str] | str


class CategorizationRuleResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str | None = None
    direction: str
    action_type: str
    category_id: uuid.UUID
    subcategory_id: uuid.UUID | None = None
    conditions: list[ConditionSchema]
    priority: int
    is_active: bool
    category: CategoryResponse | None = None
    subcategory: SubcategoryResponse | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateCategorizationRuleRequest(BaseModel):
    name: str | None = None
    direction: str
    category_id: uuid.UUID
    subcategory_id: uuid.UUID | None = None
    conditions: list[ConditionSchema]
    priority: int = 0
    is_active: bool = True


class UpdateCategorizationRuleRequest(BaseModel):
    name: str | None = None
    direction: str | None = None
    category_id: uuid.UUID | None = None
    subcategory_id: uuid.UUID | None = None
    conditions: list[ConditionSchema] | None = None
    priority: int | None = None
    is_active: bool | None = None


class TestRuleResponse(BaseModel):
    matching_count: int
    sample_transactions: list[dict]
