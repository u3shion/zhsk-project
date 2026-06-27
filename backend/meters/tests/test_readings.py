import pytest


class TestReadingsCreate:

    def test_create_reading_success(self, client, auth_headers, sample_reading):
        response = client.post("/readings/", headers=auth_headers, json=sample_reading)
        assert response.status_code == 201
        data = response.json()
        assert data["apartment"] == sample_reading["apartment"]
        assert data["period"] == sample_reading["period"]
        assert data["meter_type"] == sample_reading["meter_type"]
        assert data["value"] == sample_reading["value"]
        assert data["user_id"] == 1

    def test_create_reading_unauthorized(self, client, sample_reading):
        response = client.post("/readings/", json=sample_reading)
        assert response.status_code == 401

    @pytest.mark.parametrize("meter_type", [
        "electricity",
        "cold_water",
        "hot_water",
        "heating",
        "gas"
    ])
    def test_create_reading_all_types(self, client, auth_headers, meter_type):
        reading = {
            "apartment": "10",
            "period": "2026-06",
            "meter_type": meter_type,
            "value": 100.0
        }
        response = client.post("/readings/", headers=auth_headers, json=reading)
        assert response.status_code == 201
        assert response.json()["meter_type"] == meter_type

    def test_create_duplicate_reading(self, client, auth_headers, sample_reading):
        response1 = client.post("/readings/", headers=auth_headers, json=sample_reading)
        assert response1.status_code == 201

        response2 = client.post("/readings/", headers=auth_headers, json=sample_reading)
        assert response2.status_code == 400
        assert "already submitted" in response2.json()["detail"].lower() or "duplicate" in response2.json()["detail"].lower()

    def test_create_reading_different_periods(self, client, auth_headers):
        reading1 = {
            "apartment": "42",
            "period": "2026-05",
            "meter_type": "cold_water",
            "value": 100.0
        }
        reading2 = {
            "apartment": "42",
            "period": "2026-06",
            "meter_type": "cold_water",
            "value": 110.0
        }

        response1 = client.post("/readings/", headers=auth_headers, json=reading1)
        response2 = client.post("/readings/", headers=auth_headers, json=reading2)

        assert response1.status_code == 201
        assert response2.status_code == 201

    @pytest.mark.parametrize("invalid_value", [
        -10,
        -0.001
    ])
    def test_create_reading_negative_value(self, client, auth_headers, invalid_value):
        reading = {
            "apartment": "42",
            "period": "2026-05",
            "meter_type": "cold_water",
            "value": invalid_value
        }
        response = client.post("/readings/", headers=auth_headers, json=reading)
        assert response.status_code in [400, 422]

    def test_create_reading_very_large_value(self, client, auth_headers):
        reading = {
            "apartment": "42",
            "period": "2026-05",
            "meter_type": "electricity",
            "value": 999999999.99
        }
        response = client.post("/readings/", headers=auth_headers, json=reading)
        assert response.status_code in [201, 400, 422]

    @pytest.mark.parametrize("invalid_period", [
        "2026-13",
        "2026-00",
        "26-05",
        "2026/05",
        "invalid"
    ])
    def test_create_reading_invalid_period(self, client, auth_headers, invalid_period):
        reading = {
            "apartment": "42",
            "period": invalid_period,
            "meter_type": "cold_water",
            "value": 100.0
        }
        response = client.post("/readings/", headers=auth_headers, json=reading)
        assert response.status_code == 422

    def test_create_reading_invalid_meter_type(self, client, auth_headers):
        reading = {
            "apartment": "42",
            "period": "2026-05",
            "meter_type": "invalid_type",
            "value": 100.0
        }
        response = client.post("/readings/", headers=auth_headers, json=reading)
        assert response.status_code == 422

    def test_create_reading_missing_fields(self, client, auth_headers):
        response = client.post("/readings/", headers=auth_headers, json={})
        assert response.status_code == 422


