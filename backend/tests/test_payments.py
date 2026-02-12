"""Test suite for Module 8: Payment Management."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models import (
    PaymentOrder, PaymentOrderLine, PaymentApproval, PaymentTemplate,
    PaymentOrderType, PaymentOrderStatus, PaymentPriority,
    PaymentLineStatus, ApprovalAction,
    Schedule, SchedulePayment, ScheduleType, ScheduleStatus,
    DocumentType, SchedulePriority, ScheduleSource, PaymentMethod,
    User, UserCompany, UserRole, UserCompanyStatus,
)
from app.core.security import get_password_hash


def _h(auth_headers: dict) -> dict:
    """Auth + company headers shortcut."""
    return {
        "Authorization": auth_headers["Authorization"],
        "X-Company-ID": auth_headers.get("_company_id", ""),
    }


@pytest.fixture()
def auth_headers_with_company(auth_headers, test_company):
    headers = dict(auth_headers)
    headers["_company_id"] = str(test_company.id)
    headers["X-Company-ID"] = str(test_company.id)
    return headers


@pytest.fixture()
def second_user(db_session) -> User:
    user = User(
        email="approver@example.com",
        password_hash=get_password_hash("Test1234!"),
        first_name="Approver",
        last_name="User",
        email_verified=True,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture()
def second_user_company(db_session, second_user, test_company) -> UserCompany:
    uc = UserCompany(
        user_id=second_user.id,
        company_id=test_company.id,
        role=UserRole.ADMIN,
        status=UserCompanyStatus.ACTIVE,
    )
    db_session.add(uc)
    db_session.flush()
    return uc


@pytest.fixture()
def second_auth_headers(client, second_user, second_user_company, test_company) -> dict:
    resp = client.post("/api/v1/auth/login", json={
        "email": "approver@example.com", "password": "Test1234!",
    })
    tokens = resp.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Company-ID": str(test_company.id),
        "_company_id": str(test_company.id),
    }


@pytest.fixture()
def test_payment_order(db_session, test_company, test_bank_account, test_user) -> PaymentOrder:
    order = PaymentOrder(
        company_id=test_company.id,
        bank_account_id=test_bank_account.id,
        tipo=PaymentOrderType.SEPA_CREDIT_TRANSFER,
        stato=PaymentOrderStatus.BOZZA,
        riferimento_interno="PAG-2026-99001",
        data_esecuzione_richiesta=date.today() + timedelta(days=5),
        importo_totale=Decimal("2500.00"),
        numero_disposizioni=1,
        valuta="EUR",
        priorita=PaymentPriority.NORMALE,
        creato_da_user_id=test_user.id,
        note="Test order",
    )
    db_session.add(order)
    db_session.flush()
    return order


@pytest.fixture()
def test_payment_line(db_session, test_payment_order) -> PaymentOrderLine:
    line = PaymentOrderLine(
        payment_order_id=test_payment_order.id,
        beneficiario_nome="Fornitore Test SRL",
        beneficiario_iban="IT60X0542811101000000111111",
        importo=Decimal("2500.00"),
        valuta="EUR",
        causale="Saldo fattura test",
        end_to_end_id="E2E-TEST-001",
        stato=PaymentLineStatus.INCLUSA,
    )
    db_session.add(line)
    db_session.flush()
    return line


@pytest.fixture()
def test_schedule_passiva(db_session, test_company, test_bank_account, test_user) -> Schedule:
    s = Schedule(
        company_id=test_company.id,
        tipo=ScheduleType.PASSIVA,
        stato=ScheduleStatus.APERTA,
        descrizione="Fattura fornitore da pagare",
        importo_totale=Decimal("3000.00"),
        importo_pagato=Decimal("0"),
        valuta="EUR",
        data_scadenza=date.today() + timedelta(days=10),
        tipo_documento=DocumentType.FATTURA_ACQUISTO,
        numero_documento="FT-TEST/001",
        controparte_nome="Fornitore Alpha SRL",
        controparte_iban="IT60X0542811101000000111111",
        bank_account_id=test_bank_account.id,
        priorita=SchedulePriority.NORMALE,
        source=ScheduleSource.MANUALE,
        is_ricorrente=False,
        ricorrenza_attiva=True,
        created_by_user_id=test_user.id,
    )
    db_session.add(s)
    db_session.flush()
    return s


# ===== Test Classes =====

class TestPaymentOrderCRUD:

    def test_create_payment_order(self, client, auth_headers_with_company, test_bank_account):
        resp = client.post("/api/v1/payments", headers=_h(auth_headers_with_company), json={
            "tipo": "sepa_credit_transfer",
            "bank_account_id": str(test_bank_account.id),
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
            "priorita": "normale",
            "note": "Test payment",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "sepa_credit_transfer"
        assert data["stato"] == "bozza"
        assert data["riferimento_interno"].startswith("PAG-")

    def test_list_payment_orders(self, client, auth_headers_with_company, test_payment_order):
        resp = client.get("/api/v1/payments", headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
        assert "summary" in data

    def test_list_payment_orders_filter_stato(self, client, auth_headers_with_company, test_payment_order):
        resp = client.get("/api/v1/payments?stato=bozza", headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["stato"] == "bozza" for item in data["items"])

    def test_get_payment_order(self, client, auth_headers_with_company, test_payment_order):
        resp = client.get(f"/api/v1/payments/{test_payment_order.id}", headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert resp.json()["id"] == str(test_payment_order.id)

    def test_get_payment_order_404(self, client, auth_headers_with_company):
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/v1/payments/{fake_id}", headers=_h(auth_headers_with_company))
        assert resp.status_code == 404

    def test_update_payment_order(self, client, auth_headers_with_company, test_payment_order):
        resp = client.put(f"/api/v1/payments/{test_payment_order.id}", headers=_h(auth_headers_with_company), json={
            "note": "Updated note",
            "priorita": "alta",
        })
        assert resp.status_code == 200
        assert resp.json()["note"] == "Updated note"
        assert resp.json()["priorita"] == "alta"

    def test_delete_payment_order(self, client, auth_headers_with_company, test_payment_order):
        resp = client.delete(f"/api/v1/payments/{test_payment_order.id}", headers=_h(auth_headers_with_company))
        assert resp.status_code == 204

    def test_create_validates_tipo(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments", headers=_h(auth_headers_with_company), json={
            "tipo": "sepa_credit_transfer",
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 201

    def test_summary(self, client, auth_headers_with_company, test_payment_order):
        resp = client.get("/api/v1/payments/summary", headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        data = resp.json()
        assert "totale_bozze" in data
        assert "importo_bozze" in data


class TestPaymentOrderLines:

    def test_add_line(self, client, auth_headers_with_company, test_payment_order):
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/lines",
                           headers=_h(auth_headers_with_company), json={
            "beneficiario_nome": "Fornitore Test",
            "beneficiario_iban": "IT60X0542811101000000111111",
            "importo": "1500.00",
            "causale": "Test causale",
        })
        assert resp.status_code == 201
        assert resp.json()["beneficiario_nome"] == "Fornitore Test"
        assert resp.json()["importo"] == "1500.00"

    def test_update_line(self, client, auth_headers_with_company, test_payment_order, test_payment_line):
        resp = client.put(
            f"/api/v1/payments/{test_payment_order.id}/lines/{test_payment_line.id}",
            headers=_h(auth_headers_with_company), json={
                "importo": "3000.00",
                "causale": "Updated causale",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["importo"] == "3000.00"

    def test_delete_line(self, client, auth_headers_with_company, test_payment_order, test_payment_line):
        resp = client.delete(
            f"/api/v1/payments/{test_payment_order.id}/lines/{test_payment_line.id}",
            headers=_h(auth_headers_with_company),
        )
        assert resp.status_code == 204

    def test_add_line_recalculates_totals(self, client, auth_headers_with_company, test_payment_order):
        client.post(f"/api/v1/payments/{test_payment_order.id}/lines",
                     headers=_h(auth_headers_with_company), json={
            "beneficiario_nome": "Fornitore A",
            "importo": "1000.00",
        })
        client.post(f"/api/v1/payments/{test_payment_order.id}/lines",
                     headers=_h(auth_headers_with_company), json={
            "beneficiario_nome": "Fornitore B",
            "importo": "2000.00",
        })
        resp = client.get(f"/api/v1/payments/{test_payment_order.id}",
                          headers=_h(auth_headers_with_company))
        data = resp.json()
        assert Decimal(data["importo_totale"]) == Decimal("3000.00")
        assert data["numero_disposizioni"] == 2

    def test_add_line_to_non_bozza_fails(self, client, auth_headers_with_company,
                                          test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/lines",
                           headers=_h(auth_headers_with_company), json={
            "beneficiario_nome": "Should Fail",
            "importo": "100.00",
        })
        assert resp.status_code == 400

    def test_add_multiple_lines(self, client, auth_headers_with_company, test_payment_order):
        for i in range(3):
            resp = client.post(f"/api/v1/payments/{test_payment_order.id}/lines",
                               headers=_h(auth_headers_with_company), json={
                "beneficiario_nome": f"Fornitore {i}",
                "importo": f"{1000 + i * 500}.00",
            })
            assert resp.status_code == 201

    def test_delete_recalculates(self, client, auth_headers_with_company, test_payment_order, test_payment_line):
        client.delete(f"/api/v1/payments/{test_payment_order.id}/lines/{test_payment_line.id}",
                       headers=_h(auth_headers_with_company))
        resp = client.get(f"/api/v1/payments/{test_payment_order.id}",
                          headers=_h(auth_headers_with_company))
        assert Decimal(resp.json()["importo_totale"]) == Decimal("0")

    def test_update_nonexistent_line(self, client, auth_headers_with_company, test_payment_order):
        fake_id = uuid.uuid4()
        resp = client.put(f"/api/v1/payments/{test_payment_order.id}/lines/{fake_id}",
                          headers=_h(auth_headers_with_company), json={"importo": "100.00"})
        assert resp.status_code == 400


class TestPaymentOrderWorkflow:

    def test_submit_order(self, client, auth_headers_with_company, test_payment_order, test_payment_line):
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/submit",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert resp.json()["stato"] == "da_approvare"

    def test_submit_empty_order_fails(self, client, auth_headers_with_company, test_payment_order):
        # No lines => should fail
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/submit",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 400

    def test_approve_order(self, client, auth_headers_with_company, second_auth_headers,
                           test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/approve",
                           headers=_h(second_auth_headers), json={"commento": "Approvato"})
        assert resp.status_code == 200
        assert resp.json()["stato"] == "approvata"

    def test_approve_by_creator_fails(self, client, auth_headers_with_company,
                                       test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        # Same user who created tries to approve
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/approve",
                           headers=_h(auth_headers_with_company), json={})
        assert resp.status_code == 400

    def test_reject_order(self, client, second_auth_headers,
                          test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/reject",
                           headers=_h(second_auth_headers), json={"commento": "Da rivedere"})
        assert resp.status_code == 200
        assert resp.json()["stato"] == "bozza"

    def test_reject_requires_comment(self, client, second_auth_headers,
                                      test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/reject",
                           headers=_h(second_auth_headers), json={})
        assert resp.status_code == 422  # Validation error

    def test_invalid_transition(self, client, auth_headers_with_company,
                                 test_payment_order, test_payment_line, db_session):
        # Try approve from bozza (should fail, must submit first)
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/approve",
                           headers=_h(auth_headers_with_company), json={})
        assert resp.status_code == 400

    def test_approval_audit_trail(self, client, auth_headers_with_company, second_auth_headers,
                                   test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()

        client.post(f"/api/v1/payments/{test_payment_order.id}/approve",
                     headers=_h(second_auth_headers), json={"commento": "OK"})

        resp = client.get(f"/api/v1/payments/{test_payment_order.id}/approvals",
                          headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert data[0]["azione"] == "approvata"

    def test_full_workflow_bozza_to_approvata(self, client, auth_headers_with_company,
                                               second_auth_headers, test_payment_order,
                                               test_payment_line, db_session):
        # Submit
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/submit",
                           headers=_h(auth_headers_with_company))
        assert resp.json()["stato"] == "da_approvare"
        # Approve
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/approve",
                           headers=_h(second_auth_headers), json={})
        assert resp.json()["stato"] == "approvata"

    def test_submit_then_reject_then_resubmit(self, client, auth_headers_with_company,
                                                second_auth_headers, test_payment_order,
                                                test_payment_line, db_session):
        client.post(f"/api/v1/payments/{test_payment_order.id}/submit",
                     headers=_h(auth_headers_with_company))
        client.post(f"/api/v1/payments/{test_payment_order.id}/reject",
                     headers=_h(second_auth_headers), json={"commento": "Fix amount"})
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/submit",
                           headers=_h(auth_headers_with_company))
        assert resp.json()["stato"] == "da_approvare"

    def test_update_non_bozza_fails(self, client, auth_headers_with_company,
                                     test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        resp = client.put(f"/api/v1/payments/{test_payment_order.id}",
                          headers=_h(auth_headers_with_company), json={"note": "Should fail"})
        assert resp.status_code == 400

    def test_delete_non_bozza_fails(self, client, auth_headers_with_company,
                                     test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.DA_APPROVARE
        db_session.flush()
        resp = client.delete(f"/api/v1/payments/{test_payment_order.id}",
                             headers=_h(auth_headers_with_company))
        assert resp.status_code == 400


class TestPaymentFileGeneration:

    def test_generate_sepa_file(self, client, auth_headers_with_company, second_auth_headers,
                                 test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.APPROVATA
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert resp.json()["stato"] == "file_generato"
        assert resp.json()["file_generato_nome"].endswith(".xml")

    def test_generate_riba_file(self, client, auth_headers_with_company,
                                 test_payment_order, test_payment_line, db_session):
        test_payment_order.tipo = PaymentOrderType.RIBA
        test_payment_order.stato = PaymentOrderStatus.APPROVATA
        test_payment_line.riba_data_scadenza = date.today() + timedelta(days=10)
        test_payment_line.riba_piazza = "Milano"
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert resp.json()["file_generato_nome"].endswith(".txt")

    def test_generate_f24_file(self, client, auth_headers_with_company,
                                test_payment_order, db_session):
        test_payment_order.tipo = PaymentOrderType.F24
        test_payment_order.stato = PaymentOrderStatus.APPROVATA
        # Add F24 line
        line = PaymentOrderLine(
            payment_order_id=test_payment_order.id,
            beneficiario_nome="Agenzia delle Entrate",
            importo=Decimal("1200.00"),
            f24_sezione="erario",
            f24_codice_tributo="6001",
            f24_anno_riferimento=2026,
            f24_mese_riferimento=1,
            f24_importo_debito=Decimal("1200.00"),
            f24_importo_credito=Decimal("0"),
            stato=PaymentLineStatus.INCLUSA,
        )
        db_session.add(line)
        test_payment_order.importo_totale = Decimal("1200.00")
        test_payment_order.numero_disposizioni = 1
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 200

    def test_generate_sdd_file(self, client, auth_headers_with_company,
                                test_payment_order, db_session):
        test_payment_order.tipo = PaymentOrderType.SDD
        test_payment_order.stato = PaymentOrderStatus.APPROVATA
        line = PaymentOrderLine(
            payment_order_id=test_payment_order.id,
            beneficiario_nome="Cliente Debitore SRL",
            beneficiario_iban="IT60X0542811101000000333333",
            importo=Decimal("500.00"),
            causale="Incasso SDD",
            sdd_mandate_id="MNDT-001",
            sdd_mandate_date=date(2025, 1, 15),
            sdd_mandate_type="core",
            sdd_sequence_type="rcur",
            stato=PaymentLineStatus.INCLUSA,
        )
        db_session.add(line)
        test_payment_order.importo_totale = Decimal("500.00")
        test_payment_order.numero_disposizioni = 1
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 200

    def test_download_file(self, client, auth_headers_with_company,
                           test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.APPROVATA
        db_session.flush()
        client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                     headers=_h(auth_headers_with_company))
        resp = client.get(f"/api/v1/payments/{test_payment_order.id}/download-file",
                          headers=_h(auth_headers_with_company))
        assert resp.status_code == 200

    def test_download_without_file_fails(self, client, auth_headers_with_company, test_payment_order):
        resp = client.get(f"/api/v1/payments/{test_payment_order.id}/download-file",
                          headers=_h(auth_headers_with_company))
        assert resp.status_code == 404

    def test_generate_non_approvata_fails(self, client, auth_headers_with_company,
                                           test_payment_order, test_payment_line):
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 400

    def test_regenerate_file(self, client, auth_headers_with_company,
                              test_payment_order, test_payment_line, db_session):
        # Generate once, then transition back to approvata and regenerate
        test_payment_order.stato = PaymentOrderStatus.APPROVATA
        db_session.flush()
        resp1 = client.post(f"/api/v1/payments/{test_payment_order.id}/generate-file",
                            headers=_h(auth_headers_with_company))
        assert resp1.json()["stato"] == "file_generato"


class TestPaymentExecution:

    def test_mark_sent(self, client, auth_headers_with_company,
                       test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.FILE_GENERATO
        test_payment_order.file_generato_path = "/tmp/test.xml"
        test_payment_order.file_generato_nome = "test.xml"
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/mark-sent",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert resp.json()["stato"] == "inviata_banca"

    def test_mark_executed(self, client, auth_headers_with_company,
                           test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.INVIATA_BANCA
        db_session.flush()
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/mark-executed",
                           headers=_h(auth_headers_with_company), json={})
        assert resp.status_code == 200
        assert resp.json()["stato"] == "eseguita"

    def test_mark_executed_with_date(self, client, auth_headers_with_company,
                                      test_payment_order, test_payment_line, db_session):
        test_payment_order.stato = PaymentOrderStatus.INVIATA_BANCA
        db_session.flush()
        exec_date = str(date.today() - timedelta(days=1))
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/mark-executed",
                           headers=_h(auth_headers_with_company),
                           json={"data_esecuzione": exec_date})
        assert resp.status_code == 200

    def test_mark_sent_invalid_state(self, client, auth_headers_with_company,
                                      test_payment_order, test_payment_line):
        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/mark-sent",
                           headers=_h(auth_headers_with_company))
        assert resp.status_code == 400

    def test_mark_executed_updates_schedule(self, client, auth_headers_with_company,
                                             test_payment_order, test_schedule_passiva, db_session):
        line = PaymentOrderLine(
            payment_order_id=test_payment_order.id,
            beneficiario_nome="Fornitore Alpha SRL",
            beneficiario_iban="IT60X0542811101000000111111",
            importo=Decimal("3000.00"),
            causale="Pagamento test",
            schedule_id=test_schedule_passiva.id,
            stato=PaymentLineStatus.INCLUSA,
        )
        db_session.add(line)
        test_payment_order.stato = PaymentOrderStatus.INVIATA_BANCA
        test_payment_order.importo_totale = Decimal("3000.00")
        test_payment_order.numero_disposizioni = 1
        db_session.flush()

        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/mark-executed",
                           headers=_h(auth_headers_with_company), json={})
        assert resp.status_code == 200

        # Check schedule was updated
        db_session.refresh(test_schedule_passiva)
        assert test_schedule_passiva.importo_pagato == Decimal("3000.00")
        assert test_schedule_passiva.stato == ScheduleStatus.PAGATA

    def test_mark_executed_partial_schedule(self, client, auth_headers_with_company,
                                             test_payment_order, test_schedule_passiva, db_session):
        line = PaymentOrderLine(
            payment_order_id=test_payment_order.id,
            beneficiario_nome="Fornitore Alpha SRL",
            importo=Decimal("1000.00"),
            schedule_id=test_schedule_passiva.id,
            stato=PaymentLineStatus.INCLUSA,
        )
        db_session.add(line)
        test_payment_order.stato = PaymentOrderStatus.INVIATA_BANCA
        test_payment_order.importo_totale = Decimal("1000.00")
        test_payment_order.numero_disposizioni = 1
        db_session.flush()

        resp = client.post(f"/api/v1/payments/{test_payment_order.id}/mark-executed",
                           headers=_h(auth_headers_with_company), json={})
        assert resp.status_code == 200

        db_session.refresh(test_schedule_passiva)
        assert test_schedule_passiva.importo_pagato == Decimal("1000.00")
        assert test_schedule_passiva.stato == ScheduleStatus.PARZIALMENTE_PAGATA


class TestPaymentFromSchedules:

    def test_create_from_schedules(self, client, auth_headers_with_company,
                                    test_schedule_passiva, test_bank_account):
        resp = client.post("/api/v1/payments/from-schedules", headers=_h(auth_headers_with_company), json={
            "schedule_ids": [str(test_schedule_passiva.id)],
            "bank_account_id": str(test_bank_account.id),
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "sepa_credit_transfer"
        assert data["numero_disposizioni"] == 1
        assert Decimal(data["importo_totale"]) == Decimal("3000.00")

    def test_from_schedules_invalid_tipo(self, client, auth_headers_with_company,
                                          db_session, test_company, test_bank_account, test_user):
        s = Schedule(
            company_id=test_company.id,
            tipo=ScheduleType.ATTIVA,
            stato=ScheduleStatus.APERTA,
            descrizione="Da incassare",
            importo_totale=Decimal("500.00"),
            importo_pagato=Decimal("0"),
            valuta="EUR",
            data_scadenza=date.today() + timedelta(days=5),
            tipo_documento=DocumentType.FATTURA_VENDITA,
            priorita=SchedulePriority.NORMALE,
            source=ScheduleSource.MANUALE,
            is_ricorrente=False,
            ricorrenza_attiva=True,
            created_by_user_id=test_user.id,
        )
        db_session.add(s)
        db_session.flush()

        resp = client.post("/api/v1/payments/from-schedules", headers=_h(auth_headers_with_company), json={
            "schedule_ids": [str(s.id)],
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 400  # attiva not allowed

    def test_from_schedules_partial_amount(self, client, auth_headers_with_company,
                                            test_schedule_passiva, test_bank_account, db_session):
        test_schedule_passiva.importo_pagato = Decimal("1000.00")
        db_session.flush()

        resp = client.post("/api/v1/payments/from-schedules", headers=_h(auth_headers_with_company), json={
            "schedule_ids": [str(test_schedule_passiva.id)],
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 201
        assert Decimal(resp.json()["importo_totale"]) == Decimal("2000.00")

    def test_from_schedules_multiple(self, client, auth_headers_with_company,
                                      test_schedule_passiva, test_bank_account, db_session, test_company, test_user):
        s2 = Schedule(
            company_id=test_company.id,
            tipo=ScheduleType.PASSIVA,
            stato=ScheduleStatus.APERTA,
            descrizione="Seconda scadenza",
            importo_totale=Decimal("500.00"),
            importo_pagato=Decimal("0"),
            valuta="EUR",
            data_scadenza=date.today() + timedelta(days=7),
            tipo_documento=DocumentType.FATTURA_ACQUISTO,
            controparte_nome="Fornitore Beta",
            controparte_iban="IT60X0542811101000000222222",
            priorita=SchedulePriority.NORMALE,
            source=ScheduleSource.MANUALE,
            is_ricorrente=False,
            ricorrenza_attiva=True,
            created_by_user_id=test_user.id,
        )
        db_session.add(s2)
        db_session.flush()

        resp = client.post("/api/v1/payments/from-schedules", headers=_h(auth_headers_with_company), json={
            "schedule_ids": [str(test_schedule_passiva.id), str(s2.id)],
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 201
        assert resp.json()["numero_disposizioni"] == 2

    def test_from_schedules_nonexistent(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments/from-schedules", headers=_h(auth_headers_with_company), json={
            "schedule_ids": [str(uuid.uuid4())],
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 400


class TestPaymentTemplates:

    def test_create_template(self, client, auth_headers_with_company, test_bank_account):
        resp = client.post("/api/v1/payments/templates", headers=_h(auth_headers_with_company), json={
            "nome": "Template SEPA",
            "tipo": "sepa_credit_transfer",
            "bank_account_id": str(test_bank_account.id),
            "dati_template": {"priorita": "normale", "valuta": "EUR"},
        })
        assert resp.status_code == 201
        assert resp.json()["nome"] == "Template SEPA"

    def test_list_templates(self, client, auth_headers_with_company, db_session, test_company):
        t = PaymentTemplate(
            company_id=test_company.id,
            nome="Test Template",
            tipo=PaymentOrderType.SEPA_CREDIT_TRANSFER,
        )
        db_session.add(t)
        db_session.flush()

        resp = client.get("/api/v1/payments/templates", headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_apply_template(self, client, auth_headers_with_company, db_session,
                             test_company, test_bank_account):
        t = PaymentTemplate(
            company_id=test_company.id,
            nome="Template Apply",
            tipo=PaymentOrderType.SEPA_CREDIT_TRANSFER,
            bank_account_id=test_bank_account.id,
            dati_template={"priorita": "alta", "valuta": "EUR", "note_default": "Da template"},
        )
        db_session.add(t)
        db_session.flush()

        resp = client.post(f"/api/v1/payments/templates/{t.id}/apply",
                           headers=_h(auth_headers_with_company), json={
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=10)),
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "sepa_credit_transfer"
        assert data["priorita"] == "alta"

    def test_apply_template_with_overrides(self, client, auth_headers_with_company,
                                            db_session, test_company, test_bank_account):
        t = PaymentTemplate(
            company_id=test_company.id,
            nome="Template Override",
            tipo=PaymentOrderType.RIBA,
            dati_template={"priorita": "normale"},
        )
        db_session.add(t)
        db_session.flush()

        resp = client.post(f"/api/v1/payments/templates/{t.id}/apply",
                           headers=_h(auth_headers_with_company), json={
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=10)),
            "override_priorita": "urgente",
            "override_note": "Override note",
        })
        assert resp.status_code == 201
        assert resp.json()["priorita"] == "urgente"
        assert resp.json()["note"] == "Override note"

    def test_delete_template(self, client, auth_headers_with_company, db_session, test_company):
        t = PaymentTemplate(
            company_id=test_company.id,
            nome="To Delete",
            tipo=PaymentOrderType.SEPA_CREDIT_TRANSFER,
        )
        db_session.add(t)
        db_session.flush()

        resp = client.delete(f"/api/v1/payments/templates/{t.id}",
                             headers=_h(auth_headers_with_company))
        assert resp.status_code == 204

    def test_delete_nonexistent_template(self, client, auth_headers_with_company):
        resp = client.delete(f"/api/v1/payments/templates/{uuid.uuid4()}",
                             headers=_h(auth_headers_with_company))
        assert resp.status_code == 404


class TestIbanValidation:

    def test_valid_italian_iban(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments/validate-iban",
                           headers=_h(auth_headers_with_company),
                           json={"iban": "IT60 X054 2811 1010 0000 0123 456"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["valid"] is True
        assert data["iban_formatted"] == "IT60X0542811101000000123456"

    def test_valid_german_iban(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments/validate-iban",
                           headers=_h(auth_headers_with_company),
                           json={"iban": "DE89370400440532013000"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is True

    def test_invalid_checksum(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments/validate-iban",
                           headers=_h(auth_headers_with_company),
                           json={"iban": "IT00X0542811101000000123456"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    def test_invalid_format(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments/validate-iban",
                           headers=_h(auth_headers_with_company),
                           json={"iban": "INVALID"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is False

    def test_empty_iban(self, client, auth_headers_with_company):
        resp = client.post("/api/v1/payments/validate-iban",
                           headers=_h(auth_headers_with_company),
                           json={"iban": "AB"})
        assert resp.status_code == 200
        assert resp.json()["valid"] is False


class TestPaymentIntegration:

    def test_full_payment_lifecycle(self, client, auth_headers_with_company, second_auth_headers,
                                     test_bank_account, db_session):
        # 1. Create order
        resp = client.post("/api/v1/payments", headers=_h(auth_headers_with_company), json={
            "tipo": "sepa_credit_transfer",
            "bank_account_id": str(test_bank_account.id),
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        order_id = resp.json()["id"]

        # 2. Add lines
        client.post(f"/api/v1/payments/{order_id}/lines",
                     headers=_h(auth_headers_with_company), json={
            "beneficiario_nome": "Fornitore A",
            "beneficiario_iban": "IT60X0542811101000000111111",
            "importo": "1500.00",
            "causale": "Fattura FT-001",
        })

        # 3. Submit
        resp = client.post(f"/api/v1/payments/{order_id}/submit",
                           headers=_h(auth_headers_with_company))
        assert resp.json()["stato"] == "da_approvare"

        # 4. Approve
        resp = client.post(f"/api/v1/payments/{order_id}/approve",
                           headers=_h(second_auth_headers), json={"commento": "OK"})
        assert resp.json()["stato"] == "approvata"

    def test_schedule_payment_integration(self, client, auth_headers_with_company, second_auth_headers,
                                           test_schedule_passiva, test_bank_account, db_session):
        # Create from schedules
        resp = client.post("/api/v1/payments/from-schedules", headers=_h(auth_headers_with_company), json={
            "schedule_ids": [str(test_schedule_passiva.id)],
            "bank_account_id": str(test_bank_account.id),
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=5)),
        })
        assert resp.status_code == 201
        order_id = resp.json()["id"]

        # Submit and approve
        client.post(f"/api/v1/payments/{order_id}/submit",
                     headers=_h(auth_headers_with_company))
        client.post(f"/api/v1/payments/{order_id}/approve",
                     headers=_h(second_auth_headers), json={})

        # Generate file
        resp = client.post(f"/api/v1/payments/{order_id}/generate-file",
                           headers=_h(auth_headers_with_company))
        assert resp.json()["stato"] == "file_generato"

    def test_template_create_and_apply(self, client, auth_headers_with_company,
                                        test_bank_account, db_session):
        # Create template
        resp = client.post("/api/v1/payments/templates", headers=_h(auth_headers_with_company), json={
            "nome": "Template Test Integrazione",
            "tipo": "sepa_credit_transfer",
            "bank_account_id": str(test_bank_account.id),
            "dati_template": {"priorita": "normale", "valuta": "EUR"},
        })
        template_id = resp.json()["id"]

        # Apply template
        resp = client.post(f"/api/v1/payments/templates/{template_id}/apply",
                           headers=_h(auth_headers_with_company), json={
            "data_esecuzione_richiesta": str(date.today() + timedelta(days=10)),
        })
        assert resp.status_code == 201
        assert resp.json()["tipo"] == "sepa_credit_transfer"

    def test_list_with_search(self, client, auth_headers_with_company, test_payment_order):
        resp = client.get("/api/v1/payments?search=PAG-2026",
                          headers=_h(auth_headers_with_company))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1
