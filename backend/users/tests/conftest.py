import os
import pytest
from contextlib import nullcontext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.database import Base, get_db
from main import app

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(test_db):
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    app.router.lifespan_context = lambda app: nullcontext()

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def admin_secret():
    return os.getenv("ADMIN_SECRET", "supersecret123")


@pytest.fixture
def test_user_data():
    return {
        "email": "test@example.com",
        "password": "strongpassword123",
        "full_name": "Test User",
        "apartment": "42"
    }


@pytest.fixture
def test_admin_data(admin_secret):
    return {
        "email": "admin@example.com",
        "password": "adminpass123",
        "admin_secret": admin_secret
    }


@pytest.fixture
def create_user(client, test_user_data):
    def _create(email=None, password=None, is_admin=False, admin_secret=None):
        data = test_user_data.copy()
        if email:
            data["email"] = email
        if password:
            data["password"] = password
        if is_admin and admin_secret:
            data["admin_secret"] = admin_secret

        response = client.post("/auth/register", json=data)
        assert response.status_code == 200

        login_response = client.post("/auth/login", json={
            "email": data["email"],
            "password": data["password"]
        })
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]

        return {"token": token, "email": data["email"], "password": data["password"]}

    return _create


@pytest.fixture
def auth_headers(create_user):
    user = create_user()
    return {"Authorization": f"Bearer {user['token']}"}


@pytest.fixture
def admin_headers(create_user, admin_secret):
    admin = create_user(
        email="admin@test.com",
        is_admin=True,
        admin_secret=admin_secret
    )
    return {"Authorization": f"Bearer {admin['token']}"}
