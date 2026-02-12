"""Test per il modulo regole di categorizzazione."""
from datetime import date
from decimal import Decimal

from app.models import (
    Transaction, FlowDirection, TransactionStatus, TransactionType,
)


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


class TestListRules:
    def test_list_empty(self, client, auth_headers, test_company, test_user_company):
        resp = client.get("/api/v1/categorization-rules", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_rules(self, client, auth_headers, test_company, test_user_company, test_categorization_rule):
        resp = client.get("/api/v1/categorization-rules", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Regola test fornitori"

    def test_filter_by_direction(self, client, auth_headers, test_company, test_user_company, test_categorization_rule):
        resp = client.get("/api/v1/categorization-rules?direction=outflow", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert len(data) == 1

        resp = client.get("/api/v1/categorization-rules?direction=inflow", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert len(data) == 0


class TestCreateRule:
    def test_create(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.post(
            "/api/v1/categorization-rules",
            json={
                "name": "Nuova regola",
                "direction": "outflow",
                "category_id": str(test_category.id),
                "conditions": [{"type": "KEYWORDS", "value": ["test"]}],
                "priority": 5,
            },
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Nuova regola"
        assert data["priority"] == 5
        assert len(data["conditions"]) == 1


class TestUpdateRule:
    def test_update(self, client, auth_headers, test_company, test_user_company, test_categorization_rule):
        resp = client.patch(
            f"/api/v1/categorization-rules/{test_categorization_rule.id}",
            json={"name": "Regola aggiornata", "priority": 20},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Regola aggiornata"
        assert data["priority"] == 20


class TestDeleteRule:
    def test_delete(self, client, auth_headers, test_company, test_user_company, test_categorization_rule):
        resp = client.delete(
            f"/api/v1/categorization-rules/{test_categorization_rule.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 204


class TestTestRule:
    def test_rule_matching(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_categorization_rule, db_session):
        # Create a transaction that matches the rule
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("-500.00"),
            currency="EUR",
            direction=FlowDirection.OUTFLOW,
            transaction_date=date.today(),
            description="Pagamento fornitore ABC",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            status=TransactionStatus.BOOKED,
        )
        db_session.add(tx)
        db_session.flush()

        resp = client.post(
            f"/api/v1/categorization-rules/{test_categorization_rule.id}/test",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["matching_count"] >= 1

    def test_rule_no_match(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_categorization_rule, db_session):
        # Create a transaction that does NOT match
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("1000.00"),
            currency="EUR",
            direction=FlowDirection.INFLOW,  # Rule is for outflow
            transaction_date=date.today(),
            description="Incasso cliente",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            status=TransactionStatus.BOOKED,
        )
        db_session.add(tx)
        db_session.flush()

        resp = client.post(
            f"/api/v1/categorization-rules/{test_categorization_rule.id}/test",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        assert resp.json()["matching_count"] == 0


class TestRulePriority:
    def test_higher_priority_wins(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        from app.models import Category, CategorizationRule, RuleActionType
        # Create second category
        cat2 = Category(company_id=test_company.id, name="Utenze", color="#f97316")
        db_session.add(cat2)
        db_session.flush()

        # Low priority rule
        rule_low = CategorizationRule(
            company_id=test_company.id,
            name="Low priority",
            direction=FlowDirection.OUTFLOW,
            action_type=RuleActionType.SET_CATEGORY,
            category_id=test_category.id,
            conditions=[{"type": "KEYWORDS", "value": ["bolletta"]}],
            priority=1,
            is_active=True,
        )
        db_session.add(rule_low)

        # High priority rule
        rule_high = CategorizationRule(
            company_id=test_company.id,
            name="High priority",
            direction=FlowDirection.OUTFLOW,
            action_type=RuleActionType.SET_CATEGORY,
            category_id=cat2.id,
            conditions=[{"type": "KEYWORDS", "value": ["bolletta"]}],
            priority=100,
            is_active=True,
        )
        db_session.add(rule_high)
        db_session.flush()

        # Create uncategorized transaction
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("-300.00"),
            currency="EUR",
            direction=FlowDirection.OUTFLOW,
            transaction_date=date.today(),
            description="Bolletta gas",
            transaction_type=TransactionType.OTHER,
            status=TransactionStatus.BOOKED,
        )
        db_session.add(tx)
        db_session.flush()

        # Recategorize
        resp = client.post("/api/v1/transactions/recategorize", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200

        # Verify high priority rule won
        resp = client.get(f"/api/v1/transactions/{tx.id}", headers=_headers(auth_headers, test_company))
        assert resp.json()["category_id"] == str(cat2.id)
