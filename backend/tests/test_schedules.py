"""Test suite for Module 7: Schedule Management."""
import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.models import (
    Schedule, SchedulePayment, ScheduleReminder, ScheduleAttachment,
    ScheduleType, ScheduleStatus, DocumentType, SchedulePriority,
    ScheduleSource, PaymentMethod, RecurrenceType,
    ExpectedTransaction, ExpectedTransactionStatus, ExpectedTransactionSource,
    Reconciliation, ReconciliationLine, ReconciliationLineType,
    ReconciliationType, ReconciliationStatus,
)


def _h(auth_headers: dict) -> dict:
    """Auth + company headers shortcut."""
    return {
        "Authorization": auth_headers["Authorization"],
        "X-Company-ID": auth_headers.get("_company_id", ""),
    }


@pytest.fixture()
def auth_headers_with_company(auth_headers, test_company):
    """Add company ID to auth headers."""
    headers = dict(auth_headers)
    headers["_company_id"] = str(test_company.id)
    headers["X-Company-ID"] = str(test_company.id)
    return headers


@pytest.fixture()
def test_schedule(db_session, test_company, test_bank_account, test_user) -> Schedule:
    s = Schedule(
        company_id=test_company.id,
        tipo=ScheduleType.PASSIVA,
        stato=ScheduleStatus.APERTA,
        descrizione="Fattura test fornitore",
        importo_totale=Decimal("2500.00"),
        importo_pagato=Decimal("0"),
        valuta="EUR",
        data_scadenza=date.today() + timedelta(days=10),
        data_emissione=date.today() - timedelta(days=5),
        tipo_documento=DocumentType.FATTURA_ACQUISTO,
        numero_documento="FT-2026/TEST",
        riferimento_documento="FT-2026/TEST",
        controparte_nome="Fornitore Test SRL",
        controparte_iban="IT60X0542811101000000111111",
        bank_account_id=test_bank_account.id,
        priorita=SchedulePriority.NORMALE,
        metodo_pagamento=PaymentMethod.BONIFICO,
        source=ScheduleSource.MANUALE,
        is_ricorrente=False,
        ricorrenza_attiva=True,
        created_by_user_id=test_user.id,
    )
    db_session.add(s)
    db_session.flush()
    return s


@pytest.fixture()
def test_schedule_attiva(db_session, test_company, test_bank_account, test_user) -> Schedule:
    s = Schedule(
        company_id=test_company.id,
        tipo=ScheduleType.ATTIVA,
        stato=ScheduleStatus.APERTA,
        descrizione="Fattura vendita test",
        importo_totale=Decimal("5000.00"),
        importo_pagato=Decimal("0"),
        valuta="EUR",
        data_scadenza=date.today() + timedelta(days=15),
        tipo_documento=DocumentType.FATTURA_VENDITA,
        numero_documento="FV-2026/TEST",
        controparte_nome="Cliente Test SpA",
        bank_account_id=test_bank_account.id,
        priorita=SchedulePriority.ALTA,
        source=ScheduleSource.MANUALE,
        is_ricorrente=False,
        ricorrenza_attiva=True,
        created_by_user_id=test_user.id,
    )
    db_session.add(s)
    db_session.flush()
    return s


@pytest.fixture()
def test_schedule_ricorrente(db_session, test_company, test_bank_account, test_user) -> Schedule:
    s = Schedule(
        company_id=test_company.id,
        tipo=ScheduleType.PASSIVA,
        stato=ScheduleStatus.APERTA,
        descrizione="Affitto ufficio mensile",
        importo_totale=Decimal("1500.00"),
        importo_pagato=Decimal("0"),
        valuta="EUR",
        data_scadenza=date.today() + timedelta(days=5),
        tipo_documento=DocumentType.AFFITTO,
        controparte_nome="Immobiliare Test SRL",
        bank_account_id=test_bank_account.id,
        priorita=SchedulePriority.NORMALE,
        metodo_pagamento=PaymentMethod.BONIFICO,
        source=ScheduleSource.MANUALE,
        is_ricorrente=True,
        ricorrenza_tipo=RecurrenceType.MENSILE,
        ricorrenza_attiva=True,
        created_by_user_id=test_user.id,
    )
    db_session.add(s)
    db_session.flush()
    return s


# --- CRUD Tests ---

