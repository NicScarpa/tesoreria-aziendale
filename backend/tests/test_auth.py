def test_login_ok(client, test_user, test_user_company):
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "Test1234!"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    resp = client.post("/api/v1/auth/login", json={"email": "test@example.com", "password": "wrong"})
    assert resp.status_code == 401


def test_login_nonexistent_user(client):
    resp = client.post("/api/v1/auth/login", json={"email": "nobody@example.com", "password": "Test1234!"})
    assert resp.status_code == 401


def test_register_ok(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "new@example.com",
        "password": "NewPass1!",
        "first_name": "New",
        "last_name": "User",
        "company_name": "New Company",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_register_duplicate_email(client, test_user):
    resp = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "NewPass1!",
        "first_name": "Dup",
        "last_name": "User",
        "company_name": "Dup Company",
    })
    assert resp.status_code == 409


def test_register_weak_password(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "weak@example.com",
        "password": "short",
        "first_name": "Weak",
        "last_name": "User",
        "company_name": "Weak Co",
    })
    assert resp.status_code == 422


def test_refresh_token_ok(client, auth_headers):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": auth_headers["_refresh_token"]})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    # Old refresh should be revoked (rotated)
    resp2 = client.post("/api/v1/auth/refresh", json={"refresh_token": auth_headers["_refresh_token"]})
    assert resp2.status_code == 401


def test_refresh_invalid_token(client):
    resp = client.post("/api/v1/auth/refresh", json={"refresh_token": "invalid_token_123"})
    assert resp.status_code == 401


def test_logout_ok(client, auth_headers):
    resp = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": auth_headers["_refresh_token"]},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200


def test_logout_no_auth(client):
    resp = client.post("/api/v1/auth/logout", json={"refresh_token": "whatever"})
    assert resp.status_code == 401


def test_get_me(client, auth_headers):
    resp = client.get("/api/v1/users/me", headers={"Authorization": auth_headers["Authorization"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "test@example.com"
    assert data["first_name"] == "Test"
    assert len(data["companies"]) == 1


def test_update_me(client, auth_headers):
    resp = client.patch(
        "/api/v1/users/me",
        json={"first_name": "Updated"},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200
    assert resp.json()["first_name"] == "Updated"


def test_change_password_ok(client, auth_headers):
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "Test1234!", "new_password": "NewPass99!"},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 200


def test_change_password_wrong_current(client, auth_headers):
    resp = client.post(
        "/api/v1/auth/change-password",
        json={"current_password": "wrongwrong", "new_password": "NewPass99!"},
        headers={"Authorization": auth_headers["Authorization"]},
    )
    assert resp.status_code == 400


def test_forgot_password(client, test_user):
    resp = client.post("/api/v1/auth/forgot-password", json={"email": "test@example.com"})
    assert resp.status_code == 200
    # Anche con email inesistente ritorna 200
    resp2 = client.post("/api/v1/auth/forgot-password", json={"email": "nonexistent@example.com"})
    assert resp2.status_code == 200
