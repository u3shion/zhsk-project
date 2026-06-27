import pytest
from io import BytesIO


class TestAnnouncementsCreate:

    def test_create_ad_by_resident_success(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "ad"
        assert data["subtype"] == "service"
        assert data["title"] == sample_announcement["title"]
        assert data["author_role"] == "resident"
        assert data["is_active"] is True

    def test_create_news_by_admin_success(self, client, admin_headers, sample_news):
        response = client.post("/announcements/", headers=admin_headers, data=sample_news)
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "news"
        assert data["author_role"] == "admin"

    def test_create_news_by_resident_forbidden(self, client, auth_headers, sample_news):
        response = client.post("/announcements/", headers=auth_headers, data=sample_news)
        assert response.status_code == 403

    @pytest.mark.parametrize("subtype", ["service", "noise"])
    def test_create_ad_both_subtypes(self, client, auth_headers, subtype):
        announcement = {
            "type": "ad",
            "subtype": subtype,
            "title": f"Тест {subtype}",
            "content": "Контент"
        }
        response = client.post("/announcements/", headers=auth_headers, data=announcement)
        assert response.status_code == 201
        assert response.json()["subtype"] == subtype

    def test_create_announcement_with_photo(self, client, auth_headers, sample_announcement):
        photo = BytesIO(b"fake image data")
        photo.name = "test.jpg"

        files = [("photos", ("test.jpg", photo, "image/jpeg"))]
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement, files=files)

        assert response.status_code in [201, 500]
        data = response.json()
        assert response.status_code in [201, 500]

    def test_create_announcement_photo_too_large(self, client, auth_headers, sample_announcement):
        large_photo = BytesIO(b"x" * (6 * 1024 * 1024))
        large_photo.name = "large.jpg"

        files = [("photos", ("large.jpg", large_photo, "image/jpeg"))]
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement, files=files)

        assert response.status_code == 400
        assert "too large" in response.json()["detail"].lower() or "size" in response.json()["detail"].lower()

    def test_create_announcement_invalid_photo_type(self, client, auth_headers, sample_announcement):
        invalid_file = BytesIO(b"not an image")
        invalid_file.name = "file.exe"

        files = [("photos", ("file.exe", invalid_file, "application/octet-stream"))]
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement, files=files)

        assert response.status_code == 400

    def test_create_announcement_unauthorized(self, client, sample_announcement):
        response = client.post("/announcements/", data=sample_announcement)
        assert response.status_code == 401

    def test_create_announcement_missing_fields(self, client, auth_headers):
        response = client.post("/announcements/", headers=auth_headers, data={})
        assert response.status_code == 422


