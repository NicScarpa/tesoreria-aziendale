"""Test per il modulo integrazioni - API endpoints."""
import os
import uuid

import pytest
from cryptography.fernet import Fernet


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


def _read_fixture(name: str) -> bytes:
    with open(os.path.join(FIXTURES_DIR, name), "rb") as f:
        return f.read()


# =====================================================================
# INTEGRATION OVERVIEW & CONFIG
# =====================================================================


class TestIntegrationOverview:
    def test_get_overview(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "integrations" in data
        assert isinstance(data["integrations"], list)

    def test_get_alerts_count(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/alerts-count",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "consents_expiring" in data
        assert "invoices_pending" in data
        assert "sync_errors" in data

    def test_get_config_open_banking(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/open_banking",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "integration_type" in data
        assert "is_enabled" in data


# =====================================================================
# OPEN BANKING
# =====================================================================


class TestOpenBanking:
    def test_list_institutions(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/open-banking/institutions",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_connections(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/open-banking/connections",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_get_connection_not_found(self, client, auth_headers, test_company, test_user_company):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/integrations/open-banking/connections/{fake_id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 404


# =====================================================================
# FATTURE ELETTRONICHE
# =====================================================================


class TestInvoices:
    def test_list_invoices(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/invoices",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_upload_invoice_fatturapa(self, client, auth_headers, test_company, test_user_company):
        headers = _headers(auth_headers, test_company)
        content = _read_fixture("fatturapa_td01.xml")
        resp = client.post(
            "/api/v1/integrations/invoices/upload",
            headers=headers,
            files={"file": ("fatturapa_td01.xml", content, "application/xml")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cedente_denominazione"] == "Tecnoparts SRL"
        assert data["numero_fattura"] == "FPA-2026-001"
        assert data["tipo_documento"] is not None

    def test_upload_invoice_td04(self, client, auth_headers, test_company, test_user_company):
        headers = _headers(auth_headers, test_company)
        content = _read_fixture("fatturapa_td04.xml")
        resp = client.post(
            "/api/v1/integrations/invoices/upload",
            headers=headers,
            files={"file": ("fatturapa_td04.xml", content, "application/xml")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["numero_fattura"] == "NC-2026-001"

    def test_get_invoice_not_found(self, client, auth_headers, test_company, test_user_company):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/v1/integrations/invoices/{fake_id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 404

    def test_list_invoices_with_filters(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/invoices?tipo_documento=fattura_acquisto&page=1&page_size=10",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data


# =====================================================================
# CBI / SEPA
# =====================================================================


class TestSEPA:
    def test_sepa_validate_camt053(self, client, auth_headers, test_company, test_user_company):
        headers = _headers(auth_headers, test_company)
        content = _read_fixture("camt053_sample.xml")
        resp = client.post(
            "/api/v1/integrations/sepa/validate",
            headers=headers,
            files={"file": ("camt053.xml", content, "application/xml")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert "camt.053" in data["file_type"]
        assert data["message_id"] == "CAMT053-20260201-001"

    def test_sepa_validate_pain002(self, client, auth_headers, test_company, test_user_company):
        headers = _headers(auth_headers, test_company)
        content = _read_fixture("pain002_sample.xml")
        resp = client.post(
            "/api/v1/integrations/sepa/validate",
            headers=headers,
            files={"file": ("pain002.xml", content, "application/xml")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert "pain.002" in data["file_type"]

    def test_sepa_validate_invalid(self, client, auth_headers, test_company, test_user_company):
        headers = _headers(auth_headers, test_company)
        resp = client.post(
            "/api/v1/integrations/sepa/validate",
            headers=headers,
            files={"file": ("garbage.xml", b"not valid xml", "application/xml")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is False

    def test_sepa_import_camt053(self, client, auth_headers, test_company, test_user_company):
        headers = _headers(auth_headers, test_company)
        content = _read_fixture("camt053_sample.xml")
        resp = client.post(
            "/api/v1/integrations/sepa/import-camt053",
            headers=headers,
            files={"file": ("camt053.xml", content, "application/xml")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["transactions_imported"] == 3
        assert data["balance_updated"] is True
        assert data["account_iban"] == "IT60X0542811101000000123456"

    def test_cbi_parse(self, client, auth_headers, test_company, test_user_company):
        """Test CBI rendicontazione parse endpoint with mock fixed-width data."""
        headers = _headers(auth_headers, test_company)
        # Build a minimal CBI record line (tipo 14, at least 113 chars)
        line = "14" + " " * 8 + "260201" + "C" + "0000001500000" + "48" + "RIF-TEST-001".ljust(23) + "Bonifico test".ljust(58)
        line = line.ljust(120)
        resp = client.post(
            "/api/v1/integrations/cbi/parse",
            headers=headers,
            files={"file": ("rendiconto.txt", line.encode("utf-8"), "text/plain")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["records_parsed"] >= 1


# =====================================================================
# WEBHOOK
# =====================================================================


class TestWebhooks:
    def test_list_webhooks(self, client, auth_headers, test_company, test_user_company):
        resp = client.get(
            "/api/v1/integrations/webhooks",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_create_webhook(self, client, auth_headers, test_company, test_user_company):
        resp = client.post(
            "/api/v1/integrations/webhooks",
            headers=_headers(auth_headers, test_company),
            json={"tipo": "open_banking_sync"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["tipo"] == "open_banking_sync"
        assert data["is_active"] is True
        assert "url_path" in data

    def test_create_and_delete_webhook(self, client, auth_headers, test_company, test_user_company):
        # Create
        resp = client.post(
            "/api/v1/integrations/webhooks",
            headers=_headers(auth_headers, test_company),
            json={"tipo": "generico"},
        )
        assert resp.status_code == 200
        wh_id = resp.json()["id"]

        # Delete
        resp = client.delete(
            f"/api/v1/integrations/webhooks/{wh_id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200

    def test_delete_webhook_not_found(self, client, auth_headers, test_company, test_user_company):
        fake_id = str(uuid.uuid4())
        resp = client.delete(
            f"/api/v1/integrations/webhooks/{fake_id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 404


# =====================================================================
# ENCRYPTION ROUNDTRIP (unit test, no HTTP)
# =====================================================================


class TestEncryption:
    def test_roundtrip(self, monkeypatch):
        """Test Fernet encrypt/decrypt roundtrip with a test key."""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("FERNET_KEY", test_key)

        # Reload settings to pick up env var
        from app.core.config import Settings
        test_settings = Settings()
        monkeypatch.setattr("app.core.encryption.settings", test_settings)

        from app.core.encryption import encrypt_value, decrypt_value

        plaintext = "secret-banking-token-12345"
        encrypted = encrypt_value(plaintext)
        assert encrypted != plaintext
        decrypted = decrypt_value(encrypted)
        assert decrypted == plaintext

    def test_different_values_different_ciphertexts(self, monkeypatch):
        """Same plaintext encrypted twice produces different ciphertexts (Fernet uses random IV)."""
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("FERNET_KEY", test_key)

        from app.core.config import Settings
        test_settings = Settings()
        monkeypatch.setattr("app.core.encryption.settings", test_settings)

        from app.core.encryption import encrypt_value

        enc1 = encrypt_value("same-value")
        enc2 = encrypt_value("same-value")
        # Fernet uses random IV, so ciphertexts differ
        assert enc1 != enc2

    def test_missing_fernet_key_raises(self, monkeypatch):
        """encrypt_value raises ValueError when FERNET_KEY is empty."""
        monkeypatch.setenv("FERNET_KEY", "")

        from app.core.config import Settings
        test_settings = Settings()
        monkeypatch.setattr("app.core.encryption.settings", test_settings)

        from app.core.encryption import encrypt_value

        with pytest.raises(ValueError, match="FERNET_KEY not configured"):
            encrypt_value("test")
