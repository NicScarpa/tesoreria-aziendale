import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.category import (
    CategoryResponse,
    SubcategoryResponse,
    CreateCategoryRequest,
    UpdateCategoryRequest,
    CreateSubcategoryRequest,
    UpdateSubcategoryRequest,
)
from app.services import category_service

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return category_service.list_categories(db, company.id)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    body: CreateCategoryRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return category_service.create_category(db, company.id, body)


@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: uuid.UUID,
    body: UpdateCategoryRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return category_service.update_category(db, category_id, company.id, body)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    category_service.delete_category(db, category_id, company.id)


# --- Subcategories ---

@router.post("/{category_id}/subcategories", response_model=SubcategoryResponse, status_code=status.HTTP_201_CREATED)
def create_subcategory(
    category_id: uuid.UUID,
    body: CreateSubcategoryRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return category_service.create_subcategory(db, category_id, company.id, body)


@router.patch("/subcategories/{subcategory_id}", response_model=SubcategoryResponse)
def update_subcategory(
    subcategory_id: uuid.UUID,
    body: UpdateSubcategoryRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return category_service.update_subcategory(db, subcategory_id, company.id, body)


@router.delete("/subcategories/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subcategory(
    subcategory_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
    mode: str = Query("mark_uncategorised"),
):
    company, _uc = company_data
    category_service.delete_subcategory(db, subcategory_id, company.id, mode)
