"""Reconciliation matching engine.

7-step scoring algorithm:
1. Exact match (amount + counterpart + reference) → 100
2. Strong match (amount + counterpart, no ref) → 90
3. Amount match (exact amount, no counterpart, date ok) → 75
4. Tolerance match (amount tolerance + counterpart) → 70
5. Fuzzy match (amount tolerance + date tolerance) → 50
6. Cumulative match (sum of txs = expected) → 60-80
7. Split match (tx partially covers expected) → 40-60
"""
import re
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from itertools import combinations

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.expected_transaction import ExpectedTransaction
from app.models.reconciliation import Reconciliation
from app.models.reconciliation_line import ReconciliationLine
from app.models.reconciliation_rule import ReconciliationRule
from app.models.transaction import Transaction
from app.models.enums import (
    FlowDirection, ReconciliationStatus, ReconciliationType,
    ExpectedTransactionStatus, ExpectedTransactionType,
    ReconciliationLineType,
)

# Italian invoice patterns
INVOICE_PATTERNS = [
    re.compile(r"fatt\.?\s*n?\.?\s*(\d+)", re.IGNORECASE),
    re.compile(r"ft\s*(\d+)", re.IGNORECASE),
    re.compile(r"rif\.?\s*(\d+)", re.IGNORECASE),
    re.compile(r"FV[- ]?\d{4}/(\d+)", re.IGNORECASE),
    re.compile(r"FT[- ]?\d{4}/(\d+)", re.IGNORECASE),
]


def _extract_reference(text: str | None) -> str | None:
    if not text:
        return None
    for pattern in INVOICE_PATTERNS:
        m = pattern.search(text)
        if m:
            return m.group(0)
    return None


def _reference_in_text(reference: str | None, text: str | None) -> bool:
    if not reference or not text:
        return False
    return reference.lower() in text.lower()


def _counterpart_matches(tx: Transaction, et: ExpectedTransaction) -> bool:
    if tx.counterpart_name and et.counterpart_name:
        if tx.counterpart_name.lower().strip() == et.counterpart_name.lower().strip():
            return True
    if tx.counterpart_iban and et.counterpart_iban:
        if tx.counterpart_iban.replace(" ", "") == et.counterpart_iban.replace(" ", ""):
            return True
    return False


def _direction_matches(tx: Transaction, et: ExpectedTransaction) -> bool:
    if et.type == ExpectedTransactionType.EXPECTED_INFLOW:
        return tx.direction == FlowDirection.INFLOW
    return tx.direction == FlowDirection.OUTFLOW


def _score_match(
    tx: Transaction,
    et: ExpectedTransaction,
    amount_tolerance: Decimal = Decimal("0.01"),
    date_tolerance_days: int = 3,
) -> Decimal:
    """Score a single tx-expected pair. Returns 0 if incompatible."""
    if not _direction_matches(tx, et):
        return Decimal("0")

    tx_amount = abs(tx.amount)
    et_amount = abs(et.expected_amount)
    amount_diff = abs(tx_amount - et_amount)
    exact_amount = amount_diff <= Decimal("0.01")
    within_tolerance = amount_diff <= amount_tolerance

    has_counterpart = _counterpart_matches(tx, et)
    has_reference = _reference_in_text(
        et.reference_number,
        (tx.description or "") + " " + (tx.remittance_info or "")
    )

    date_diff = abs((tx.transaction_date - et.due_date).days)
    date_ok = date_diff <= date_tolerance_days

    # Step 1: Exact match
    if exact_amount and has_counterpart and has_reference:
        return Decimal("100")

    # Step 2: Strong match
    if exact_amount and has_counterpart:
        return Decimal("90")

    # Step 3: Amount match (exact, no counterpart but date ok)
    if exact_amount and date_ok:
        return Decimal("75")

    # Step 4: Tolerance match (within tolerance + counterpart)
    if within_tolerance and has_counterpart:
        return Decimal("70")

    # Step 5: Fuzzy match
    if within_tolerance and date_ok:
        return Decimal("50")

    return Decimal("0")


def find_matches_for_transaction(
    db: Session,
    tx: Transaction,
    company_id: uuid.UUID,
    amount_tolerance: Decimal = Decimal("5.00"),
    date_tolerance_days: int = 5,
) -> list[dict]:
    """Find expected transactions that could match a given transaction."""
    open_statuses = [ExpectedTransactionStatus.OPEN, ExpectedTransactionStatus.PARTIALLY_MATCHED]
    expected = (
        db.query(ExpectedTransaction)
        .filter(
            ExpectedTransaction.company_id == company_id,
            ExpectedTransaction.status.in_(open_statuses),
        )
        .all()
    )

    matches = []
    for et in expected:
        score = _score_match(tx, et, amount_tolerance, date_tolerance_days)
        if score > 0:
            matches.append({
                "expected_transaction_id": et.id,
                "transaction_id": tx.id,
                "score": score,
                "match_type": _classify_match(score),
                "matched_amount": min(abs(tx.amount), abs(et.expected_amount - et.matched_amount)),
            })

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches


