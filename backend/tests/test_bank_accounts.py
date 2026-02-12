import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.core.security import get_password_hash
from app.models import (
    User, UserCompany, UserCompanyStatus, UserRole,
    BankAccount, AccountStatus, AccountType,
)


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


# =====================================================================
# CREATE
# =====================================================================


def test_create_manual_account(client, auth_headers, test_company, test_user_company):
    resp = client.post(
        "/api/v1/bank-accounts",
        json={
            "nickname": "Conto Nuovo",
            "iban": "IT60X0542811101000000123456",
            "currency": "EUR",
            "current_balance": 5000.00,
            "account_type": "checking",
            "color": "#2563eb",
            "bank_name": "Banco BPM",
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nickname"] == "Conto Nuovo"
    assert data["iban"] == "IT60X0542811101000000123456"
    assert data["bank_connection_id"] is None
    assert data["bank_abi"] == "05428"
    assert data["bank_cab"] == "11101"
    assert data["status"] == "active"


def test_create_account_invalid_iban(client, auth_headers, test_company, test_user_company):
    resp = client.post(
        "/api/v1/bank-accounts",
        json={
            "nickname": "Conto Invalido",
            "iban": "IT00X0000000000000000000000",
            "currency": "EUR",
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 422


def test_create_account_valid_iban(client, auth_headers, test_company, test_user_company):
    resp = client.post(
        "/api/v1/bank-accounts",
        json={
            "nickname": "Conto Valido",
            "iban": "IT60X0542811101000000123456",
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 201


# =====================================================================
# GET
# =====================================================================


def test_get_account(client, auth_headers, test_company, test_user_company, test_bank_account):
    resp = client.get(
        f"/api/v1/bank-accounts/{test_bank_account.id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == str(test_bank_account.id)
    assert data["nickname"] == "Conto Test"


def test_get_account_not_found(client, auth_headers, test_company, test_user_company):
    resp = client.get(
        f"/api/v1/bank-accounts/{uuid.uuid4()}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 404


def test_get_account_wrong_company(client, db_session, auth_headers, test_company, test_user_company):
    # Create account for a different company
    other_company = type(test_company)(name="Other SRL", vat_number="11223344556", country="IT")
    db_session.add(other_company)
    db_session.flush()

    other_account = BankAccount(
        company_id=other_company.id,
        nickname="Altro Conto",
        currency="EUR",
        status=AccountStatus.ACTIVE,
    )
    db_session.add(other_account)
    db_session.flush()

    resp = client.get(
        f"/api/v1/bank-accounts/{other_account.id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 404


def test_list_accounts(client, auth_headers, test_company, test_user_company, test_bank_account):
    resp = client.get(
        "/api/v1/bank-accounts",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


# =====================================================================
# UPDATE
# =====================================================================


def test_update_account(client, auth_headers, test_company, test_user_company, test_bank_account):
    resp = client.patch(
        f"/api/v1/bank-accounts/{test_bank_account.id}",
        json={"nickname": "Conto Aggiornato", "color": "#dc2626"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["nickname"] == "Conto Aggiornato"
    assert data["color"] == "#dc2626"


# =====================================================================
# DELETE (soft)
# =====================================================================


def test_delete_account(client, auth_headers, test_company, test_user_company, test_bank_account):
    resp = client.delete(
        f"/api/v1/bank-accounts/{test_bank_account.id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 204

    # Verify it's closed, not deleted
    resp2 = client.get(
        f"/api/v1/bank-accounts/{test_bank_account.id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "closed"


# =====================================================================
# BALANCE UPDATE
# =====================================================================


def test_update_balance_allowed(client, auth_headers, test_company, test_user_company, test_bank_account):
    resp = client.patch(
        f"/api/v1/bank-accounts/{test_bank_account.id}/balance",
        json={"current_balance": 12000.00, "available_balance": 11500.00},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert float(data["current_balance"]) == 12000.00
    assert float(data["available_balance"]) == 11500.00


def test_update_balance_denied(client, db_session, auth_headers, test_company, test_user_company):
    # Create account with allow_balance_change=False
    account = BankAccount(
        company_id=test_company.id,
        nickname="Conto Bloccato",
        currency="EUR",
        current_balance=Decimal("5000.00"),
        status=AccountStatus.ACTIVE,
        allow_balance_change=False,
    )
    db_session.add(account)
    db_session.flush()

    resp = client.patch(
        f"/api/v1/bank-accounts/{account.id}/balance",
        json={"current_balance": 999.00},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 403


# =====================================================================
# HIDE / UNHIDE
# =====================================================================


def test_hide_unhide_account(client, auth_headers, test_company, test_user_company, test_bank_account):
    # Hide
    resp = client.post(
        f"/api/v1/bank-accounts/{test_bank_account.id}/hide",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "hidden"
    assert resp.json()["hidden_at"] is not None

    # Unhide
    resp2 = client.post(
        f"/api/v1/bank-accounts/{test_bank_account.id}/unhide",
        headers=_headers(auth_headers, test_company),
    )
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "active"
    assert resp2.json()["hidden_at"] is None


# =====================================================================
# SUMMARY
# =====================================================================


def test_summary_aggregation(client, db_session, auth_headers, test_company, test_user_company):
    # Create 2 active accounts
    for i, bal in enumerate([Decimal("10000.00"), Decimal("5000.00")]):
        db_session.add(BankAccount(
            company_id=test_company.id, nickname=f"Conto {i}", currency="EUR",
            current_balance=bal, available_balance=bal - Decimal("100"),
            status=AccountStatus.ACTIVE,
        ))
    db_session.flush()

    resp = client.get(
        "/api/v1/bank-accounts/summary",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["count"] == 2
    assert float(data["total_current_balance"]) == 15000.00


def test_summary_excludes_hidden(client, db_session, auth_headers, test_company, test_user_company):
    from datetime import datetime, timezone
    db_session.add(BankAccount(
        company_id=test_company.id, nickname="Visibile", currency="EUR",
        current_balance=Decimal("10000.00"), available_balance=Decimal("10000.00"),
        status=AccountStatus.ACTIVE,
    ))
    db_session.add(BankAccount(
        company_id=test_company.id, nickname="Nascosto", currency="EUR",
        current_balance=Decimal("5000.00"), available_balance=Decimal("5000.00"),
        status=AccountStatus.HIDDEN, hidden_at=datetime.now(timezone.utc),
    ))
    db_session.flush()

    resp = client.get(
        "/api/v1/bank-accounts/summary",
        headers=_headers(auth_headers, test_company),
    )
    data = resp.json()
    assert data["count"] == 1
    assert float(data["total_current_balance"]) == 10000.00


def test_summary_excludes_ignored(client, db_session, auth_headers, test_company, test_user_company):
    db_session.add(BankAccount(
        company_id=test_company.id, nickname="Incluso", currency="EUR",
        current_balance=Decimal("8000.00"), available_balance=Decimal("8000.00"),
        status=AccountStatus.ACTIVE, ignore_balance=False,
    ))
    db_session.add(BankAccount(
        company_id=test_company.id, nickname="Escluso", currency="EUR",
        current_balance=Decimal("2000.00"), available_balance=Decimal("2000.00"),
        status=AccountStatus.ACTIVE, ignore_balance=True,
    ))
    db_session.flush()

    resp = client.get(
        "/api/v1/bank-accounts/summary",
        headers=_headers(auth_headers, test_company),
    )
    data = resp.json()
    assert data["count"] == 1
    assert float(data["total_current_balance"]) == 8000.00


# =====================================================================
# DEFAULT CONSTRAINT
# =====================================================================


def test_default_unique_constraint(client, auth_headers, test_company, test_user_company):
    # Create first as default
    resp1 = client.post(
        "/api/v1/bank-accounts",
        json={"nickname": "Default 1", "is_default": True, "iban": "IT60X0542811101000000123456"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp1.status_code == 201
    id1 = resp1.json()["id"]

    # Create second as default — should unset first
    resp2 = client.post(
        "/api/v1/bank-accounts",
        json={"nickname": "Default 2", "is_default": True, "iban": "IT60X0542811101000000123456"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp2.status_code == 201

    # Verify first is no longer default
    resp3 = client.get(
        f"/api/v1/bank-accounts/{id1}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp3.json()["is_default"] is False


# =====================================================================
# BALANCE HISTORY
# =====================================================================


def test_balance_history_create(client, auth_headers, test_company, test_user_company, test_bank_account):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    resp = client.post(
        f"/api/v1/bank-accounts/{test_bank_account.id}/balances",
        json={
            "balance_date": yesterday,
            "current_balance": 9000.00,
            "available_balance": 8500.00,
            "source": "manual",
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["balance_date"] == yesterday
    assert float(data["current_balance"]) == 9000.00


def test_balance_history_list(client, auth_headers, test_company, test_user_company, test_bank_account, test_bank_account_balance):
    resp = client.get(
        f"/api/v1/bank-accounts/{test_bank_account.id}/balances",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_balance_chart(client, auth_headers, test_company, test_user_company, test_bank_account, test_bank_account_balance):
    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()
    resp = client.get(
        f"/api/v1/bank-accounts/{test_bank_account.id}/balance-chart?date_from={week_ago}&date_to={today}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


# =====================================================================
# ACCESSES
# =====================================================================


def test_access_crud(client, db_session, auth_headers, test_company, test_user_company, test_bank_account, test_user):
    headers = _headers(auth_headers, test_company)

    # Create second user
    user2 = User(
        email="access@example.com",
        password_hash=get_password_hash("Access1234!"),
        first_name="Access",
        last_name="User",
        email_verified=True,
        is_active=True,
    )
    db_session.add(user2)
    db_session.flush()

    # Create access
    resp = client.post(
        f"/api/v1/bank-accounts/{test_bank_account.id}/accesses",
        json={"user_id": str(user2.id), "access_level": "read"},
        headers=headers,
    )
    assert resp.status_code == 201
    access_id = resp.json()["id"]
    assert resp.json()["user_email"] == "access@example.com"

    # List accesses
    resp2 = client.get(
        f"/api/v1/bank-accounts/{test_bank_account.id}/accesses",
        headers=headers,
    )
    assert resp2.status_code == 200
    assert len(resp2.json()) >= 1

    # Update access
    resp3 = client.patch(
        f"/api/v1/bank-accounts/{test_bank_account.id}/accesses/{access_id}",
        json={"access_level": "write"},
        headers=headers,
    )
    assert resp3.status_code == 200
    assert resp3.json()["access_level"] == "write"

    # Delete access
    resp4 = client.delete(
        f"/api/v1/bank-accounts/{test_bank_account.id}/accesses/{access_id}",
        headers=headers,
    )
    assert resp4.status_code == 204


# =====================================================================
# ROLE-BASED ACCESS
# =====================================================================


def test_viewer_cannot_create(client, db_session, test_company):
    # Create viewer user
    viewer = User(
        email="viewer@example.com",
        password_hash=get_password_hash("Viewer1234!"),
        first_name="Viewer",
        last_name="User",
        email_verified=True,
        is_active=True,
    )
    db_session.add(viewer)
    db_session.flush()

    uc = UserCompany(
        user_id=viewer.id,
        company_id=test_company.id,
        role=UserRole.VIEWER,
        status=UserCompanyStatus.ACTIVE,
    )
    db_session.add(uc)
    db_session.flush()

    # Login as viewer
    resp = client.post("/api/v1/auth/login", json={"email": "viewer@example.com", "password": "Viewer1234!"})
    viewer_headers = {
        "Authorization": f"Bearer {resp.json()['access_token']}",
        "X-Company-ID": str(test_company.id),
    }

    # Try to create — should fail
    resp2 = client.post(
        "/api/v1/bank-accounts",
        json={"nickname": "Tentativo", "currency": "EUR"},
        headers=viewer_headers,
    )
    assert resp2.status_code == 403


def test_editor_can_create(client, db_session, test_company):
    # Create editor user
    editor = User(
        email="editor_ba@example.com",
        password_hash=get_password_hash("Editor1234!"),
        first_name="Editor",
        last_name="BA",
        email_verified=True,
        is_active=True,
    )
    db_session.add(editor)
    db_session.flush()

    uc = UserCompany(
        user_id=editor.id,
        company_id=test_company.id,
        role=UserRole.EDITOR,
        status=UserCompanyStatus.ACTIVE,
    )
    db_session.add(uc)
    db_session.flush()

    resp = client.post("/api/v1/auth/login", json={"email": "editor_ba@example.com", "password": "Editor1234!"})
    editor_headers = {
        "Authorization": f"Bearer {resp.json()['access_token']}",
        "X-Company-ID": str(test_company.id),
    }

    resp2 = client.post(
        "/api/v1/bank-accounts",
        json={"nickname": "Conto Editor", "currency": "EUR"},
        headers=editor_headers,
    )
    assert resp2.status_code == 201


def test_editor_cannot_delete(client, db_session, test_company):
    # Create editor
    editor = User(
        email="editor_del@example.com",
        password_hash=get_password_hash("Editor1234!"),
        first_name="Editor",
        last_name="Del",
        email_verified=True,
        is_active=True,
    )
    db_session.add(editor)
    db_session.flush()

    uc = UserCompany(
        user_id=editor.id,
        company_id=test_company.id,
        role=UserRole.EDITOR,
        status=UserCompanyStatus.ACTIVE,
    )
    db_session.add(uc)
    db_session.flush()

    # Create account as editor
    resp = client.post("/api/v1/auth/login", json={"email": "editor_del@example.com", "password": "Editor1234!"})
    editor_headers = {
        "Authorization": f"Bearer {resp.json()['access_token']}",
        "X-Company-ID": str(test_company.id),
    }

    create_resp = client.post(
        "/api/v1/bank-accounts",
        json={"nickname": "Da Eliminare", "currency": "EUR"},
        headers=editor_headers,
    )
    account_id = create_resp.json()["id"]

    # Try delete as editor — should fail (requires ADMIN)
    resp2 = client.delete(
        f"/api/v1/bank-accounts/{account_id}",
        headers=editor_headers,
    )
    assert resp2.status_code == 403