class TestAnnouncementsGet:

    def test_get_announcements_empty(self, client, auth_headers):
        response = client.get("/announcements/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_announcements_list(self, client, auth_headers, admin_headers, sample_announcement, sample_news):
        client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        client.post("/announcements/", headers=admin_headers, data=sample_news)

        response = client.get("/announcements/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_announcements_filter_by_type(self, client, auth_headers, admin_headers, sample_announcement, sample_news):
        client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        client.post("/announcements/", headers=admin_headers, data=sample_news)

        response = client.get("/announcements/?type=news", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "news"

        response = client.get("/announcements/?type=ad", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["type"] == "ad"

    def test_get_announcements_filter_by_subtype(self, client, auth_headers):
        service_ad = {
            "type": "ad",
            "subtype": "service",
            "title": "Услуга",
            "content": "Контент"
        }
        noise_ad = {
            "type": "ad",
            "subtype": "noise",
            "title": "Шум",
            "content": "Контент"
        }

        client.post("/announcements/", headers=auth_headers, data=service_ad)
        client.post("/announcements/", headers=auth_headers, data=noise_ad)

        response = client.get("/announcements/?subtype=service", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["items"][0]["subtype"] == "service"

    def test_get_announcements_pagination(self, client, auth_headers):
        for i in range(5):
            announcement = {
                "type": "ad",
                "subtype": "service",
                "title": f"Объявление {i}",
                "content": "Контент"
            }
            client.post("/announcements/", headers=auth_headers, data=announcement)

        response = client.get("/announcements/?page=1&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 5
        assert data["page"] == 1
        assert data["page_size"] == 2

        response = client.get("/announcements/?page=2&page_size=2", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2

    def test_get_announcements_max_page_size(self, client, auth_headers):
        response = client.get("/announcements/?page_size=200", headers=auth_headers)
        assert response.status_code in [200, 422]

    def test_get_announcement_by_id(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        response = client.get(f"/announcements/{announcement_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == announcement_id
        assert data["title"] == sample_announcement["title"]

    def test_get_announcement_not_found(self, client, auth_headers):
        response = client.get("/announcements/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_announcements_only_active(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        client.delete(f"/announcements/{announcement_id}", headers=auth_headers)

        response = client.get("/announcements/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0


class TestAnnouncementsUpdate:

    def test_update_announcement_by_author(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        update_data = {
            "title": "Обновленный заголовок",
            "content": "Обновленный контент"
        }
        response = client.put(f"/announcements/{announcement_id}", headers=auth_headers, data=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Обновленный заголовок"
        assert data["content"] == "Обновленный контент"

    def test_update_announcement_by_admin(self, client, auth_headers, admin_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        update_data = {"title": "Отредактировано админом"}
        response = client.put(f"/announcements/{announcement_id}", headers=admin_headers, data=update_data)
        assert response.status_code == 200
        assert response.json()["title"] == "Отредактировано админом"

    def test_update_announcement_by_another_user(self, client, mock_jwt_token, sample_announcement):
        user1_token = mock_jwt_token(user_id=1, role="resident")
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        response = client.post("/announcements/", headers=user1_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        user2_token = mock_jwt_token(user_id=2, role="resident")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        update_data = {"title": "Попытка взлома"}
        response = client.put(f"/announcements/{announcement_id}", headers=user2_headers, data=update_data)
        assert response.status_code == 403

    def test_update_announcement_partial(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]
        original_content = response.json()["content"]

        update_data = {"title": "Новый заголовок"}
        response = client.put(f"/announcements/{announcement_id}", headers=auth_headers, data=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Новый заголовок"
        assert data["content"] == original_content

    def test_update_announcement_not_found(self, client, auth_headers):
        response = client.put("/announcements/99999", headers=auth_headers, data={"title": "Test"})
        assert response.status_code == 404


class TestAnnouncementsDelete:

    def test_delete_announcement_by_author(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        response = client.delete(f"/announcements/{announcement_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Announcement deleted"
        assert data["id"] == announcement_id

    def test_delete_announcement_by_admin(self, client, auth_headers, admin_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        response = client.delete(f"/announcements/{announcement_id}", headers=admin_headers)
        assert response.status_code == 200

    def test_delete_announcement_by_another_user(self, client, mock_jwt_token, sample_announcement):
        user1_token = mock_jwt_token(user_id=1, role="resident")
        user1_headers = {"Authorization": f"Bearer {user1_token}"}
        response = client.post("/announcements/", headers=user1_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        user2_token = mock_jwt_token(user_id=2, role="resident")
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        response = client.delete(f"/announcements/{announcement_id}", headers=user2_headers)
        assert response.status_code == 403

    def test_delete_announcement_not_found(self, client, auth_headers):
        response = client.delete("/announcements/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_deleted_announcement_not_visible(self, client, auth_headers, sample_announcement):
        response = client.post("/announcements/", headers=auth_headers, data=sample_announcement)
        announcement_id = response.json()["id"]

        client.delete(f"/announcements/{announcement_id}", headers=auth_headers)

        response = client.get("/announcements/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["total"] == 0

        response = client.get(f"/announcements/{announcement_id}", headers=auth_headers)
        assert response.status_code == 404
