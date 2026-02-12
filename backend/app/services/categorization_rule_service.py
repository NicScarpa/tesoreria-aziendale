import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.categorization_rule import CategorizationRule
from app.models.transaction import Transaction
from app.models.enums import FlowDirection, CategorizationSource
from app.schemas.categorization_rule import (
    CreateCategorizationRuleRequest, UpdateCategorizationRuleRequest,
)


def list_rules(
    db: Session,
    company_id: uuid.UUID,
    direction: str | None = None,
    is_active: bool | None = None,
) -> list[CategorizationRule]:
    q = db.query(CategorizationRule).filter(CategorizationRule.company_id == company_id)
    if direction:
        q = q.filter(CategorizationRule.direction == direction)
    if is_active is not None:
        q = q.filter(CategorizationRule.is_active == is_active)
    return q.order_by(CategorizationRule.priority.desc(), CategorizationRule.created_at).all()


def get_rule(db: Session, rule_id: uuid.UUID, company_id: uuid.UUID) -> CategorizationRule:
    rule = (
        db.query(CategorizationRule)
        .filter(CategorizationRule.id == rule_id, CategorizationRule.company_id == company_id)
        .first()
    )
    if not rule:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regola non trovata")
    return rule


def create_rule(db: Session, company_id: uuid.UUID, data: CreateCategorizationRuleRequest) -> CategorizationRule:
    rule = CategorizationRule(
        company_id=company_id,
        name=data.name,
        direction=FlowDirection(data.direction),
        category_id=data.category_id,
        subcategory_id=data.subcategory_id,
        conditions=[c.model_dump() for c in data.conditions],
        priority=data.priority,
        is_active=data.is_active,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_rule(
    db: Session, rule_id: uuid.UUID, company_id: uuid.UUID, data: UpdateCategorizationRuleRequest
) -> CategorizationRule:
    rule = get_rule(db, rule_id, company_id)
    update_data = data.model_dump(exclude_unset=True)

    if "conditions" in update_data:
        update_data["conditions"] = [c.model_dump() if hasattr(c, "model_dump") else c for c in data.conditions]

    if "direction" in update_data:
        update_data["direction"] = FlowDirection(update_data["direction"])

    for key, value in update_data.items():
        setattr(rule, key, value)

    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, rule_id: uuid.UUID, company_id: uuid.UUID) -> None:
    rule = get_rule(db, rule_id, company_id)
    db.delete(rule)
    db.commit()


def test_rule(db: Session, rule_id: uuid.UUID, company_id: uuid.UUID) -> dict:
    rule = get_rule(db, rule_id, company_id)

    q = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.direction == rule.direction,
        Transaction.hidden_at.is_(None),
    )

    # Apply conditions to filter
    all_txs = q.all()
    matching = [tx for tx in all_txs if _matches_conditions(tx, rule.conditions)]

    sample = []
    for tx in matching[:5]:
        sample.append({
            "id": str(tx.id),
            "description": tx.description,
            "amount": float(tx.amount),
            "transaction_date": tx.transaction_date.isoformat(),
        })

    return {"matching_count": len(matching), "sample_transactions": sample}


def apply_rules(db: Session, transaction: Transaction) -> bool:
    """Apply categorization rules to a single transaction. Returns True if categorized."""
    rules = (
        db.query(CategorizationRule)
        .filter(
            CategorizationRule.company_id == transaction.company_id,
            CategorizationRule.direction == transaction.direction,
            CategorizationRule.is_active == True,  # noqa: E712
        )
        .order_by(CategorizationRule.priority.desc())
        .all()
    )

    for rule in rules:
        if _matches_conditions(transaction, rule.conditions):
            transaction.category_id = rule.category_id
            transaction.subcategory_id = rule.subcategory_id
            transaction.categorization_source = CategorizationSource.RULE
            return True

    return False


def apply_rules_bulk(db: Session, company_id: uuid.UUID, direction: str | None = None) -> int:
    """Re-categorize uncategorized transactions. Returns count of categorized."""
    q = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.category_id.is_(None),
        Transaction.hidden_at.is_(None),
    )
    if direction:
        q = q.filter(Transaction.direction == direction)

    transactions = q.all()
    count = 0
    for tx in transactions:
        if apply_rules(db, tx):
            count += 1

    if count > 0:
        db.commit()

    return count


def _matches_conditions(transaction: Transaction, conditions: list[dict]) -> bool:
    """Check if a transaction matches ALL conditions (AND logic)."""
    for condition in conditions:
        cond_type = condition.get("type", "").upper()
        value = condition.get("value")

        if cond_type == "KEYWORDS":
            keywords = value if isinstance(value, list) else [value]
            text = " ".join(filter(None, [
                transaction.description,
                transaction.remittance_info,
                transaction.notes,
            ])).lower()
            if not all(kw.lower() in text for kw in keywords):
                return False

        elif cond_type == "ACCOUNT":
            if str(transaction.bank_account_id) != str(value):
                return False

        elif cond_type == "TRANSACTION_TYPE":
            types = value if isinstance(value, list) else [value]
            if transaction.transaction_type.value not in types:
                return False

    return True
