import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.categorization_rule import (
    CategorizationRuleResponse,
    CreateCategorizationRuleRequest,
    UpdateCategorizationRuleRequest,
    TestRuleResponse,
)
from app.services import categorization_rule_service

router = APIRouter(prefix="/categorization-rules", tags=["categorization-rules"])


@router.get("", response_model=list[CategorizationRuleResponse])
def list_rules(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    direction: str | None = Query(None),
    is_active: bool | None = Query(None),
):
    company, _uc = company_data
    return categorization_rule_service.list_rules(db, company.id, direction, is_active)


@router.post("", response_model=CategorizationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: CreateCategorizationRuleRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return categorization_rule_service.create_rule(db, company.id, body)


@router.patch("/{rule_id}", response_model=CategorizationRuleResponse)
def update_rule(
    rule_id: uuid.UUID,
    body: UpdateCategorizationRuleRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return categorization_rule_service.update_rule(db, rule_id, company.id, body)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    categorization_rule_service.delete_rule(db, rule_id, company.id)


@router.post("/{rule_id}/test", response_model=TestRuleResponse)
def test_rule(
    rule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return categorization_rule_service.test_rule(db, rule_id, company.id)