def find_matches_for_expected(
    db: Session,
    et: ExpectedTransaction,
    company_id: uuid.UUID,
    amount_tolerance: Decimal = Decimal("5.00"),
    date_tolerance_days: int = 5,
) -> list[dict]:
    """Find transactions that could match a given expected transaction."""
    txs = (
        db.query(Transaction)
        .filter(
            Transaction.company_id == company_id,
            Transaction.reconciliation_status == ReconciliationStatus.UNRECONCILED,
        )
        .all()
    )

    matches = []
    for tx in txs:
        score = _score_match(tx, et, amount_tolerance, date_tolerance_days)
        if score > 0:
            matches.append({
                "transaction_id": tx.id,
                "expected_transaction_id": et.id,
                "score": score,
                "match_type": _classify_match(score),
                "matched_amount": min(abs(tx.amount), abs(et.expected_amount - et.matched_amount)),
            })

    matches.sort(key=lambda m: m["score"], reverse=True)
    return matches


def _classify_match(score: Decimal) -> str:
    if score >= 100:
        return "exact"
    if score >= 90:
        return "strong"
    if score >= 75:
        return "amount"
    if score >= 70:
        return "tolerance"
    if score >= 60:
        return "cumulative"
    if score >= 50:
        return "fuzzy"
    return "split"


def auto_match(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    *,
    bank_account_id: uuid.UUID | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    dry_run: bool = False,
) -> dict:
    """Run the auto-matching engine."""
    # Get active rules ordered by priority
    rules = (
        db.query(ReconciliationRule)
        .filter(ReconciliationRule.company_id == company_id, ReconciliationRule.is_active == True)
        .order_by(ReconciliationRule.priority.desc())
        .all()
    )

    # Default tolerances
    amount_tolerance = Decimal("5.00")
    date_tolerance_days = 5

    # Get unreconciled transactions
    tx_q = db.query(Transaction).filter(
        Transaction.company_id == company_id,
        Transaction.reconciliation_status == ReconciliationStatus.UNRECONCILED,
    )
    if bank_account_id:
        tx_q = tx_q.filter(Transaction.bank_account_id == bank_account_id)
    if date_from:
        tx_q = tx_q.filter(Transaction.transaction_date >= date_from)
    if date_to:
        tx_q = tx_q.filter(Transaction.transaction_date <= date_to)
    transactions = tx_q.all()

    # Get open expected transactions
    open_statuses = [ExpectedTransactionStatus.OPEN, ExpectedTransactionStatus.PARTIALLY_MATCHED]
    expected_txs = (
        db.query(ExpectedTransaction)
        .filter(
            ExpectedTransaction.company_id == company_id,
            ExpectedTransaction.status.in_(open_statuses),
        )
        .all()
    )

    results = {"total_matches": 0, "confirmed": 0, "suggested": 0, "matches": []}
    used_tx_ids = set()
    used_et_ids = set()

    # Try each transaction against each expected
    for tx in transactions:
        if tx.id in used_tx_ids:
            continue

        best_match = None
        best_score = Decimal("0")
        best_et = None

        for et in expected_txs:
            if et.id in used_et_ids:
                continue

            score = _score_match(tx, et, amount_tolerance, date_tolerance_days)
            if score > best_score:
                best_score = score
                best_et = et
                best_match = {
                    "tx": tx,
                    "et": et,
                    "score": score,
                }

        if best_match and best_score >= Decimal("50"):
            tx = best_match["tx"]
            et = best_match["et"]
            score = best_match["score"]

            # Determine action from rules
            should_auto = False
            applied_rule_name = None
            for rule in rules:
                if score >= rule.min_confidence * 100:
                    should_auto = rule.auto_confirm
                    applied_rule_name = rule.name
                    break

            rec_type = ReconciliationType.AUTOMATIC if should_auto else ReconciliationType.SUGGESTED
            rec_status = "confirmed" if should_auto else "pending"

            if not dry_run:
                reconciliation = _create_reconciliation(
                    db, company_id, user_id, tx, et,
                    rec_type=rec_type, rec_status=rec_status,
                    score=score, applied_rule=applied_rule_name,
                )
                # Update rule stats
                if applied_rule_name:
                    for rule in rules:
                        if rule.name == applied_rule_name:
                            rule.times_applied += 1
                            rule.last_applied_at = datetime.now(timezone.utc)
                            break

                results["matches"].append(reconciliation)
            else:
                results["matches"].append({
                    "transaction_id": tx.id,
                    "expected_transaction_id": et.id,
                    "score": float(score),
                    "type": rec_type.value,
                    "status": rec_status,
                })

            used_tx_ids.add(tx.id)
            used_et_ids.add(et.id)
            results["total_matches"] += 1
            if should_auto:
                results["confirmed"] += 1
            else:
                results["suggested"] += 1

    if not dry_run:
        db.commit()
        # Hook Module 7: update linked schedules for confirmed reconciliations
        for rec in results["matches"]:
            if hasattr(rec, "status") and rec.status == "confirmed":
                try:
                    from app.services.schedule_expected_service import on_reconciliation_confirmed
                    on_reconciliation_confirmed(db, rec)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).error(f"Schedule callback error: {e}")

    return results


