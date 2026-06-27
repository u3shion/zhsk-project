class TestRoomCreate:

    def test_create_room_success(self, client, auth_headers, sample_room):
        response = client.post("/rooms/", headers=auth_headers, json=sample_room)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_room["name"]
        assert data["description"] == sample_room["description"]
        assert data["created_by"] == 1
        assert data["is_active"] is True

    def test_create_room_without_description(self, client, auth_headers):
        response = client.post("/rooms/", headers=auth_headers, json={
            "name": "Комната без описания"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Комната без описания"
        assert data["description"] is None

    def test_create_room_unauthorized(self, client, sample_room):
        response = client.post("/rooms/", json=sample_room)
        assert response.status_code == 401

    def test_create_room_missing_name(self, client, auth_headers):
        response = client.post("/rooms/", headers=auth_headers, json={})
        assert response.status_code == 422


class TestRoomList:

    def test_list_rooms_empty(self, client, auth_headers):
        response = client.get("/rooms/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_list_rooms_with_own_rooms(self, client, auth_headers, sample_room):
        client.post("/rooms/", headers=auth_headers, json=sample_room)
        client.post("/rooms/", headers=auth_headers, json={"name": "Комната 2"})

        response = client.get("/rooms/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2

    def test_list_rooms_no_other_users_rooms(self, client, auth_headers, auth_headers2):
        client.post("/rooms/", headers=auth_headers, json={"name": "Комната User1"})
        client.post("/rooms/", headers=auth_headers2, json={"name": "Комната User2"})

        response = client.get("/rooms/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Комната User1"


class TestRoomGet:

    def test_get_room_success(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == room_id
        assert data["name"] == sample_room["name"]

    def test_get_room_not_found(self, client, auth_headers):
        response = client.get("/rooms/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_get_room_not_member(self, client, auth_headers, auth_headers2, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}", headers=auth_headers2)
        assert response.status_code == 403


class TestRoomInvite:

    def test_invite_user_success(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.post(
            f"/rooms/{room_id}/invite",
            headers=auth_headers,
            json={"user_id": 2}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == 2

    def test_invite_user_already_member(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        client.post(f"/rooms/{room_id}/invite", headers=auth_headers, json={"user_id": 2})
        response = client.post(f"/rooms/{room_id}/invite", headers=auth_headers, json={"user_id": 2})

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_invite_user_not_member(self, client, auth_headers, auth_headers2, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.post(
            f"/rooms/{room_id}/invite",
            headers=auth_headers2,
            json={"user_id": 3}
        )
        assert response.status_code == 403


class TestRoomLeave:

    def test_leave_room_success(self, client, auth_headers, auth_headers2, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        client.post(f"/rooms/{room_id}/invite", headers=auth_headers, json={"user_id": 2})

        response = client.delete(f"/rooms/{room_id}/leave", headers=auth_headers2)
        assert response.status_code == 200
        data = response.json()
        assert data["room_id"] == room_id

    def test_leave_room_not_member(self, client, auth_headers, auth_headers2, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.delete(f"/rooms/{room_id}/leave", headers=auth_headers2)
        assert response.status_code == 400


class TestRoomMembers:

    def test_get_members_creator_only(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}/members", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user_id"] == 1

    def test_get_members_multiple(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        client.post(f"/rooms/{room_id}/invite", headers=auth_headers, json={"user_id": 2})
        client.post(f"/rooms/{room_id}/invite", headers=auth_headers, json={"user_id": 3})

        response = client.get(f"/rooms/{room_id}/members", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_members_not_member(self, client, auth_headers, auth_headers2, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}/members", headers=auth_headers2)
        assert response.status_code == 403


class TestRoomMessages:

    def test_get_messages_empty(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}/messages", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_messages_not_member(self, client, auth_headers, auth_headers2, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}/messages", headers=auth_headers2)
        assert response.status_code == 403

    def test_get_messages_with_limit(self, client, auth_headers, sample_room):
        create_resp = client.post("/rooms/", headers=auth_headers, json=sample_room)
        room_id = create_resp.json()["id"]

        response = client.get(f"/rooms/{room_id}/messages?limit=10", headers=auth_headers)
        assert response.status_code == 200
