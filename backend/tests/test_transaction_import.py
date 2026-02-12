"""Test per l'import CSV delle transazioni."""
import io


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


class TestCSVImport:
    def test_import_happy_path(self, client, auth_headers, test_company, test_user_company, test_bank_account):
        csv_content = "data;importo;descrizione\n01/02/2026;-500,00;Pagamento fornitore\n02/02/2026;1200,50;Incasso cliente\n03/02/2026;-150,00;Bolletta gas\n"
        files = {"file": ("movimenti.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        data = {
            "bank_account_id": str(test_bank_account.id),
            "date_column": "data",
            "amount_column": "importo",
            "description_column": "descrizione",
            "date_format": "%d/%m/%Y",
            "decimal_separator": ",",
            "csv_separator": ";",
        }

        resp = client.post(
            "/api/v1/transactions/import",
            files=files,
            data=data,
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["total_records"] == 3
        assert result["imported_records"] == 3
        assert result["error_records"] == 0

    def test_import_with_errors(self, client, auth_headers, test_company, test_user_company, test_bank_account):
        csv_content = "data;importo;descrizione\ninvalid_date;-500,00;Test\n02/02/2026;not_a_number;Test2\n03/02/2026;-150,00;Valid\n"
        files = {"file": ("movimenti.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        data = {
            "bank_account_id": str(test_bank_account.id),
            "date_column": "data",
            "amount_column": "importo",
            "description_column": "descrizione",
        }

        resp = client.post(
            "/api/v1/transactions/import",
            files=files,
            data=data,
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["error_records"] == 2
        assert result["imported_records"] == 1
        assert result["status"] == "partial"

    def test_import_dedup(self, client, auth_headers, test_company, test_user_company, test_bank_account):
        csv_content = "data;importo;descrizione\n01/02/2026;-500,00;Pagamento duplicato\n"
        files = {"file": ("movimenti.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        data = {
            "bank_account_id": str(test_bank_account.id),
            "date_column": "data",
            "amount_column": "importo",
            "description_column": "descrizione",
        }

        # First import
        resp1 = client.post("/api/v1/transactions/import", files=files, data=data, headers=_headers(auth_headers, test_company))
        assert resp1.json()["imported_records"] == 1

        # Second import (same data) - should be skipped
        files2 = {"file": ("movimenti.csv", io.BytesIO(csv_content.encode("utf-8")), "text/csv")}
        resp2 = client.post("/api/v1/transactions/import", files=files2, data=data, headers=_headers(auth_headers, test_company))
        assert resp2.json()["skipped_records"] == 1
        assert resp2.json()["imported_records"] == 0

    def test_import_latin1_encoding(self, client, auth_headers, test_company, test_user_company, test_bank_account):
        csv_content = "data;importo;descrizione\n01/02/2026;-500,00;Pagamento caffè\n"
        files = {"file": ("movimenti.csv", io.BytesIO(csv_content.encode("iso-8859-1")), "text/csv")}
        data = {
            "bank_account_id": str(test_bank_account.id),
            "date_column": "data",
            "amount_column": "importo",
            "description_column": "descrizione",
        }

        resp = client.post("/api/v1/transactions/import", files=files, data=data, headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json()["imported_records"] == 1