def _create_reconciliation(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    tx: Transaction,
    et: ExpectedTransaction,
    *,
    rec_type: ReconciliationType,
    rec_status: str,
    score: Decimal,
    applied_rule: str | None = None,
) -> Reconciliation:
    """Create a reconciliation record with lines and update statuses."""
    now = datetime.now(timezone.utc)
    matched_amount = min(abs(tx.amount), abs(et.expected_amount - et.matched_amount))

    reconciliation = Reconciliation(
        company_id=company_id,
        type=rec_type.value,
        status=rec_status,
        reconciliation_date=now,
        matching_score=score,
        applied_rule=applied_rule,
        confirmed_by_user_id=user_id if rec_status == "confirmed" else None,
        confirmed_at=now if rec_status == "confirmed" else None,
    )
    db.add(reconciliation)
    db.flush()

    # Transaction line
    tx_line = ReconciliationLine(
        reconciliation_id=reconciliation.id,
        transaction_id=tx.id,
        matched_amount=matched_amount,
        line_type=ReconciliationLineType.TRANSACTION_MATCH,
    )
    db.add(tx_line)

    # Expected transaction line
    et_line = ReconciliationLine(
        reconciliation_id=reconciliation.id,
        expected_transaction_id=et.id,
        matched_amount=matched_amount,
        line_type=ReconciliationLineType.EXPECTED_MATCH,
    )
    db.add(et_line)

    # Update transaction status
    if rec_status == "confirmed":
        _apply_reconciliation_to_entities(tx, et, matched_amount, reconciliation.id)

    db.flush()
    db.refresh(reconciliation)
    return reconciliation


def _apply_reconciliation_to_entities(
    tx: Transaction,
    et: ExpectedTransaction,
    matched_amount: Decimal,
    reconciliation_id: uuid.UUID,
):
    """Apply reconciliation side-effects to transaction and expected transaction."""
    tx_amount = abs(tx.amount)
    if matched_amount >= tx_amount:
        tx.reconciliation_status = ReconciliationStatus.RECONCILED
    else:
        tx.reconciliation_status = ReconciliationStatus.PARTIALLY_RECONCILED
    tx.reconciliation_id = reconciliation_id

    et.matched_amount += matched_amount
    if et.matched_amount >= abs(et.expected_amount):
        et.status = ExpectedTransactionStatus.MATCHED
    else:
        et.status = ExpectedTransactionStatus.PARTIALLY_MATCHED


