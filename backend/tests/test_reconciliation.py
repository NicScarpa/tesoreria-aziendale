import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest


def _h(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


class TestMatchingExact:
    """Test exact match: same amount + counterpart → score >= 90."""
    def test_exact_match(self, client, auth_headers, test_company,
                         test_transaction, test_expected_transaction):
        resp = client.get(
            f"/api/v1/reconciliation/find-matches/{test_transaction.id}",
            headers=_h(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matches"]) >= 1
        best = data["matches"][0]
        assert Decimal(str(best["score"])) >= 90


class TestMatchingInflow:
    """Test matching inflow transaction with expected inflow."""
    def test_inflow_match(self, client, auth_headers, test_company,
                          test_inflow_transaction, test_expected_inflow):
        resp = client.get(
            f"/api/v1/reconciliation/find-matches/{test_inflow_transaction.id}",
            headers=_h(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matches"]) >= 1
        best = data["matches"][0]
        assert Decimal(str(best["score"])) == 100


class TestFindMatchesForExpected:
    def test_find_matches(self, client, auth_headers, test_company,
                          test_transaction, test_expected_transaction):
        resp = client.get(
            f"/api/v1/reconciliation/find-matches-for-expected/{test_expected_transaction.id}",
            headers=_h(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["matches"]) >= 1


class TestManualReconciliation:
    def test_create_and_verify_states(self, client, auth_headers, test_company,
                                      test_transaction, test_expected_transaction):
        h = _h(auth_headers, test_company)
        body = {
            "transaction_ids": [str(test_transaction.id)],
            "expected_transaction_ids": [str(test_expected_transaction.id)],
            "notes": "Riconciliazione manuale test",
        }
        resp = client.post("/api/v1/reconciliation", json=body, headers=h)
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "confirmed"
        assert data["type"] == "manual"
        assert len(data["lines"]) == 2

        # Verify transaction state
        tx_resp = client.get(f"/api/v1/transactions/{test_transaction.id}", headers=h)
        assert tx_resp.json()["reconciliation_status"] == "reconciled"

        # Verify expected transaction state
        et_resp = client.get(
            f"/api/v1/expected-transactions/{test_expected_transaction.id}",
            headers=h
        )
        assert et_resp.json()["status"] == "matched"


class TestAutoMatch:
    def test_auto_match_dry_run(self, client, auth_headers, test_company,
                                test_inflow_transaction, test_expected_inflow):
        body = {"dry_run": True}
        resp = client.post("/api/v1/reconciliation/auto-match", json=body,
                           headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_matches"] >= 1

    def test_auto_match_execute(self, client, auth_headers, test_company,
                                test_inflow_transaction, test_expected_inflow):
        body = {"dry_run": False}
        resp = client.post("/api/v1/reconciliation/auto-match", json=body,
                           headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_matches"] >= 1


class TestConfirmRejectSuggestion:
    def test_confirm_suggestion(self, client, auth_headers, test_company,
                                test_inflow_transaction, test_expected_inflow, db_session):
        from app.models.reconciliation import Reconciliation
        from app.models.reconciliation_line import ReconciliationLine
        from app.models.enums import ReconciliationLineType
        from datetime import datetime, timezone

        rec = Reconciliation(
            company_id=test_company.id,
            type="suggested",
            status="pending",
            reconciliation_date=datetime.now(timezone.utc),
            matching_score=Decimal("90"),
        )
        db_session.add(rec)
        db_session.flush()
        line1 = ReconciliationLine(
            reconciliation_id=rec.id,
            transaction_id=test_inflow_transaction.id,
            matched_amount=Decimal("3000.00"),
            line_type=ReconciliationLineType.TRANSACTION_MATCH,
        )
        line2 = ReconciliationLine(
            reconciliation_id=rec.id,
            expected_transaction_id=test_expected_inflow.id,
            matched_amount=Decimal("3000.00"),
            line_type=ReconciliationLineType.EXPECTED_MATCH,
        )
        db_session.add_all([line1, line2])
        db_session.flush()

        resp = client.put(f"/api/v1/reconciliation/{rec.id}/confirm",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["status"] == "confirmed"

    def test_reject_suggestion(self, client, auth_headers, test_company,
                               test_inflow_transaction, test_expected_inflow, db_session):
        from app.models.reconciliation import Reconciliation
        from app.models.reconciliation_line import ReconciliationLine
        from app.models.enums import ReconciliationLineType
        from datetime import datetime, timezone

        rec = Reconciliation(
            company_id=test_company.id,
            type="suggested",
            status="pending",
            reconciliation_date=datetime.now(timezone.utc),
            matching_score=Decimal("60"),
        )
        db_session.add(rec)
        db_session.flush()
        line = ReconciliationLine(
            reconciliation_id=rec.id,
            transaction_id=test_inflow_transaction.id,
            matched_amount=Decimal("3000.00"),
            line_type=ReconciliationLineType.TRANSACTION_MATCH,
        )
        db_session.add(line)
        db_session.flush()

        resp = client.put(f"/api/v1/reconciliation/{rec.id}/reject",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"


class TestUndoReconciliation:
    def test_undo(self, client, auth_headers, test_company,
                  test_reconciliation, test_transaction, test_expected_transaction):
        h = _h(auth_headers, test_company)
        resp = client.post(
            f"/api/v1/reconciliation/{test_reconciliation.id}/undo",
            headers=h
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

        # Verify rollback
        tx_resp = client.get(f"/api/v1/transactions/{test_transaction.id}", headers=h)
        assert tx_resp.json()["reconciliation_status"] == "unreconciled"


class TestDashboard:
    def test_dashboard(self, client, auth_headers, test_company,
                       test_transaction, test_expected_transaction):
        resp = client.get("/api/v1/reconciliation/dashboard",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["unreconciled_transactions"] >= 1
        assert data["open_expected"] >= 1
        assert "reconciliation_rate" in data


class TestListReconciliations:
    def test_list_empty(self, client, auth_headers, test_company, test_bank_account):
        resp = client.get("/api/v1/reconciliation",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_with_data(self, client, auth_headers, test_company, test_reconciliation):
        resp = client.get("/api/v1/reconciliation",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1


class TestGetReconciliation:
    def test_get(self, client, auth_headers, test_company, test_reconciliation):
        resp = client.get(
            f"/api/v1/reconciliation/{test_reconciliation.id}",
            headers=_h(auth_headers, test_company)
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "confirmed"
        assert len(data["lines"]) == 2

    def test_not_found(self, client, auth_headers, test_company, test_bank_account):
        resp = client.get(
            f"/api/v1/reconciliation/{uuid.uuid4()}",
            headers=_h(auth_headers, test_company)
        )
        assert resp.status_code == 404


class TestSuggestions:
    def test_get_suggestions(self, client, auth_headers, test_company, test_bank_account):
        resp = client.get("/api/v1/reconciliation/suggestions",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_bulk_confirm(self, client, auth_headers, test_company, test_bank_account):
        body = {"reconciliation_ids": []}
        resp = client.post("/api/v1/reconciliation/suggestions/bulk-confirm",
                           json=body, headers=_h(auth_headers, test_company))
        assert resp.status_code == 200

    def test_bulk_reject(self, client, auth_headers, test_company, test_bank_account):
        body = {"reconciliation_ids": []}
        resp = client.post("/api/v1/reconciliation/suggestions/bulk-reject",
                           json=body, headers=_h(auth_headers, test_company))
        assert resp.status_code == 200


class TestReconciliationRulesExtended:
    def test_reorder(self, client, auth_headers, test_company, db_session):
        from app.models.reconciliation_rule import ReconciliationRule
        rule1 = ReconciliationRule(
            company_id=test_company.id, name="Rule 1", priority=10,
        )
        rule2 = ReconciliationRule(
            company_id=test_company.id, name="Rule 2", priority=20,
        )
        db_session.add_all([rule1, rule2])
        db_session.flush()

        body = {"rule_ids": [str(rule2.id), str(rule1.id)]}
        resp = client.put("/api/v1/reconciliation-rules/reorder", json=body,
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        rules = resp.json()
        assert len(rules) >= 2

    def test_test_rule(self, client, auth_headers, test_company, db_session):
        from app.models.reconciliation_rule import ReconciliationRule
        rule = ReconciliationRule(
            company_id=test_company.id, name="Test Rule", priority=10,
            min_confidence=Decimal("0.50"),
        )
        db_session.add(rule)
        db_session.flush()

        resp = client.post(
            f"/api/v1/reconciliation-rules/{rule.id}/test",
            headers=_h(auth_headers, test_company)
        )
        assert resp.status_code == 200
        assert "matching_count" in resp.json()
