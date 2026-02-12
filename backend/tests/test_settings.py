import uuid

import pytest

from app.core.security import get_password_hash
from app.models import User, UserCompany, UserCompanyStatus, UserRole


@pytest.fixture()
def second_user(db_session) -> User:
    user = User(
        email="second@example.com",
        password_hash=get_password_hash("Second1234!"),
        first_name="Second",
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
        role=UserRole.EDITOR,
        status=UserCompanyStatus.ACTIVE,
    )
    db_session.add(uc)
    db_session.flush()
    return uc


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


# =====================================================================
# COMPANY UPDATE (nuovi campi)
# =====================================================================


def test_update_company_fiscal_fields(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}",
        json={
            "fiscal_regime": "RF01",
            "city": "Milano",
            "postal_code": "20100",
            "province_code": "MI",
            "certified_email": "test@pec.it",
            "destination_code": "ABC1234",
        },
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["fiscal_regime"] == "RF01"
    assert data["city"] == "Milano"
    assert data["postal_code"] == "20100"
    assert data["province_code"] == "MI"
    assert data["certified_email"] == "test@pec.it"
    assert data["destination_code"] == "ABC1234"


def test_validate_vat_number_checksum(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}",
        json={"vat_number": "12345678901"},  # Invalid Luhn
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 422


def test_validate_tax_number_format(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}",
        json={"tax_number": "SHORT"},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 422


def test_validate_sdi_code_format(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}",
        json={"destination_code": "AB"},  # Too short
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 422


# =====================================================================
# COMPANY SETTINGS (JSONB treasury + display)
# =====================================================================