class TestReadingsGet:

    def test_get_my_readings_empty(self, client, auth_headers):
        response = client.get("/readings/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["readings"] == []
        assert data["total"] == 0

    def test_get_my_readings(self, client, auth_headers):
        readings = [
            {"apartment": "42", "period": "2026-05", "meter_type": "cold_water", "value": 100.0},
            {"apartment": "42", "period": "2026-05", "meter_type": "hot_water", "value": 80.0},
        ]
        for r in readings:
            client.post("/readings/", headers=auth_headers, json=r)

        response = client.get("/readings/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["readings"]) == 2

    def test_get_my_readings_filter_by_period(self, client, auth_headers):
        client.post("/readings/", headers=auth_headers, json={
            "apartment": "42", "period": "2026-05", "meter_type": "cold_water", "value": 100.0
        })
        client.post("/readings/", headers=auth_headers, json={
            "apartment": "42", "period": "2026-06", "meter_type": "cold_water", "value": 110.0
        })

        response = client.get("/readings/me?period=2026-05", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["readings"][0]["period"] == "2026-05"

    def test_get_my_readings_filter_by_meter_type(self, client, auth_headers):
        client.post("/readings/", headers=auth_headers, json={
            "apartment": "42", "period": "2026-05", "meter_type": "cold_water", "value": 100.0
        })
        client.post("/readings/", headers=auth_headers, json={
            "apartment": "42", "period": "2026-05", "meter_type": "electricity", "value": 500.0
        })

        response = client.get("/readings/me?meter_type=cold_water", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["readings"][0]["meter_type"] == "cold_water"

    def test_get_my_readings_unauthorized(self, client):
        response = client.get("/readings/me")
        assert response.status_code == 401

    def test_user_sees_only_own_readings(self, client, mock_jwt_token):
        user1_token = mock_jwt_token(user_id=1, role="resident")
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        client.post("/readings/", headers=user1_headers, json={
            "apartment": "10", "period": "2026-05", "meter_type": "cold_water", "value": 100.0
        })

        user2_token = mock_jwt_token(user_id=2, role="resident")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        client.post("/readings/", headers=user2_headers, json={
            "apartment": "20", "period": "2026-05", "meter_type": "cold_water", "value": 200.0
        })

        response1 = client.get("/readings/me", headers=user1_headers)
        response2 = client.get("/readings/me", headers=user2_headers)

        assert response1.json()["total"] == 1
        assert response2.json()["total"] == 1
        assert response1.json()["readings"][0]["apartment"] == "10"
        assert response2.json()["readings"][0]["apartment"] == "20"


class TestReadingsSummary:

    def test_summary_admin_access(self, client, admin_headers):
        response = client.get("/readings/summary?period=2026-05", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "apartments" in data

    def test_summary_resident_denied(self, client, auth_headers):
        response = client.get("/readings/summary?period=2026-05", headers=auth_headers)
        assert response.status_code == 403

    def test_summary_missing_period(self, client, admin_headers):
        response = client.get("/readings/summary", headers=admin_headers)
        assert response.status_code in [200, 422]

    def test_summary_shows_complete_incomplete(self, client, admin_headers, mock_jwt_token):
        user1_token = mock_jwt_token(user_id=1, role="resident")
        user1_headers = {"Authorization": f"Bearer {user1_token}"}

        meter_types = ["electricity", "cold_water", "hot_water", "heating", "gas"]
        for meter_type in meter_types:
            client.post("/readings/", headers=user1_headers, json={
                "apartment": "10",
                "period": "2026-05",
                "meter_type": meter_type,
                "value": 100.0
            })

        user2_token = mock_jwt_token(user_id=2, role="resident")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        client.post("/readings/", headers=user2_headers, json={
            "apartment": "20",
            "period": "2026-05",
            "meter_type": "electricity",
            "value": 50.0
        })

        response = client.get("/readings/summary?period=2026-05", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()

        assert data["complete"] >= 1
        assert data["incomplete"] >= 1