class TestScheduleCRUD:
    def test_create_schedule(self, client, auth_headers_with_company, test_bank_account):
        resp = client.post(
            "/api/v1/schedules",
            headers=auth_headers_with_company,
            json={
                "tipo": "passiva",
                "descrizione": "Nuova fattura fornitore",
                "importo_totale": 1200.50,
                "data_scadenza": str(date.today() + timedelta(days=30)),
                "tipo_documento": "fattura_acquisto",
                "controparte_nome": "Fornitore Nuovo SRL",
                "bank_account_id": str(test_bank_account.id),
                "priorita": "alta",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["tipo"] == "passiva"
        assert data["descrizione"] == "Nuova fattura fornitore"
        assert float(data["importo_totale"]) == 1200.50
        assert float(data["importo_pagato"]) == 0
        assert float(data["importo_residuo"]) == 1200.50
        assert data["stato"] == "aperta"
        assert data["expected_transaction_id"] is not None

    def test_create_schedule_generates_expected_transaction(self, client, auth_headers_with_company, db_session):
        resp = client.post(
            "/api/v1/schedules",
            headers=auth_headers_with_company,
            json={
                "tipo": "attiva",
                "descrizione": "Fattura vendita",
                "importo_totale": 3000.00,
                "data_scadenza": str(date.today() + timedelta(days=10)),
                "tipo_documento": "fattura_vendita",
                "controparte_nome": "Cliente Test",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        et_id = data["expected_transaction_id"]
        assert et_id is not None

        # Verify ExpectedTransaction
        et = db_session.get(ExpectedTransaction, uuid.UUID(et_id))
        assert et is not None
        assert et.type.value == "expected_inflow"
        assert et.expected_amount == Decimal("3000.00")
        assert et.source == ExpectedTransactionSource.SCHEDULE

    def test_list_schedules(self, client, auth_headers_with_company, test_schedule, test_schedule_attiva):
        resp = client.get("/api/v1/schedules", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 2
        assert len(data["items"]) >= 2
        assert "totals" in data

    def test_list_schedules_filter_stato(self, client, auth_headers_with_company, test_schedule):
        resp = client.get("/api/v1/schedules?stato=aperta", headers=auth_headers_with_company)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["stato"] == "aperta"

    def test_list_schedules_filter_tipo(self, client, auth_headers_with_company, test_schedule, test_schedule_attiva):
        resp = client.get("/api/v1/schedules?tipo=attiva", headers=auth_headers_with_company)
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["tipo"] == "attiva"

    def test_list_schedules_search(self, client, auth_headers_with_company, test_schedule):
        resp = client.get("/api/v1/schedules?search=fornitore", headers=auth_headers_with_company)
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    def test_get_schedule(self, client, auth_headers_with_company, test_schedule):
        resp = client.get(f"/api/v1/schedules/{test_schedule.id}", headers=auth_headers_with_company)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(test_schedule.id)

    def test_get_schedule_not_found(self, client, auth_headers_with_company):
        resp = client.get(f"/api/v1/schedules/{uuid.uuid4()}", headers=auth_headers_with_company)
        assert resp.status_code == 404

    def test_update_schedule(self, client, auth_headers_with_company, test_schedule):
        resp = client.put(
            f"/api/v1/schedules/{test_schedule.id}",
            headers=auth_headers_with_company,
            json={"descrizione": "Descrizione aggiornata", "priorita": "urgente"},
        )
        assert resp.status_code == 200
        assert resp.json()["descrizione"] == "Descrizione aggiornata"
        assert resp.json()["priorita"] == "urgente"

    def test_delete_schedule(self, client, auth_headers_with_company, test_schedule):
        resp = client.delete(f"/api/v1/schedules/{test_schedule.id}", headers=auth_headers_with_company)
        assert resp.status_code == 204

        resp = client.get(f"/api/v1/schedules/{test_schedule.id}", headers=auth_headers_with_company)
        assert resp.status_code == 404

    def test_create_schedule_invalid_importo(self, client, auth_headers_with_company):
        resp = client.post(
            "/api/v1/schedules",
            headers=auth_headers_with_company,
            json={
                "tipo": "passiva",
                "descrizione": "Test",
                "importo_totale": -100,
                "data_scadenza": str(date.today()),
            },
        )
        assert resp.status_code == 422


# --- Status Tests ---

class TestScheduleStatus:
    def test_update_status(self, client, auth_headers_with_company, test_schedule):
        resp = client.put(
            f"/api/v1/schedules/{test_schedule.id}/stato",
            headers=auth_headers_with_company,
            json={"stato": "annullata"},
        )
        assert resp.status_code == 200
        assert resp.json()["stato"] == "annullata"


# --- Payment Tests ---

class TestSchedulePayments:
    def test_create_payment_partial(self, client, auth_headers_with_company, test_schedule):
        resp = client.post(
            f"/api/v1/schedules/{test_schedule.id}/payments",
            headers=auth_headers_with_company,
            json={
                "importo": 1000.00,
                "data_pagamento": str(date.today()),
                "metodo": "bonifico",
                "riferimento": "BON-001",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert float(data["importo"]) == 1000.00

        # Verify schedule updated
        sched = client.get(f"/api/v1/schedules/{test_schedule.id}", headers=auth_headers_with_company).json()
        assert float(sched["importo_pagato"]) == 1000.00
        assert sched["stato"] == "parzialmente_pagata"

    def test_create_payment_total(self, client, auth_headers_with_company, test_schedule):
        resp = client.post(
            f"/api/v1/schedules/{test_schedule.id}/payments",
            headers=auth_headers_with_company,
            json={
                "importo": 2500.00,
                "data_pagamento": str(date.today()),
            },
        )
        assert resp.status_code == 201

        sched = client.get(f"/api/v1/schedules/{test_schedule.id}", headers=auth_headers_with_company).json()
        assert float(sched["importo_pagato"]) == 2500.00
        assert sched["stato"] == "pagata"

    def test_delete_payment_recalculates(self, client, auth_headers_with_company, test_schedule):
        # Create payment
        pay_resp = client.post(
            f"/api/v1/schedules/{test_schedule.id}/payments",
            headers=auth_headers_with_company,
            json={"importo": 1500.00, "data_pagamento": str(date.today())},
        )
        payment_id = pay_resp.json()["id"]

        # Delete payment
        resp = client.delete(
            f"/api/v1/schedules/{test_schedule.id}/payments/{payment_id}",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 204

        # Verify recalculation
        sched = client.get(f"/api/v1/schedules/{test_schedule.id}", headers=auth_headers_with_company).json()
        assert float(sched["importo_pagato"]) == 0
        assert sched["stato"] == "aperta"

    def test_list_payments(self, client, auth_headers_with_company, test_schedule):
        client.post(
            f"/api/v1/schedules/{test_schedule.id}/payments",
            headers=auth_headers_with_company,
            json={"importo": 500.00, "data_pagamento": str(date.today())},
        )
        resp = client.get(f"/api/v1/schedules/{test_schedule.id}/payments", headers=auth_headers_with_company)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


# --- Recurrence Tests ---

class TestScheduleRecurrence:
    def test_generate_next_occurrence(self, client, auth_headers_with_company, test_schedule_ricorrente):
        resp = client.post(
            f"/api/v1/schedules/{test_schedule_ricorrente.id}/generate-next",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 201
        child = resp.json()
        assert child["ricorrenza_parent_id"] == str(test_schedule_ricorrente.id)
        assert child["stato"] == "aperta"
        assert child["expected_transaction_id"] is not None

    def test_generate_next_sequential(self, client, auth_headers_with_company, test_schedule_ricorrente):
        resp1 = client.post(
            f"/api/v1/schedules/{test_schedule_ricorrente.id}/generate-next",
            headers=auth_headers_with_company,
        )
        resp2 = client.post(
            f"/api/v1/schedules/{test_schedule_ricorrente.id}/generate-next",
            headers=auth_headers_with_company,
        )
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        # Each call generates the next occurrence in sequence
        assert resp1.json()["id"] != resp2.json()["id"]
        assert resp1.json()["data_scadenza"] < resp2.json()["data_scadenza"]

    def test_stop_recurrence(self, client, auth_headers_with_company, test_schedule_ricorrente):
        resp = client.put(
            f"/api/v1/schedules/{test_schedule_ricorrente.id}/stop-recurrence",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        assert resp.json()["ricorrenza_attiva"] is False

    def test_list_occurrences(self, client, auth_headers_with_company, test_schedule_ricorrente):
        client.post(
            f"/api/v1/schedules/{test_schedule_ricorrente.id}/generate-next",
            headers=auth_headers_with_company,
        )
        resp = client.get(
            f"/api/v1/schedules/{test_schedule_ricorrente.id}/occurrences",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200
        assert len(resp.json()) >= 2

    def test_generate_non_recurring_fails(self, client, auth_headers_with_company, test_schedule):
        resp = client.post(
            f"/api/v1/schedules/{test_schedule.id}/generate-next",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 400


# --- Reminder Tests ---

class TestScheduleReminders:
    def test_create_reminder(self, client, auth_headers_with_company, test_schedule):
        resp = client.post(
            f"/api/v1/schedules/{test_schedule.id}/reminders",
            headers=auth_headers_with_company,
            json={"giorni_prima": 5, "tipo": "in_app", "messaggio": "Scadenza imminente"},
        )
        assert resp.status_code == 201
        assert resp.json()["giorni_prima"] == 5

    def test_list_reminders(self, client, auth_headers_with_company, test_schedule):
        client.post(
            f"/api/v1/schedules/{test_schedule.id}/reminders",
            headers=auth_headers_with_company,
            json={"giorni_prima": 3},
        )
        resp = client.get(f"/api/v1/schedules/{test_schedule.id}/reminders", headers=auth_headers_with_company)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    def test_delete_reminder(self, client, auth_headers_with_company, test_schedule):
        create_resp = client.post(
            f"/api/v1/schedules/{test_schedule.id}/reminders",
            headers=auth_headers_with_company,
            json={"giorni_prima": 7},
        )
        reminder_id = create_resp.json()["id"]
        resp = client.delete(
            f"/api/v1/schedules/{test_schedule.id}/reminders/{reminder_id}",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 204


# --- Aggregate View Tests ---

class TestScheduleViews:
    def test_summary(self, client, auth_headers_with_company, test_schedule, test_schedule_attiva):
        resp = client.get("/api/v1/schedules/summary", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "totale_attive" in data
        assert "totale_passive" in data
        assert "totale_aperte" in data

    def test_calendar(self, client, auth_headers_with_company, test_schedule):
        today = date.today()
        resp = client.get(
            f"/api/v1/schedules/calendar?month={today.month}&year={today.year}",
            headers=auth_headers_with_company,
        )
        assert resp.status_code == 200

    def test_aging(self, client, auth_headers_with_company, test_schedule, test_schedule_attiva):
        resp = client.get("/api/v1/schedules/aging", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "attive" in data
        assert "passive" in data

    def test_generate_all_recurring(self, client, auth_headers_with_company, test_schedule_ricorrente):
        resp = client.post("/api/v1/schedules/generate-recurring", headers=auth_headers_with_company)
        assert resp.status_code == 200
        data = resp.json()
        assert "generati" in data
        assert "errori" in data

    def test_check_reminders(self, client, auth_headers_with_company, test_schedule):
        # Add a reminder that should fire today
        client.post(
            f"/api/v1/schedules/{test_schedule.id}/reminders",
            headers=auth_headers_with_company,
            json={"giorni_prima": 30},  # due in 10 days, reminder 30 days before = should fire
        )
        resp = client.post("/api/v1/schedules/check-reminders", headers=auth_headers_with_company)
        assert resp.status_code == 200


# --- Integration Test: Schedule ↔ Reconciliation ---

class TestScheduleReconciliationHook:
    def test_reconciliation_updates_schedule(self, db_session, test_company, test_user,
                                              test_bank_account, test_schedule):
        from datetime import datetime, timezone
        from app.services.schedule_expected_service import create_expected_from_schedule

        # Create expected transaction from schedule
        et = create_expected_from_schedule(db_session, test_schedule)
        db_session.flush()

        # Create a matching transaction
        from app.models import Transaction, FlowDirection, TransactionStatus, TransactionType
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("-2500.00"),
            currency="EUR",
            direction=FlowDirection.OUTFLOW,
            transaction_date=date.today(),
            description="Pagamento Fornitore Test SRL",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            counterpart_name="Fornitore Test SRL",
            status=TransactionStatus.BOOKED,
            verified=False,
            reconciliation_status=ReconciliationStatus.UNRECONCILED,
        )
        db_session.add(tx)
        db_session.flush()

        # Simulate confirmed reconciliation
        rec = Reconciliation(
            company_id=test_company.id,
            type=ReconciliationType.MANUAL.value,
            status="confirmed",
            reconciliation_date=datetime.now(timezone.utc),
            confirmed_by_user_id=test_user.id,
            confirmed_at=datetime.now(timezone.utc),
        )
        db_session.add(rec)
        db_session.flush()

        line = ReconciliationLine(
            reconciliation_id=rec.id,
            expected_transaction_id=et.id,
            matched_amount=Decimal("2500.00"),
            line_type=ReconciliationLineType.EXPECTED_MATCH,
        )
        db_session.add(line)
        db_session.flush()
        db_session.refresh(rec)

        # Call the hook
        from app.services.schedule_expected_service import on_reconciliation_confirmed
        on_reconciliation_confirmed(db_session, rec)
        db_session.flush()

        # Verify schedule updated
        db_session.refresh(test_schedule)
        assert test_schedule.importo_pagato == Decimal("2500.00")
        assert test_schedule.stato == ScheduleStatus.PAGATA

    def test_delete_schedule_removes_expected(self, db_session, test_company, test_user,
                                               test_bank_account, test_schedule):
        from app.services.schedule_expected_service import create_expected_from_schedule, delete_expected_for_schedule

        et = create_expected_from_schedule(db_session, test_schedule)
        et_id = et.id
        db_session.flush()

        delete_expected_for_schedule(db_session, test_schedule)
        db_session.flush()

        assert db_session.get(ExpectedTransaction, et_id) is None
