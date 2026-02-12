import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest


def _h(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


class TestListExpectedTransactions:
    def test_list_empty(self, client, auth_headers, test_company, test_bank_account):
        resp = client.get("/api/v1/expected-transactions", headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_list_with_data(self, client, auth_headers, test_company, test_expected_transaction):
        resp = client.get("/api/v1/expected-transactions", headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["reference_number"] == "FT-2026/001"

    def test_filter_by_status(self, client, auth_headers, test_company, test_expected_transaction):
        h = _h(auth_headers, test_company)
        resp = client.get("/api/v1/expected-transactions?status=open", headers=h)
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp = client.get("/api/v1/expected-transactions?status=matched", headers=h)
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_filter_by_type(self, client, auth_headers, test_company, test_expected_transaction):
        resp = client.get("/api/v1/expected-transactions?type=expected_outflow",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_filter_by_search(self, client, auth_headers, test_company, test_expected_transaction):
        resp = client.get("/api/v1/expected-transactions?search=materiali",
                          headers=_h(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    def test_totals(self, client, auth_headers, test_company, test_expected_transaction):
        resp = client.get("/api/v1/expected-transactions", headers=_h(auth_headers, test_company))
        data = resp.json()
        assert Decimal(str(data["total_expected_amount"])) == Decimal("1500.00")
        assert Decimal(str(data["total_matched_amount"])) == Decimal("0")


class TestCreateExpectedTransaction:
    def test_create(self, client, auth_headers, test_company, test_bank_account):
        body = {
            "type": "expected_inflow",
            "expected_amount": "5000.00",
            "due_date": str(date.today() + timedelta(days=10)),
            "description": "Test fattura vendita",
            "document_type": "sales_invoice",
            "counterpart_name": "Cliente Test",
        }
        resp = client.post("/api/v1/expected-transactions", json=body,
                           headers=_h(auth_headers, test_company))
        assert resp.status_code == 201
        data = resp.json()
        assert data["type"] == "expected_inflow"
        assert Decimal(str(data["expected_amount"])) == Decimal("5000.00")
        assert data["status"] == "open"


class TestUpdateExpectedTransaction:
    def test_update(self, client, auth_headers, test_company, test_expected_transaction):
        body = {"description": "Descrizione aggiornata"}
        resp = client.patch(
            f"/api/v1/expected-transactions/{test_expected_transaction.id}",
            json=body, headers=_h(auth_headers, test_company)
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Descrizione aggiornata"


class TestDeleteExpectedTransaction:
    def test_delete(self, client, auth_headers, test_company, test_expected_transaction):
        resp = client.delete(
            f"/api/v1/expected-transactions/{test_expected_transaction.id}",
            headers=_h(auth_headers, test_company)
        )
        assert resp.status_code == 204

    def test_delete_not_found(self, client, auth_headers, test_company, test_bank_account):
        resp = client.delete(
            f"/api/v1/expected-transactions/{uuid.uuid4()}",
            headers=_h(auth_headers, test_company)
        )
        assert resp.status_code == 404
