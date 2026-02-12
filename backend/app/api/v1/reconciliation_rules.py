import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.reconciliation_rule import (
    CreateReconciliationRuleRequest,
    ReconciliationRuleResponse,
    UpdateReconciliationRuleRequest,
)
from app.services import reconciliation_service

router = APIRouter(prefix="/reconciliation-rules", tags=["reconciliation-rules"])


@router.get("", response_model=list[ReconciliationRuleResponse])
def list_rules(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return [
        ReconciliationRuleResponse.model_validate(r)
        for r in reconciliation_service.list_rules(db, company.id)
    ]


@router.post("", response_model=ReconciliationRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(
    body: CreateReconciliationRuleRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    rule = reconciliation_service.create_rule(db, company.id, body.model_dump())
    return ReconciliationRuleResponse.model_validate(rule)


@router.patch("/{rule_id}", response_model=ReconciliationRuleResponse)
def update_rule(
    rule_id: uuid.UUID,
    body: UpdateReconciliationRuleRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    data = body.model_dump(exclude_unset=True)
    rule = reconciliation_service.update_rule(db, rule_id, company.id, data)
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regola non trovata")
    return ReconciliationRuleResponse.model_validate(rule)


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_rule(
    rule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    if not reconciliation_service.delete_rule(db, rule_id, company.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regola non trovata")


@router.put("/reorder", response_model=list[ReconciliationRuleResponse])
def reorder_rules(
    body: dict,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    rule_ids = [uuid.UUID(rid) for rid in body.get("rule_ids", [])]
    rules = reconciliation_service.reorder_rules(db, company.id, rule_ids)
    return [ReconciliationRuleResponse.model_validate(r) for r in rules]


@router.post("/{rule_id}/test")
def test_rule(
    rule_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    return reconciliation_service.test_rule(db, rule_id, company.id)
