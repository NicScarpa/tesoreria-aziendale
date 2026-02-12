import uuid
from datetime import datetime
from pydantic import BaseModel, field_validator
import re


class SubcategoryResponse(BaseModel):
    id: uuid.UUID
    category_id: uuid.UUID
    company_id: uuid.UUID
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    name: str
    color: str
    sort_order: int
    is_system: bool
    subcategories: list[SubcategoryResponse] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CreateCategoryRequest(BaseModel):
    name: str
    color: str = "#6b7280"
    sort_order: int = 0

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome categoria obbligatorio")
        return v

    @field_validator("color")
    @classmethod
    def check_color(cls, v: str) -> str:
        if not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Colore deve essere in formato #RRGGBB")
        return v


class UpdateCategoryRequest(BaseModel):
    name: str | None = None
    color: str | None = None
    sort_order: int | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nome categoria obbligatorio")
        return v

    @field_validator("color")
    @classmethod
    def check_color(cls, v: str | None) -> str | None:
        if v is not None and not re.match(r"^#[0-9a-fA-F]{6}$", v):
            raise ValueError("Colore deve essere in formato #RRGGBB")
        return v


class CreateSubcategoryRequest(BaseModel):
    name: str

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Nome sottocategoria obbligatorio")
        return v


class UpdateSubcategoryRequest(BaseModel):
    name: str | None = None
    sort_order: int | None = None

    @field_validator("name")
    @classmethod
    def check_name(cls, v: str | None) -> str | None:
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Nome sottocategoria obbligatorio")
        return v
