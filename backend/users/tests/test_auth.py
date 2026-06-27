import pytest
from jose import jwt
from datetime import datetime, timedelta


class TestRegistration:

    def test_register_resident_success(self, client):
        response = client.post("/auth/register", json={
            "email": "resident@example.com",
            "password": "securepass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "user created"
        assert data["role"] == "resident"

    def test_register_admin_success(self, client, admin_secret):
        response = client.post("/auth/register", json={
            "email": "admin@example.com",
            "password": "adminpass123",
            "admin_secret": admin_secret
        })
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "user created"
        assert data["role"] == "admin"

    def test_register_admin_wrong_secret(self, client):
        response = client.post("/auth/register", json={
            "email": "notadmin@example.com",
            "password": "password123",
            "admin_secret": "wrongsecret"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["role"] == "resident"

    def test_register_duplicate_email(self, client):
        email = "duplicate@example.com"
        client.post("/auth/register", json={
            "email": email,
            "password": "password1"
        })

        response = client.post("/auth/register", json={
            "email": email,
            "password": "password2"
        })
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    @pytest.mark.parametrize("invalid_email", [
        "",
        "notanemail",
        "@example.com",
        "user@",
        "user @example.com",
        None
    ])
    def test_register_invalid_email(self, client, invalid_email):
        response = client.post("/auth/register", json={
            "email": invalid_email,
            "password": "password123"
        })
        assert response.status_code == 422

    @pytest.mark.parametrize("invalid_password", [
        "",
        "123",
        None
    ])
    def test_register_invalid_password(self, client, invalid_password):
        response = client.post("/auth/register", json={
            "email": "test@example.com",
            "password": invalid_password
        })
        assert response.status_code == 422

    def test_register_missing_fields(self, client):
        response = client.post("/auth/register", json={})
        assert response.status_code == 422


class TestLogin:

    def test_login_success(self, client, create_user):
        user = create_user()

        response = client.post("/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client, create_user):
        user = create_user()

        response = client.post("/auth/login", json={
            "email": user["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    def test_login_nonexistent_user(self, client):
        response = client.post("/auth/login", json={
            "email": "ghost@example.com",
            "password": "anypass"
        })
        assert response.status_code == 401

    def test_login_case_sensitive_email(self, client, create_user):
        user = create_user(email="Test@Example.com")

        response = client.post("/auth/login", json={
            "email": "test@example.com",
            "password": user["password"]
        })
        assert response.status_code in [200, 401]

    def test_jwt_token_structure(self, client, create_user):
        import os
        user = create_user()

        response = client.post("/auth/login", json={
            "email": user["email"],
            "password": user["password"]
        })
        token = response.json()["access_token"]

        secret = os.getenv("SECRET_KEY", "supersecretkey")
        payload = jwt.decode(token, secret, algorithms=["HS256"])

        assert "user_id" in payload
        assert "role" in payload
        assert "exp" in payload
        assert payload["role"] in ["resident", "admin"]

    def test_login_missing_fields(self, client):
        response = client.post("/auth/login", json={})
        assert response.status_code == 422


class TestTokenExpiration:

    def test_expired_token_rejected(self, client):
        import os
        from jose import jwt

        secret = os.getenv("SECRET_KEY", "supersecretkey")
        expired_payload = {
            "user_id": 1,
            "role": "resident",
            "exp": datetime.utcnow() - timedelta(hours=1)
        }
        expired_token = jwt.encode(expired_payload, secret, algorithm="HS256")

        response = client.get("/users/me", headers={
            "Authorization": f"Bearer {expired_token}"
        })
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower() or "invalid" in response.json()["detail"].lower()

    def test_malformed_token(self, client):
        response = client.get("/users/me", headers={
            "Authorization": "Bearer invalidtoken123"
        })
        assert response.status_code == 401

    def test_missing_token(self, client):
        response = client.get("/users/me")
        assert response.status_code == 401


class TestPasswordSecurity:

    def test_password_hashed_in_db(self, test_db, create_user):
        from models.user import User

        password = "mypassword123"
        user_data = create_user(password=password)

        db_user = test_db.query(User).filter(User.email == user_data["email"]).first()
        assert db_user.hashed_password != password
        assert len(db_user.hashed_password) > 50

    def test_same_password_different_hashes(self, client, test_db):
        from models.user import User

        password = "samepass123"
        client.post("/auth/register", json={
            "email": "user1@example.com",
            "password": password
        })
        client.post("/auth/register", json={
            "email": "user2@example.com",
            "password": password
        })

        user1 = test_db.query(User).filter(User.email == "user1@example.com").first()
        user2 = test_db.query(User).filter(User.email == "user2@example.com").first()

        assert user1.hashed_password != user2.hashed_password
