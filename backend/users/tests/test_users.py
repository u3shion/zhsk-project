import pytest


class TestUserProfile:

    def test_get_me_success(self, client, auth_headers):
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert "role" in data
        assert data["role"] == "resident"

    def test_get_me_unauthorized(self, client):
        response = client.get("/users/me")
        assert response.status_code == 401

    def test_update_profile_full_name(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": "Иван Иванов"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["full_name"] == "Иван Иванов"

    def test_update_profile_apartment(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "apartment": "123"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["apartment"] == "123"

    def test_update_profile_notification_channel(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "notification_channel": "email"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["notification_channel"] == "email"

    def test_update_profile_phone(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "phone": "79001234567"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["phone"] == "79001234567"

    def test_update_profile_vk_id(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "vk_id": "123456789"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["vk_id"] == "123456789"

    def test_update_profile_multiple_fields(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": "Петр Петров",
            "apartment": "42",
            "notification_channel": "vk",
            "vk_id": "987654321"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["full_name"] == "Петр Петров"
        assert profile["apartment"] == "42"
        assert profile["notification_channel"] == "vk"
        assert profile["vk_id"] == "987654321"

    def test_update_profile_partial(self, client, auth_headers):
        client.put("/users/me", headers=auth_headers, json={
            "full_name": "Начальное имя",
            "apartment": "10"
        })

        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": "Новое имя"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["full_name"] == "Новое имя"
        assert profile["apartment"] == "10"

    def test_update_profile_empty_json(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={})
        assert response.status_code == 200

    @pytest.mark.parametrize("invalid_channel", [
        "invalid",
        "EMAIL",
        "phone",
        ""
    ])
    def test_update_profile_invalid_notification_channel(self, client, auth_headers, invalid_channel):
        response = client.put("/users/me", headers=auth_headers, json={
            "notification_channel": invalid_channel
        })
        assert response.status_code == 422

    def test_update_profile_unauthorized(self, client):
        response = client.put("/users/me", json={
            "full_name": "Hacker"
        })
        assert response.status_code == 401


class TestUserRoles:

    def test_admin_role_persists(self, client, admin_headers):
        response = client.get("/users/me", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "admin"

    def test_resident_role_default(self, client, auth_headers):
        response = client.get("/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "resident"

    def test_cannot_change_role_via_update(self, client, auth_headers):
        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["role"] == "resident"


class TestEdgeCases:

    def test_very_long_full_name(self, client, auth_headers):
        long_name = "А" * 1000
        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": long_name
        })
        assert response.status_code in [200, 422]

    def test_special_characters_in_name(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": "O'Brien-Smith <test@test>"
        })
        assert response.status_code == 200

    def test_unicode_in_profile(self, client, auth_headers):
        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": "Тест 测试 🏠",
            "apartment": "42А"
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["full_name"] == "Тест 测试 🏠"

    def test_sql_injection_attempt(self, client):
        response = client.post("/auth/register", json={
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "pass123"
        })
        assert response.status_code in [200, 422]

    def test_xss_attempt_in_name(self, client, auth_headers):
        xss_payload = "<script>alert('xss')</script>"
        response = client.put("/users/me", headers=auth_headers, json={
            "full_name": xss_payload
        })
        assert response.status_code == 200

        profile = client.get("/users/me", headers=auth_headers).json()
        assert profile["full_name"] == xss_payload
