import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expected_transaction import ExpectedTransaction
from app.models.reconciliation import Reconciliation
from app.models.reconciliation_rule import ReconciliationRule
from app.models.transaction import Transaction
from app.models.enums import (
    ReconciliationStatus, ExpectedTransactionStatus,
)


# --- Rule CRUD (unchanged from before) ---

def list_rules(db: Session, company_id: uuid.UUID) -> list[ReconciliationRule]:
    return (
        db.query(ReconciliationRule)
        .filter(ReconciliationRule.company_id == company_id)
        .order_by(ReconciliationRule.priority.desc(), ReconciliationRule.created_at)
        .all()
    )


def create_rule(db: Session, company_id: uuid.UUID, data: dict) -> ReconciliationRule:
    rule = ReconciliationRule(company_id=company_id, **data)
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(db: Session, rule_id: uuid.UUID, company_id: uuid.UUID, data: dict) -> ReconciliationRule | None:
    rule = (
        db.query(ReconciliationRule)
        .filter(ReconciliationRule.id == rule_id, ReconciliationRule.company_id == company_id)
        .first()
    )
    if not rule:
        return None
    for key, value in data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: uuid.UUID, company_id: uuid.UUID) -> bool:
    rule = (
        db.query(ReconciliationRule)
        .filter(ReconciliationRule.id == rule_id, ReconciliationRule.company_id == company_id)
        .first()
    )
    if not rule:
        return False
    db.delete(rule)
    db.commit()
    return True


def reorder_rules(db: Session, company_id: uuid.UUID, rule_ids: list[uuid.UUID]) -> list[ReconciliationRule]:
    """Reorder rules by setting priority based on position."""
    rules = (
        db.query(ReconciliationRule)
        .filter(ReconciliationRule.company_id == company_id)
        .all()
    )
    rule_map = {r.id: r for r in rules}
    for i, rid in enumerate(reversed(rule_ids)):
        if rid in rule_map:
            rule_map[rid].priority = i
    db.commit()
    return list_rules(db, company_id)


def test_rule(
    db: Session,
    rule_id: uuid.UUID,
    company_id: uuid.UUID,
) -> dict:
    """Test a rule and return how many unreconciled transactions would match."""
    from app.services.reconciliation_matching_engine import find_matches_for_expected

    rule = (
        db.query(ReconciliationRule)
        .filter(ReconciliationRule.id == rule_id, ReconciliationRule.company_id == company_id)
        .first()
    )
    if not rule:
        return {"matching_count": 0, "sample_matches": []}

    tolerance = rule.amount_tolerance_override or rule.amount_tolerance
    date_tol = rule.date_tolerance_override or rule.date_tolerance_days

    open_expected = (
        db.query(ExpectedTransaction)
        .filter(
            ExpectedTransaction.company_id == company_id,
            ExpectedTransaction.status.in_([
                ExpectedTransactionStatus.OPEN,
                ExpectedTransactionStatus.PARTIALLY_MATCHED,
            ]),
        )
        .all()
    )

    total_matches = 0
    samples = []
    for et in open_expected:
        matches = find_matches_for_expected(db, et, company_id, tolerance, date_tol)
        filtered = [m for m in matches if m["score"] >= rule.min_confidence * 100]
        total_matches += len(filtered)
        if filtered and len(samples) < 5:
            samples.append({
                "expected_id": str(et.id),
                "expected_description": et.description,
                "match_count": len(filtered),
                "best_score": float(filtered[0]["score"]),
            })

    return {"matching_count": total_matches, "sample_matches": samples}


# --- Reconciliation listing ---

def list_reconciliations(
    db: Session,
    company_id: uuid.UUID,
    *,
    status: str | None = None,
    type_: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    bank_account_id: uuid.UUID | None = None,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[Reconciliation], int]:
    q = db.query(Reconciliation).filter(Reconciliation.company_id == company_id)

    if status:
        q = q.filter(Reconciliation.status == status)
    if type_:
        q = q.filter(Reconciliation.type == type_)
    if date_from:
        q = q.filter(func.date(Reconciliation.reconciliation_date) >= date_from)
    if date_to:
        q = q.filter(func.date(Reconciliation.reconciliation_date) <= date_to)

    total = q.count()
    items = (
        q.order_by(Reconciliation.reconciliation_date.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_reconciliation(
    db: Session, rec_id: uuid.UUID, company_id: uuid.UUID
) -> Reconciliation | None:
    return (
        db.query(Reconciliation)
        .filter(Reconciliation.id == rec_id, Reconciliation.company_id == company_id)
        .first()
    )


def get_pending_suggestions(
    db: Session, company_id: uuid.UUID
) -> list[Reconciliation]:
    return (
        db.query(Reconciliation)
        .filter(
            Reconciliation.company_id == company_id,
            Reconciliation.status == "pending",
        )
        .order_by(Reconciliation.matching_score.desc().nullslast())
        .all()
    )


# --- Dashboard ---

def get_dashboard(db: Session, company_id: uuid.UUID) -> dict:
    unreconciled_count = (
        db.query(func.count(Transaction.id))
        .filter(
            Transaction.company_id == company_id,
            Transaction.reconciliation_status == ReconciliationStatus.UNRECONCILED,
        )
        .scalar()
    ) or 0

    unreconciled_amount = (
        db.query(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .filter(
            Transaction.company_id == company_id,
            Transaction.reconciliation_status == ReconciliationStatus.UNRECONCILED,
        )
        .scalar()
    ) or Decimal("0")

    total_tx = (
        db.query(func.count(Transaction.id))
        .filter(Transaction.company_id == company_id)
        .scalar()
    ) or 0

    open_expected = (
        db.query(func.count(ExpectedTransaction.id))
        .filter(
            ExpectedTransaction.company_id == company_id,
            ExpectedTransaction.status.in_([
                ExpectedTransactionStatus.OPEN,
                ExpectedTransactionStatus.PARTIALLY_MATCHED,
            ]),
        )
        .scalar()
    ) or 0

    open_expected_amount = (
        db.query(func.coalesce(func.sum(ExpectedTransaction.expected_amount - ExpectedTransaction.matched_amount), 0))
        .filter(
            ExpectedTransaction.company_id == company_id,
            ExpectedTransaction.status.in_([
                ExpectedTransactionStatus.OPEN,
                ExpectedTransactionStatus.PARTIALLY_MATCHED,
            ]),
        )
        .scalar()
    ) or Decimal("0")

    pending_suggestions = (
        db.query(func.count(Reconciliation.id))
        .filter(
            Reconciliation.company_id == company_id,
            Reconciliation.status == "pending",
        )
        .scalar()
    ) or 0

    expired = (
        db.query(func.count(ExpectedTransaction.id))
        .filter(
            ExpectedTransaction.company_id == company_id,
            ExpectedTransaction.status == ExpectedTransactionStatus.OPEN,
            ExpectedTransaction.due_date < func.current_date(),
        )
        .scalar()
    ) or 0

    reconciliation_rate = Decimal("0")
    if total_tx > 0:
        reconciled = total_tx - unreconciled_count
        reconciliation_rate = round(Decimal(str(reconciled)) / Decimal(str(total_tx)) * 100, 2)

    return {
        "unreconciled_transactions": unreconciled_count,
        "open_expected": open_expected,
        "pending_suggestions": pending_suggestions,
        "reconciliation_rate": reconciliation_rate,
        "expired_expected": expired,
        "total_unreconciled_amount": unreconciled_amount,
        "total_open_expected_amount": open_expected_amount,
    }
