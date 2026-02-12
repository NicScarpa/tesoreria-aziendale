"""Test per il modulo categorie e sottocategorie."""


def _headers(auth_headers, test_company):
    return {**auth_headers, "X-Company-ID": str(test_company.id)}


class TestListCategories:
    def test_list_empty(self, client, auth_headers, test_company, test_user_company):
        resp = client.get("/api/v1/categories", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_with_categories(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.get("/api/v1/categories", headers=_headers(auth_headers, test_company))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Fornitori"

    def test_list_includes_subcategories(self, client, auth_headers, test_company, test_user_company, test_category, test_subcategory):
        resp = client.get("/api/v1/categories", headers=_headers(auth_headers, test_company))
        data = resp.json()
        assert len(data[0]["subcategories"]) == 1
        assert data[0]["subcategories"][0]["name"] == "Materie Prime"


class TestCreateCategory:
    def test_create(self, client, auth_headers, test_company, test_user_company):
        resp = client.post(
            "/api/v1/categories",
            json={"name": "Utenze", "color": "#f97316"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Utenze"
        assert data["color"] == "#f97316"
        assert data["is_system"] is False

    def test_duplicate_name(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.post(
            "/api/v1/categories",
            json={"name": "Fornitori", "color": "#000000"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 409

    def test_invalid_color(self, client, auth_headers, test_company, test_user_company):
        resp = client.post(
            "/api/v1/categories",
            json={"name": "Test", "color": "red"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 422


class TestUpdateCategory:
    def test_update_name(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.patch(
            f"/api/v1/categories/{test_category.id}",
            json={"name": "Fornitori Aggiornato"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fornitori Aggiornato"

    def test_update_color(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.patch(
            f"/api/v1/categories/{test_category.id}",
            json={"color": "#000000"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        assert resp.json()["color"] == "#000000"


class TestDeleteCategory:
    def test_delete(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.delete(
            f"/api/v1/categories/{test_category.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 204

    def test_delete_system_category_fails(self, client, auth_headers, test_company, test_user_company, test_system_category):
        resp = client.delete(
            f"/api/v1/categories/{test_system_category.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 400


class TestSubcategories:
    def test_create_subcategory(self, client, auth_headers, test_company, test_user_company, test_category):
        resp = client.post(
            f"/api/v1/categories/{test_category.id}/subcategories",
            json={"name": "Servizi"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 201
        assert resp.json()["name"] == "Servizi"

    def test_create_duplicate_subcategory(self, client, auth_headers, test_company, test_user_company, test_category, test_subcategory):
        resp = client.post(
            f"/api/v1/categories/{test_category.id}/subcategories",
            json={"name": "Materie Prime"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 409

    def test_update_subcategory(self, client, auth_headers, test_company, test_user_company, test_subcategory):
        resp = client.patch(
            f"/api/v1/categories/subcategories/{test_subcategory.id}",
            json={"name": "Materie Prime Aggiornato"},
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Materie Prime Aggiornato"

    def test_delete_subcategory(self, client, auth_headers, test_company, test_user_company, test_subcategory):
        resp = client.delete(
            f"/api/v1/categories/subcategories/{test_subcategory.id}",
            headers=_headers(auth_headers, test_company),
        )
        assert resp.status_code == 204
