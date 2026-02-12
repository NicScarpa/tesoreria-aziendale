"""Test per il modulo transazioni."""
from datetime import date, timedelta
from decimal import Decimal

from app.models import (
    Transaction, FlowDirection, TransactionStatus, TransactionType, CategorizationSource,
)


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


def _create_transactions(db_session, test_company, test_bank_account, test_category, n=5):
    """Helper to create multiple transactions."""
    txs = []
    for i in range(n):
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal(f"{(i + 1) * 1000}.00") * (1 if i % 2 == 0 else -1),
            currency="EUR",
            direction=FlowDirection.INFLOW if i % 2 == 0 else FlowDirection.OUTFLOW,
            transaction_date=date.today() - timedelta(days=i),
            description=f"Transazione test {i}",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            category_id=test_category.id if i < 3 else None,
            categorization_source=CategorizationSource.MANUAL if i < 3 else None,
            status=TransactionStatus.BOOKED,
            verified=i < 2,
        )
        db_session.add(tx)
        txs.append(tx)
    db_session.flush()
    return txs


class TestListTransactions:
    def test_list_empty(self, client, auth_headers, test_company, test_user_company, test_bank_account):
        resp = client.get("/api/v1/transactions", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_with_data(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get("/api/v1/transactions", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert data["total"] == 5
        assert len(data["items"]) == 5

    def test_filter_by_direction(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get("/api/v1/transactions?direction=inflow", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert all(item["direction"] == "inflow" for item in data["items"])

    def test_filter_by_date_range(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        resp = client.get(
            f"/api/v1/transactions?date_from={yesterday}&date_to={today}",
            headers=_headers(auth_headers, test_company),
        )
        data = resp.json()
        assert data["total"] <= 2

    def test_filter_by_category(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get(
            f"/api/v1/transactions?category_id={test_category.id}",
            headers=_headers(auth_headers, test_company),
        )
        data = resp.json()
        assert data["total"] == 3

    def test_filter_uncategorized(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get("/api/v1/transactions?uncategorized=true", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert data["total"] == 2

    def test_filter_verified(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get("/api/v1/transactions?verified=true", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert data["total"] == 2

    def test_pagination(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get("/api/v1/transactions?page=1&page_size=2", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2

    def test_filter_by_bank_account(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get(
            f"/api/v1/transactions?bank_account_id={test_bank_account.id}",
            headers=_headers(auth_headers, test_company),
        )
        data = resp.json()
        assert data["total"] == 5


class TestGetTransaction:
    def test_get(self, client, auth_headers, test_company, test_user_company, test_transaction):
        resp = client.get(
            f"/api/v1/transactions/{test_transaction.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["description"] == "Pagamento fornitore test"
        assert data["bank_account_nickname"] == "Conto Test"

    def test_get_not_found(self, client, auth_headers, test_company, test_user_company):
        import uuid
        resp = client.get(
            f"/api/v1/transactions/{uuid.uuid4()}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 404


class TestMetadata:
    def test_metadata(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, db_session):
        _create_transactions(db_session, test_company, test_bank_account, test_category)
        resp = client.get("/api/v1/transactions/metadata", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 5
        assert "positive" in data["totals"]
        assert "negative" in data["totals"]
        assert data["total_uncategorized"] == 2


class TestUpdateTransaction:
    def test_update_category(self, client, auth_headers, test_company, test_user_company, test_transaction, test_category):
        resp = client.patch(
            f"/api/v1/transactions/{test_transaction.id}",
            json={"category_id": str(test_category.id), "notes": "Aggiornato"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["notes"] == "Aggiornato"

    def test_update_verified(self, client, auth_headers, test_company, test_user_company, test_transaction):
        resp = client.patch(
            f"/api/v1/transactions/{test_transaction.id}",
            json={"verified": True},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        assert resp.json()["verified"] is True


class TestDeleteTransaction:
    def test_delete(self, client, auth_headers, test_company, test_user_company, test_transaction):
        resp = client.delete(
            f"/api/v1/transactions/{test_transaction.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 204


class TestToggleVerified:
    def test_toggle(self, client, auth_headers, test_company, test_user_company, test_transaction):
        # Initially false
        resp = client.patch(
            f"/api/v1/transactions/{test_transaction.id}/verify",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        assert resp.json()["verified"] is True

        # Toggle back
        resp = client.patch(
            f"/api/v1/transactions/{test_transaction.id}/verify",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.json()["verified"] is False


class TestRecategorize:
    def test_recategorize(self, client, auth_headers, test_company, test_user_company, test_bank_account, test_category, test_categorization_rule, db_session):
        # Create uncategorized transaction that matches rule
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("-500.00"),
            currency="EUR",
            direction=FlowDirection.OUTFLOW,
            transaction_date=date.today(),
            description="Pagamento fornitore XYZ",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            status=TransactionStatus.BOOKED,
        )
        db_session.add(tx)
        db_session.flush()

        resp = client.post("/api/v1/transactions/recategorize", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["categorized_count"] >= 1


class TestCompanyIsolation:
    def test_cannot_see_other_company_transactions(self, client, auth_headers, test_company, test_user_company, test_transaction, db_session):
        # Create another company with a transaction
        from app.models import Company
        other = Company(name="Other SRL", vat_number="11111111111", country="IT")
        db_session.add(other)
        db_session.flush()

        other_tx = Transaction(
            company_id=other.id,
            bank_account_id=test_transaction.bank_account_id,
            amount=Decimal("999.00"),
            currency="EUR",
            direction=FlowDirection.INFLOW,
            transaction_date=date.today(),
            description="Other company tx",
            transaction_type=TransactionType.OTHER,
            status=TransactionStatus.BOOKED,
        )
        db_session.add(other_tx)
        db_session.flush()

        resp = client.get("/api/v1/transactions", headers=_headers(auth_headers, test_company))
        data = resp.json()
        ids = [item["id"] for item in data["items"]]
        assert str(other_tx.id) not in ids