def test_get_company_settings_defaults(client, auth_headers, test_company, test_user_company):
    resp = client.get(
        f"/api/v1/companies/{test_company.id}/settings",
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["treasury_settings"]["advance_notice_days"] == 7
    assert data["treasury_settings"]["auto_categorize"] is False
    assert data["display_settings"]["date_format"] == "DD/MM/YYYY"
    assert data["display_settings"]["timezone"] == "Europe/Rome"


def test_update_treasury_settings(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}/settings",
        json={
            "treasury_settings": {
                "min_cash_threshold": 5000.0,
                "critical_cash_threshold": 1000.0,
                "advance_notice_days": 14,
                "auto_categorize": True,
            }
        },
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["treasury_settings"]["min_cash_threshold"] == 5000.0
    assert data["treasury_settings"]["advance_notice_days"] == 14
    assert data["treasury_settings"]["auto_categorize"] is True


def test_update_display_settings(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}/settings",
        json={
            "display_settings": {
                "date_format": "YYYY-MM-DD",
                "timezone": "UTC",
                "first_day_of_week": 0,
            }
        },
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["display_settings"]["date_format"] == "YYYY-MM-DD"
    assert data["display_settings"]["timezone"] == "UTC"
    assert data["display_settings"]["first_day_of_week"] == 0


# =====================================================================
# MODULES
# =====================================================================


def test_get_modules_empty(client, auth_headers, test_company, test_user_company):
    resp = client.get(
        f"/api/v1/companies/{test_company.id}/modules",
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["features"] == []


def test_update_modules(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        f"/api/v1/companies/{test_company.id}/modules",
        json={"features": ["cashflow", "reconciliation", "payments"]},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "cashflow" in data["features"]
    assert len(data["features"]) == 3


# =====================================================================
# RECONCILIATION RULES CRUD
# =====================================================================


def test_create_reconciliation_rule(client, auth_headers, test_company, test_user_company):
    resp = client.post(
        "/api/v1/reconciliation-rules",
        json={"name": "Regola Base", "match_amount": True, "match_date": True},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Regola Base"
    assert data["match_amount"] is True
    assert data["is_active"] is True


def test_list_reconciliation_rules(client, auth_headers, test_company, test_user_company):
    # Create one first
    client.post(
        "/api/v1/reconciliation-rules",
        json={"name": "Regola Lista"},
        headers=_headers(auth_headers, test_company),
    )
    resp = client.get(
        "/api/v1/reconciliation-rules",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_update_reconciliation_rule(client, auth_headers, test_company, test_user_company):
    # Create
    create_resp = client.post(
        "/api/v1/reconciliation-rules",
        json={"name": "Regola Update"},
        headers=_headers(auth_headers, test_company),
    )
    rule_id = create_resp.json()["id"]

    # Update
    resp = client.patch(
        f"/api/v1/reconciliation-rules/{rule_id}",
        json={"name": "Regola Aggiornata", "priority": 10},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Regola Aggiornata"
    assert data["priority"] == 10


def test_delete_reconciliation_rule(client, auth_headers, test_company, test_user_company):
    # Create
    create_resp = client.post(
        "/api/v1/reconciliation-rules",
        json={"name": "Regola Delete"},
        headers=_headers(auth_headers, test_company),
    )
    rule_id = create_resp.json()["id"]

    # Delete
    resp = client.delete(
        f"/api/v1/reconciliation-rules/{rule_id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 204

    # Verify gone
    resp2 = client.get(
        "/api/v1/reconciliation-rules",
        headers=_headers(auth_headers, test_company),
    )
    ids = [r["id"] for r in resp2.json()]
    assert rule_id not in ids


# =====================================================================
# TEAM
# =====================================================================


def test_list_team_members(client, auth_headers, test_company, test_user_company):
    resp = client.get(
        "/api/v1/company-users",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_invite_member(client, db_session, auth_headers, test_company, test_user_company):
    resp = client.post(
        "/api/v1/company-users/invite",
        json={"email": "newinvite@example.com", "role": "editor"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "invited"
    assert data["role"] == "editor"


def test_invite_duplicate_member(client, db_session, auth_headers, test_company, test_user_company):
    # First invite
    client.post(
        "/api/v1/company-users/invite",
        json={"email": "dup@example.com", "role": "viewer"},
        headers=_headers(auth_headers, test_company),
    )
    # Second invite with same email
    resp = client.post(
        "/api/v1/company-users/invite",
        json={"email": "dup@example.com", "role": "viewer"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 409


def test_update_member_role(client, db_session, auth_headers, test_company, test_user_company, second_user, second_user_company):
    resp = client.patch(
        f"/api/v1/company-users/{second_user_company.id}",
        json={"role": "admin"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "admin"


def test_promote_to_owner_denied(client, db_session, auth_headers, test_company, test_user_company, second_user, second_user_company):
    resp = client.patch(
        f"/api/v1/company-users/{second_user_company.id}",
        json={"role": "owner"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 403


def test_suspend_member(client, db_session, auth_headers, test_company, test_user_company, second_user, second_user_company):
    resp = client.patch(
        f"/api/v1/company-users/{second_user_company.id}",
        json={"status": "suspended"},
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "suspended"


def test_remove_member(client, db_session, auth_headers, test_company, test_user_company, second_user, second_user_company):
    resp = client.delete(
        f"/api/v1/company-users/{second_user_company.id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 204


def test_no_self_remove(client, auth_headers, test_user_company, test_company):
    resp = client.delete(
        f"/api/v1/company-users/{test_user_company.id}",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 400


def test_transfer_ownership(client, db_session, auth_headers, test_company, test_user_company, second_user, second_user_company):
    resp = client.post(
        "/api/v1/company-users/transfer-ownership",
        json={
            "target_user_id": str(second_user.id),
            "password": "Test1234!",
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200


def test_transfer_ownership_wrong_password(client, db_session, auth_headers, test_company, test_user_company, second_user, second_user_company):
    resp = client.post(
        "/api/v1/company-users/transfer-ownership",
        json={
            "target_user_id": str(second_user.id),
            "password": "WrongPassword!",
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 403


# =====================================================================
# NOTIFICATIONS
# =====================================================================


def test_get_notification_preferences(client, auth_headers, test_company, test_user_company):
    resp = client.get(
        "/api/v1/notification-preferences",
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 8  # All NotificationType values


def test_update_notification_preferences(client, auth_headers, test_company, test_user_company):
    resp = client.patch(
        "/api/v1/notification-preferences",
        json={
            "preferences": [
                {"notification_type": "low_balance", "in_app": True, "email": True},
                {"notification_type": "sync_error", "in_app": False, "email": True},
            ]
        },
        headers=_headers(auth_headers, test_company),
    )
    assert resp.status_code == 200
    data = resp.json()
    # Find specific prefs
    low_balance = next(p for p in data if p["notification_type"] == "low_balance")
    assert low_balance["email"] is True
    sync_error = next(p for p in data if p["notification_type"] == "sync_error")
    assert sync_error["in_app"] is False
    assert sync_error["email"] is True
