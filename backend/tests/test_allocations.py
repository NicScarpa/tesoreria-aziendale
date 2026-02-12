"""Test per il modulo allocazioni (split) delle transazioni."""
from decimal import Decimal

from app.models import Category


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


class TestCreateAllocations:
    def test_create_split(self, client, auth_headers, test_company, test_user_company, test_transaction, test_category, db_session):
        # Create a second category for the split
        cat2 = Category(company_id=test_company.id, name="Utenze", color="#f97316")
        db_session.add(cat2)
        db_session.flush()

        resp = client.post(
            f"/api/v1/transactions/{test_transaction.id}/allocations",
            json={
                "allocations": [
                    {"category_id": str(test_category.id), "amount": 1000.00},
                    {"category_id": str(cat2.id), "amount": 500.00},
                ]
            },
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 2

        # Verify transaction category_id is cleared
        tx_resp = client.get(
            f"/api/v1/transactions/{test_transaction.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert tx_resp.json()["category_id"] is None

    def test_invalid_sum(self, client, auth_headers, test_company, test_user_company, test_transaction, test_category):
        resp = client.post(
            f"/api/v1/transactions/{test_transaction.id}/allocations",
            json={
                "allocations": [
                    {"category_id": str(test_category.id), "amount": 100.00},
                ]
            },
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 400


class TestReplaceAllocations:
    def test_replace(self, client, auth_headers, test_company, test_user_company, test_transaction, test_category, db_session):
        cat2 = Category(company_id=test_company.id, name="Utenze", color="#f97316")
        db_session.add(cat2)
        db_session.flush()

        # Create initial
        client.post(
            f"/api/v1/transactions/{test_transaction.id}/allocations",
            json={
                "allocations": [
                    {"category_id": str(test_category.id), "amount": 1500.00},
                ]
            },
            headers=_headers(auth_headers, test_company),
        )

        # Replace
        resp = client.put(
            f"/api/v1/transactions/{test_transaction.id}/allocations",
            json={
                "allocations": [
                    {"category_id": str(test_category.id), "amount": 800.00},
                    {"category_id": str(cat2.id), "amount": 700.00},
                ]
            },
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


class TestDeleteAllocations:
    def test_delete(self, client, auth_headers, test_company, test_user_company, test_transaction, test_category):
        # Create allocations first
        client.post(
            f"/api/v1/transactions/{test_transaction.id}/allocations",
            json={
                "allocations": [
                    {"category_id": str(test_category.id), "amount": 1500.00},
                ]
            },
            headers=_headers(auth_headers, test_company),
        )

        resp = client.delete(
            f"/api/v1/transactions/{test_transaction.id}/allocations",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 204

        # Verify allocations are gone
        tx_resp = client.get(
            f"/api/v1/transactions/{test_transaction.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert tx_resp.json()["allocations"] == []
