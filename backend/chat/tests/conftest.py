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
def mock_jwt_token():
    from jose import jwt

    secret = os.getenv("SECRET_KEY", "supersecretkey")

    def _create_token(user_id=1, role="resident"):
        from datetime import datetime, timedelta
        payload = {
            "user_id": user_id,
            "role": role,
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, secret, algorithm="HS256")

    return _create_token


@pytest.fixture
def resident_token(mock_jwt_token):
    return mock_jwt_token(user_id=1, role="resident")


@pytest.fixture
def resident2_token(mock_jwt_token):
    return mock_jwt_token(user_id=2, role="resident")


@pytest.fixture
def admin_token(mock_jwt_token):
    return mock_jwt_token(user_id=999, role="admin")


@pytest.fixture
def auth_headers(resident_token):
    return {"Authorization": f"Bearer {resident_token}"}


@pytest.fixture
def auth_headers2(resident2_token):
    return {"Authorization": f"Bearer {resident2_token}"}


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def sample_room():
    return {
        "name": "Общий чат",
        "description": "Обсуждение общих вопросов"
    }
