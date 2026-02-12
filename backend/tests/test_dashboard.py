"""Tests for Module 10: Dashboard."""
import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.models import (
    BankAccount, AccountStatus, AccountType, BankAccountBalance, BalanceSource,
    Transaction, FlowDirection, TransactionStatus, TransactionType,
    CashFlowAlert, CashFlowAlertType, AlertStatus,
    DashboardWidget, DashboardSnapshot, WidgetType, WidgetSize,
)
from app.services import dashboard_service


# --- Fixtures ---

@pytest.fixture()
def auth_headers_with_company(client, test_user, test_user_company, test_company) -> dict:
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Test1234!"})
    tokens = resp.json()
    return {
        "Authorization": f"Bearer {tokens['access_token']}",
        "X-Company-ID": str(test_company.id),
    }


@pytest.fixture()
def dashboard_data(db_session, test_company, test_user, test_bank_account):
    """Create minimal dashboard test data."""
    today = date.today()

    # Enough transactions to trigger "riconcilia" quick action (threshold > 10)
    for i in range(8):
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("1000.00"),
            currency="EUR",
            direction=FlowDirection.INFLOW,
            transaction_date=today - timedelta(days=i % 5),
            description=f"Incasso test {i}",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            status=TransactionStatus.BOOKED,
            verified=False,
        )
        db_session.add(tx)

    for i in range(5):
        tx = Transaction(
            company_id=test_company.id,
            bank_account_id=test_bank_account.id,
            amount=Decimal("-800.00"),
            currency="EUR",
            direction=FlowDirection.OUTFLOW,
            transaction_date=today - timedelta(days=i % 5),
            description=f"Pagamento test {i}",
            transaction_type=TransactionType.CREDIT_TRANSFER,
            status=TransactionStatus.BOOKED,
            verified=False,
        )
        db_session.add(tx)

    # An active alert
    alert = CashFlowAlert(
        company_id=test_company.id,
        tipo=CashFlowAlertType.SOTTO_SOGLIA_MINIMA,
        data_prevista=today + timedelta(days=10),
        saldo_previsto=Decimal("5000.00"),
        soglia=Decimal("10000.00"),
        messaggio="Saldo sotto soglia test",
        stato=AlertStatus.ATTIVO,
    )
    db_session.add(alert)

    # A few snapshots
    for i in range(10):
        snap = DashboardSnapshot(
            company_id=test_company.id,
            data=today - timedelta(days=i),
            saldo_totale=Decimal("10000.00") + Decimal(str(i * 100)),
            entrate_giorno=Decimal("500.00"),
            uscite_giorno=Decimal("300.00"),
            movimenti_non_riconciliati=3,
            scadenze_scadute_importo=Decimal("0"),
            scadenze_scadute_conteggio=0,
            pagamenti_da_approvare=0,
            previsione_30gg=Decimal("12000.00"),
            alert_attivi=1,
        )
        db_session.add(snap)

    db_session.flush()


# --- Test GET /dashboard ---

def test_get_dashboard_full(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()

    # Verify all sections present
    assert "saldi" in data
    assert "cash_flow" in data
    assert "entrate_uscite" in data
    assert "scadenze" in data
    assert "riconciliazione" in data
    assert "pagamenti" in data
    assert "alert" in data
    assert "attivita_recenti" in data
    assert "quick_actions" in data
    assert "aggiornato_a" in data


def test_get_dashboard_saldi_section(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard", headers=auth_headers_with_company)
    assert resp.status_code == 200
    saldi = resp.json()["saldi"]

    assert "totale" in saldi
    assert "disponibile" in saldi
    assert "conti" in saldi
    assert len(saldi["conti"]) >= 1


def test_get_dashboard_alert_section(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard", headers=auth_headers_with_company)
    assert resp.status_code == 200
    alert = resp.json()["alert"]

    assert alert["totale"] >= 1
    assert len(alert["items"]) >= 1
    assert alert["items"][0]["tipo"] == "sotto_soglia_minima"


def test_get_dashboard_401_no_token(client):
    resp = client.get("/api/v1/dashboard")
    assert resp.status_code == 401


def test_get_dashboard_400_no_company(client, test_user):
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Test1234!"})
    tokens = resp.json()
    resp = client.get("/api/v1/dashboard", headers={
        "Authorization": f"Bearer {tokens['access_token']}",
    })
    assert resp.status_code == 400


# --- Test GET /dashboard/section/{section} ---

def test_get_dashboard_section_saldi(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard/section/saldi", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert "totale" in data
    assert "conti" in data


def test_get_dashboard_section_invalid(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard/section/nonexistent", headers=auth_headers_with_company)
    assert resp.status_code == 400


# --- Test Widget CRUD ---

def test_get_widgets_creates_defaults(client, auth_headers_with_company):
    resp = client.get("/api/v1/dashboard/widgets", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10  # 10 default widgets


def test_update_widgets(client, auth_headers_with_company):
    # First get defaults
    client.get("/api/v1/dashboard/widgets", headers=auth_headers_with_company)

    # Update with custom layout
    resp = client.put("/api/v1/dashboard/widgets", headers=auth_headers_with_company, json={
        "widgets": [
            {"widget_type": "saldo_totale", "posizione": 0, "colonna": 0, "dimensione": "large", "visibile": True},
            {"widget_type": "scadenze", "posizione": 1, "colonna": 0, "dimensione": "medium", "visibile": True},
        ]
    })
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2


def test_reset_widgets(client, auth_headers_with_company):
    # Update to 2 widgets
    client.put("/api/v1/dashboard/widgets", headers=auth_headers_with_company, json={
        "widgets": [
            {"widget_type": "saldo_totale", "posizione": 0, "colonna": 0, "dimensione": "large", "visibile": True},
        ]
    })

    # Reset
    resp = client.post("/api/v1/dashboard/widgets/reset", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10  # Back to defaults


# --- Test Trend ---

def test_get_trend(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard/trend?kpi=saldo_totale&periodo=30g", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert data["kpi"] == "saldo_totale"
    assert "punti" in data
    assert "trend" in data


# --- Test Snapshot ---

def test_generate_snapshot(client, auth_headers_with_company, dashboard_data):
    resp = client.post("/api/v1/dashboard/snapshot", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert "saldo_totale" in data
    assert "data" in data


def test_get_snapshots(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard/snapshots", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1


# --- Test Quick Actions ---

def test_get_quick_actions(client, auth_headers_with_company, dashboard_data):
    resp = client.get("/api/v1/dashboard/quick-actions", headers=auth_headers_with_company)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    # Should have "riconcilia" action since we have unverified transactions
    actions = [a["azione"] for a in data]
    assert "riconcilia" in actions
