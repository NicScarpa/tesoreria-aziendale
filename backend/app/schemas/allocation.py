import uuid
from decimal import Decimal
from pydantic import BaseModel


class AllocationInput(BaseModel):
    category_id: uuid.UUID
    subcategory_id: uuid.UUID | None = None
    amount: Decimal
    percentage: Decimal | None = None


class CreateAllocationsRequest(BaseModel):
    allocations: list[AllocationInput]
