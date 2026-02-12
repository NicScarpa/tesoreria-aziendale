import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.deps import DB, CurrentUser, require_role
from app.models.enums import UserRole
from app.schemas.reconciliation import (
    AutoMatchRequest,
    AutoMatchResult,
    BulkActionRequest,
    CreateReconciliationRequest,
    DashboardResponse,
    FindMatchesResponse,
    MatchSuggestion,
    ReconciliationListResponse,
    ReconciliationResponse,
)
from app.services import reconciliation_service
from app.services import reconciliation_matching_engine as engine

router = APIRouter(prefix="/reconciliation", tags=["reconciliation"])


# --- Dashboard ---

@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    return reconciliation_service.get_dashboard(db, company.id)


# --- Auto-matching ---

@router.post("/auto-match", response_model=AutoMatchResult)
def auto_match(
    body: AutoMatchRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    result = engine.auto_match(
        db, company.id, current_user.id,
        bank_account_id=body.bank_account_id,
        date_from=body.date_from,
        date_to=body.date_to,
        dry_run=body.dry_run,
    )
    if body.dry_run:
        return AutoMatchResult(
            total_matches=result["total_matches"],
            confirmed=result["confirmed"],
            suggested=result["suggested"],
            matches=[],
        )
    return AutoMatchResult(
        total_matches=result["total_matches"],
        confirmed=result["confirmed"],
        suggested=result["suggested"],
        matches=[ReconciliationResponse.model_validate(r) for r in result["matches"]],
    )


# --- Suggestions ---

@router.get("/suggestions", response_model=list[ReconciliationResponse])
def get_suggestions(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    recs = reconciliation_service.get_pending_suggestions(db, company.id)
    return [ReconciliationResponse.model_validate(r) for r in recs]


@router.post("/suggestions/bulk-confirm", response_model=list[ReconciliationResponse])
def bulk_confirm(
    body: BulkActionRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    results = []
    for rid in body.reconciliation_ids:
        rec = engine.confirm_reconciliation(db, rid, company.id, current_user.id)
        if rec:
            results.append(ReconciliationResponse.model_validate(rec))
    return results


@router.post("/suggestions/bulk-reject", response_model=list[ReconciliationResponse])
def bulk_reject(
    body: BulkActionRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    results = []
    for rid in body.reconciliation_ids:
        rec = engine.reject_reconciliation(db, rid, company.id)
        if rec:
            results.append(ReconciliationResponse.model_validate(rec))
    return results


# --- Find matches ---

@router.get("/find-matches/{transaction_id}", response_model=FindMatchesResponse)
def find_matches_for_transaction(
    transaction_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    from app.models.transaction import Transaction
    company, _uc = company_data
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id, Transaction.company_id == company.id
    ).first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Movimento non trovato")
    matches = engine.find_matches_for_transaction(db, tx, company.id)
    return FindMatchesResponse(
        matches=[MatchSuggestion(**m) for m in matches]
    )


@router.get("/find-matches-for-expected/{expected_id}", response_model=FindMatchesResponse)
def find_matches_for_expected(
    expected_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    from app.models.expected_transaction import ExpectedTransaction
    company, _uc = company_data
    et = db.query(ExpectedTransaction).filter(
        ExpectedTransaction.id == expected_id, ExpectedTransaction.company_id == company.id
    ).first()
    if not et:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transazione attesa non trovata")
    matches = engine.find_matches_for_expected(db, et, company.id)
    return FindMatchesResponse(
        matches=[MatchSuggestion(**m) for m in matches]
    )


# --- CRUD Reconciliations ---

@router.get("", response_model=ReconciliationListResponse)
def list_reconciliations(
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
    status_filter: str | None = Query(None, alias="status"),
    type_filter: str | None = Query(None, alias="type"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    bank_account_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    company, _uc = company_data
    items, total = reconciliation_service.list_reconciliations(
        db, company.id,
        status=status_filter,
        type_=type_filter,
        date_from=date_from,
        date_to=date_to,
        bank_account_id=bank_account_id,
        page=page,
        page_size=page_size,
    )
    return ReconciliationListResponse(
        items=[ReconciliationResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{rec_id}", response_model=ReconciliationResponse)
def get_reconciliation(
    rec_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.VIEWER))],
    db: DB,
):
    company, _uc = company_data
    rec = reconciliation_service.get_reconciliation(db, rec_id, company.id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Riconciliazione non trovata")
    return ReconciliationResponse.model_validate(rec)


@router.post("", response_model=ReconciliationResponse, status_code=status.HTTP_201_CREATED)
def create_manual_reconciliation(
    body: CreateReconciliationRequest,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    try:
        rec = engine.create_manual_reconciliation(
            db, company.id, current_user.id,
            transaction_ids=body.transaction_ids,
            expected_transaction_ids=body.expected_transaction_ids,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return ReconciliationResponse.model_validate(rec)


@router.put("/{rec_id}/confirm", response_model=ReconciliationResponse)
def confirm_reconciliation(
    rec_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    rec = engine.confirm_reconciliation(db, rec_id, company.id, current_user.id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Riconciliazione non trovata o non confermabile")
    return ReconciliationResponse.model_validate(rec)


@router.put("/{rec_id}/reject", response_model=ReconciliationResponse)
def reject_reconciliation(
    rec_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.EDITOR))],
    db: DB,
):
    company, _uc = company_data
    rec = engine.reject_reconciliation(db, rec_id, company.id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Riconciliazione non trovata o non rifiutabile")
    return ReconciliationResponse.model_validate(rec)


@router.post("/{rec_id}/undo", response_model=ReconciliationResponse)
def undo_reconciliation(
    rec_id: uuid.UUID,
    current_user: CurrentUser,
    company_data: Annotated[tuple, Depends(require_role(UserRole.ADMIN))],
    db: DB,
):
    company, _uc = company_data
    rec = engine.undo_reconciliation(db, rec_id, company.id)
    if not rec:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Riconciliazione non trovata o non annullabile")
    return ReconciliationResponse.model_validate(rec)
