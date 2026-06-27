import pytest
from datetime import date, timedelta


class TestWaterMetersCreate:

    def test_create_water_meter_success(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "AB-123456",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        assert response.status_code == 201
        data = response.json()
        assert data["serial_number"] == meter["serial_number"]
        assert data["is_active"] is True

    def test_create_water_meter_unauthorized(self, client):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "AB-123456",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", json=meter)
        assert response.status_code == 401

    @pytest.mark.parametrize("meter_type", ["cold", "hot"])
    def test_create_water_meter_both_types(self, client, auth_headers, meter_type):
        meter = {
            "apartment": "42",
            "meter_type": meter_type,
            "serial_number": f"SN-{meter_type}-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        assert response.status_code == 201
        assert response.json()["meter_type"] == meter_type

    def test_create_water_meter_with_last_verification(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "AB-123456",
            "installed_at": "2022-01-15",
            "last_verified_at": "2024-01-15",
            "next_verification_at": "2030-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        assert response.status_code == 201
        data = response.json()
        assert data["last_verified_at"] == "2024-01-15"

    def test_create_water_meter_invalid_type(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "warm",
            "serial_number": "AB-123456",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", json=meter, headers=auth_headers)
        assert response.status_code == 422

    def test_create_water_meter_future_installed_date(self, client, auth_headers):
        future_date = (date.today() + timedelta(days=365)).isoformat()
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "AB-123456",
            "installed_at": future_date,
            "next_verification_at": "2030-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        assert response.status_code in [201, 400, 422]

    def test_create_water_meter_verification_before_install(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "AB-123456",
            "installed_at": "2025-01-15",
            "next_verification_at": "2024-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        assert response.status_code in [400, 422]

    def test_create_water_meter_missing_fields(self, client, auth_headers):
        response = client.post("/water-meters/", headers=auth_headers, json={})
        assert response.status_code == 422


class TestWaterMetersGet:

    def test_get_my_meters_empty(self, client, auth_headers):
        response = client.get("/water-meters/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_get_my_meters(self, client, auth_headers):
        meter1 = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "COLD-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        meter2 = {
            "apartment": "42",
            "meter_type": "hot",
            "serial_number": "HOT-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2027-01-15"
        }

        client.post("/water-meters/", headers=auth_headers, json=meter1)
        client.post("/water-meters/", headers=auth_headers, json=meter2)

        response = client.get("/water-meters/me", headers=auth_headers)
        assert response.status_code == 200
        meters = response.json()
        assert len(meters) == 2

    def test_get_my_meters_sorted_by_verification_date(self, client, auth_headers):
        meter1 = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "COLD-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2030-01-15"
        }
        meter2 = {
            "apartment": "42",
            "meter_type": "hot",
            "serial_number": "HOT-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2027-01-15"
        }

        client.post("/water-meters/", headers=auth_headers, json=meter1)
        client.post("/water-meters/", headers=auth_headers, json=meter2)

        response = client.get("/water-meters/me", headers=auth_headers)
        meters = response.json()

        assert meters[0]["next_verification_at"] <= meters[1]["next_verification_at"]

    def test_get_my_meters_only_active(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "COLD-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        meter_id = response.json()["id"]

        client.delete(f"/water-meters/{meter_id}", headers=auth_headers)

        response = client.get("/water-meters/me", headers=auth_headers)
        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_user_sees_only_own_meters(self, client, mock_jwt_token):
        user1_token = mock_jwt_token(user_id=1, role="resident")
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        client.post("/water-meters/", headers=user1_headers, json={
            "apartment": "10",
            "meter_type": "cold",
            "serial_number": "USER1-COLD",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        })

        user2_token = mock_jwt_token(user_id=2, role="resident")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        client.post("/water-meters/", headers=user2_headers, json={
            "apartment": "20",
            "meter_type": "cold",
            "serial_number": "USER2-COLD",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        })

        response1 = client.get("/water-meters/me", headers=user1_headers)
        response2 = client.get("/water-meters/me", headers=user2_headers)

        meters1 = response1.json()
        meters2 = response2.json()

        assert len(meters1) == 1
        assert len(meters2) == 1
        assert meters1[0]["serial_number"] == "USER1-COLD"
        assert meters2[0]["serial_number"] == "USER2-COLD"


class TestWaterMetersUpdate:

    def test_update_meter_verification_dates(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "COLD-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        meter_id = response.json()["id"]

        update_data = {
            "last_verified_at": "2026-05-01",
            "next_verification_at": "2032-05-01"
        }
        response = client.put(f"/water-meters/{meter_id}", headers=auth_headers, json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["last_verified_at"] == "2026-05-01"
        assert data["next_verification_at"] == "2032-05-01"

    def test_update_meter_not_found(self, client, auth_headers):
        update_data = {
            "last_verified_at": "2026-05-01",
            "next_verification_at": "2032-05-01"
        }
        response = client.put("/water-meters/99999", headers=auth_headers, json=update_data)
        assert response.status_code == 404


class TestWaterMetersDelete:

    def test_deactivate_meter_success(self, client, auth_headers):
        meter = {
            "apartment": "42",
            "meter_type": "cold",
            "serial_number": "COLD-001",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", headers=auth_headers, json=meter)
        meter_id = response.json()["id"]

        response = client.delete(f"/water-meters/{meter_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Meter deactivated"
        assert data["id"] == meter_id

    def test_deactivate_meter_not_found(self, client, auth_headers):
        response = client.delete("/water-meters/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_deactivate_meter_of_another_user(self, client, mock_jwt_token):
        user1_token = mock_jwt_token(user_id=1, role="resident")
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        meter = {
            "apartment": "10",
            "meter_type": "cold",
            "serial_number": "USER1-COLD",
            "installed_at": "2022-01-15",
            "next_verification_at": "2028-01-15"
        }
        response = client.post("/water-meters/", headers=user1_headers, json=meter)
        meter_id = response.json()["id"]

        user2_token = mock_jwt_token(user_id=2, role="resident")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        response = client.delete(f"/water-meters/{meter_id}", headers=user2_headers)
        assert response.status_code == 404


class TestWaterMetersSummary:

    def test_summary_admin_access(self, client, admin_headers):
        response = client.get("/water-meters/summary", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "meters" in data

    def test_summary_resident_denied(self, client, auth_headers):
        response = client.get("/water-meters/summary", headers=auth_headers)
        assert response.status_code == 403

    def test_summary_shows_overdue_meters(self, client, admin_headers, mock_jwt_token):
        user_token = mock_jwt_token(user_id=1, role="resident")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        past_date = (date.today() - timedelta(days=30)).isoformat()
        meter = {
            "apartment": "10",
            "meter_type": "cold",
            "serial_number": "OVERDUE-001",
            "installed_at": "2020-01-15",
            "next_verification_at": past_date
        }
        client.post("/water-meters/", headers=user_headers, json=meter)

        response = client.get("/water-meters/summary", headers=admin_headers)
        data = response.json()

        assert data["overdue_count"] >= 1
        overdue_meters = [m for m in data["meters"] if m.get("overdue")]
        assert len(overdue_meters) >= 1

    def test_summary_shows_needs_attention(self, client, admin_headers, mock_jwt_token):
        user_token = mock_jwt_token(user_id=1, role="resident")
        user_headers = {"Authorization": f"Bearer {user_token}"}

        soon_date = (date.today() + timedelta(days=45)).isoformat()
        meter = {
            "apartment": "20",
            "meter_type": "hot",
            "serial_number": "ATTENTION-001",
            "installed_at": "2020-01-15",
            "next_verification_at": soon_date
        }
        client.post("/water-meters/", headers=user_headers, json=meter)

        response = client.get("/water-meters/summary", headers=admin_headers)
        data = response.json()

        assert data["needs_attention_count"] >= 1