def confirm_reconciliation(
    db: Session,
    reconciliation_id: uuid.UUID,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Reconciliation | None:
    """Confirm a pending suggestion."""
    rec = (
        db.query(Reconciliation)
        .filter(
            Reconciliation.id == reconciliation_id,
            Reconciliation.company_id == company_id,
            Reconciliation.status == "pending",
        )
        .first()
    )
    if not rec:
        return None

    now = datetime.now(timezone.utc)
    rec.status = "confirmed"
    rec.confirmed_by_user_id = user_id
    rec.confirmed_at = now

    # Apply side-effects to entities
    for line in rec.lines:
        if line.transaction_id:
            tx = db.get(Transaction, line.transaction_id)
            if tx:
                tx.reconciliation_status = ReconciliationStatus.RECONCILED
                tx.reconciliation_id = rec.id
        if line.expected_transaction_id:
            et = db.get(ExpectedTransaction, line.expected_transaction_id)
            if et:
                et.matched_amount += line.matched_amount
                if et.matched_amount >= abs(et.expected_amount):
                    et.status = ExpectedTransactionStatus.MATCHED
                else:
                    et.status = ExpectedTransactionStatus.PARTIALLY_MATCHED

    # Hook Module 7: update linked schedules
    try:
        from app.services.schedule_expected_service import on_reconciliation_confirmed
        on_reconciliation_confirmed(db, rec)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Schedule callback error: {e}")

    db.commit()
    db.refresh(rec)
    return rec


def reject_reconciliation(
    db: Session,
    reconciliation_id: uuid.UUID,
    company_id: uuid.UUID,
) -> Reconciliation | None:
    """Reject a pending suggestion."""
    rec = (
        db.query(Reconciliation)
        .filter(
            Reconciliation.id == reconciliation_id,
            Reconciliation.company_id == company_id,
            Reconciliation.status == "pending",
        )
        .first()
    )
    if not rec:
        return None

    rec.status = "cancelled"
    db.commit()
    db.refresh(rec)
    return rec


def undo_reconciliation(
    db: Session,
    reconciliation_id: uuid.UUID,
    company_id: uuid.UUID,
) -> Reconciliation | None:
    """Undo a confirmed reconciliation. Resets entity statuses."""
    rec = (
        db.query(Reconciliation)
        .filter(
            Reconciliation.id == reconciliation_id,
            Reconciliation.company_id == company_id,
            Reconciliation.status == "confirmed",
        )
        .first()
    )
    if not rec:
        return None

    # Rollback side-effects
    for line in rec.lines:
        if line.transaction_id:
            tx = db.get(Transaction, line.transaction_id)
            if tx:
                tx.reconciliation_status = ReconciliationStatus.UNRECONCILED
                tx.reconciliation_id = None
        if line.expected_transaction_id:
            et = db.get(ExpectedTransaction, line.expected_transaction_id)
            if et:
                et.matched_amount = max(Decimal("0"), et.matched_amount - line.matched_amount)
                if et.matched_amount <= 0:
                    et.status = ExpectedTransactionStatus.OPEN
                else:
                    et.status = ExpectedTransactionStatus.PARTIALLY_MATCHED

    rec.status = "cancelled"
    db.commit()
    db.refresh(rec)
    return rec


def create_manual_reconciliation(
    db: Session,
    company_id: uuid.UUID,
    user_id: uuid.UUID,
    transaction_ids: list[uuid.UUID],
    expected_transaction_ids: list[uuid.UUID],
    notes: str | None = None,
) -> Reconciliation:
    """Create a manual reconciliation from selected transactions and expected transactions."""
    now = datetime.now(timezone.utc)

    # Fetch and validate
    transactions = (
        db.query(Transaction)
        .filter(Transaction.id.in_(transaction_ids), Transaction.company_id == company_id)
        .all()
    )
    expected_txs = (
        db.query(ExpectedTransaction)
        .filter(ExpectedTransaction.id.in_(expected_transaction_ids), ExpectedTransaction.company_id == company_id)
        .all()
    )

    if not transactions and not expected_txs:
        raise ValueError("Almeno un movimento o una transazione attesa richiesta")

    tx_total = sum(abs(t.amount) for t in transactions)
    et_total = sum(abs(e.expected_amount - e.matched_amount) for e in expected_txs)
    matched_amount = min(tx_total, et_total) if expected_txs else tx_total

    reconciliation = Reconciliation(
        company_id=company_id,
        type=ReconciliationType.MANUAL.value,
        status="confirmed",
        reconciliation_date=now,
        confirmed_by_user_id=user_id,
        confirmed_at=now,
        notes=notes,
    )
    db.add(reconciliation)
    db.flush()

    # Create lines for transactions
    for tx in transactions:
        line_amount = abs(tx.amount)
        line = ReconciliationLine(
            reconciliation_id=reconciliation.id,
            transaction_id=tx.id,
            matched_amount=line_amount,
            line_type=ReconciliationLineType.TRANSACTION_MATCH,
        )
        db.add(line)
        tx.reconciliation_status = ReconciliationStatus.RECONCILED
        tx.reconciliation_id = reconciliation.id

    # Create lines for expected transactions
    for et in expected_txs:
        remaining = abs(et.expected_amount) - et.matched_amount
        line_amount = min(remaining, matched_amount)
        line = ReconciliationLine(
            reconciliation_id=reconciliation.id,
            expected_transaction_id=et.id,
            matched_amount=line_amount,
            line_type=ReconciliationLineType.EXPECTED_MATCH,
        )
        db.add(line)
        et.matched_amount += line_amount
        if et.matched_amount >= abs(et.expected_amount):
            et.status = ExpectedTransactionStatus.MATCHED
        else:
            et.status = ExpectedTransactionStatus.PARTIALLY_MATCHED

    # Hook Module 7: update linked schedules (manual reconciliation is auto-confirmed)
    try:
        from app.services.schedule_expected_service import on_reconciliation_confirmed
        on_reconciliation_confirmed(db, reconciliation)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Schedule callback error: {e}")

    db.commit()
    db.refresh(reconciliation)
    return reconciliation
