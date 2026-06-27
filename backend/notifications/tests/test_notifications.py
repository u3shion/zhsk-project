from unittest.mock import patch, MagicMock


class TestGetResidents:

    @patch('notifications.router.httpx.get')
    def test_get_residents_success(self, mock_get, client, admin_headers, mock_residents):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_residents
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = client.get("/notifications/residents", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "residents" in data
        assert len(data["residents"]) == 2

    def test_get_residents_not_admin(self, client, auth_headers):
        response = client.get("/notifications/residents", headers=auth_headers)
        assert response.status_code == 403

    def test_get_residents_unauthorized(self, client):
        response = client.get("/notifications/residents")
        assert response.status_code == 401


class TestSendNotification:

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_send_notification_success(self, mock_get, mock_dispatch, client, admin_headers, mock_user_contact):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_contact
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.error = None
        mock_dispatch.return_value = mock_result

        response = client.post("/notifications/send", headers=admin_headers, json={
            "user_id": 1,
            "subject": "Тест",
            "message": "Тестовое сообщение"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "sent"
        assert data["channel"] == "email"

    @patch('notifications.router.httpx.get')
    def test_send_notification_user_not_found(self, mock_get, client, admin_headers):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        response = client.post("/notifications/send", headers=admin_headers, json={
            "user_id": 99999,
            "subject": "Тест",
            "message": "Тестовое сообщение"
        })

        assert response.status_code == 404

    def test_send_notification_not_admin(self, client, auth_headers):
        response = client.post("/notifications/send", headers=auth_headers, json={
            "user_id": 1,
            "subject": "Тест",
            "message": "Тестовое сообщение"
        })
        assert response.status_code == 403

    def test_send_notification_missing_fields(self, client, admin_headers):
        response = client.post("/notifications/send", headers=admin_headers, json={})
        assert response.status_code == 422


class TestBroadcast:

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_broadcast_success(self, mock_get, mock_dispatch, client, admin_headers, mock_residents):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_residents
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.error = None
        mock_dispatch.return_value = mock_result

        response = client.post("/notifications/broadcast", headers=admin_headers, json={
            "subject": "Общее объявление",
            "message": "Важная информация для всех"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["sent"] == 2
        assert data["failed"] == 0
        assert len(data["results"]) == 2

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_broadcast_partial_failure(self, mock_get, mock_dispatch, client, admin_headers, mock_residents):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_residents
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result_success = MagicMock()
        mock_result_success.success = True
        mock_result_success.error = None

        mock_result_fail = MagicMock()
        mock_result_fail.success = False
        mock_result_fail.error = "SMTP error"

        mock_dispatch.side_effect = [mock_result_success, mock_result_fail]

        response = client.post("/notifications/broadcast", headers=admin_headers, json={
            "subject": "Тест",
            "message": "Сообщение"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["sent"] == 1
        assert data["failed"] == 1

    def test_broadcast_not_admin(self, client, auth_headers):
        response = client.post("/notifications/broadcast", headers=auth_headers, json={
            "subject": "Тест",
            "message": "Сообщение"
        })
        assert response.status_code == 403

    @patch('notifications.router.httpx.get')
    def test_broadcast_empty_residents(self, mock_get, client, admin_headers):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        response = client.post("/notifications/broadcast", headers=admin_headers, json={
            "subject": "Тест",
            "message": "Сообщение"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["sent"] == 0
        assert data["failed"] == 0


class TestNotificationHistory:

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_get_history_empty(self, client, admin_headers):
        response = client.get("/notifications/history", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["logs"] == []

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_get_history_with_records(self, mock_get, mock_dispatch, client, admin_headers, mock_user_contact):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_contact
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.error = None
        mock_dispatch.return_value = mock_result

        client.post("/notifications/send", headers=admin_headers, json={
            "user_id": 1,
            "subject": "Тест",
            "message": "Сообщение"
        })

        response = client.get("/notifications/history", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["logs"]) == 1

    def test_get_history_filter_by_user(self, client, admin_headers):
        response = client.get("/notifications/history?user_id=1", headers=admin_headers)
        assert response.status_code == 200

    def test_get_history_filter_by_status(self, client, admin_headers):
        response = client.get("/notifications/history?status=sent", headers=admin_headers)
        assert response.status_code == 200

    def test_get_history_pagination(self, client, admin_headers):
        response = client.get("/notifications/history?page=1&page_size=10", headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data

    def test_get_history_not_admin(self, client, auth_headers):
        response = client.get("/notifications/history", headers=auth_headers)
        assert response.status_code == 403


class TestNotificationChannels:

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_send_via_email_channel(self, mock_get, mock_dispatch, client, admin_headers, mock_user_contact):
        mock_user_contact["notification_channel"] = "email"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_contact
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.error = None
        mock_dispatch.return_value = mock_result

        response = client.post("/notifications/send", headers=admin_headers, json={
            "user_id": 1,
            "subject": "Тест",
            "message": "Сообщение"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "email"

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_send_via_sms_channel(self, mock_get, mock_dispatch, client, admin_headers, mock_user_contact):
        mock_user_contact["notification_channel"] = "sms"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_contact
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.error = None
        mock_dispatch.return_value = mock_result

        response = client.post("/notifications/send", headers=admin_headers, json={
            "user_id": 1,
            "subject": "Тест",
            "message": "Сообщение"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "sms"

    @patch('notifications.router.dispatch')
    @patch('notifications.router.httpx.get')
    def test_send_via_vk_channel(self, mock_get, mock_dispatch, client, admin_headers, mock_user_contact):
        mock_user_contact["notification_channel"] = "vk"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_contact
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        mock_result = MagicMock()
        mock_result.success = True
        mock_result.error = None
        mock_dispatch.return_value = mock_result

        response = client.post("/notifications/send", headers=admin_headers, json={
            "user_id": 1,
            "subject": "Тест",
            "message": "Сообщение"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["channel"] == "vk"
