import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ── Must be set BEFORE any app module imports ──────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "testsecretkey1234567890abcdef12345678")
os.environ.setdefault("ALLOWED_ORIGINS", '["http://localhost:3000"]')

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.database import Base, get_db
from app.config import settings

# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override get_db dependency
@pytest.fixture(scope="function")
def db():
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def token_headers(client):
    # Register test user
    client.post(
        f"{settings.API_V1_STR}/auth/register",
        json={"username": "testuser", "email": "test@example.com", "password": "password123"}
    )

    # Login to get token
    login_res = client.post(
        f"{settings.API_V1_STR}/auth/token",
        data={"username": "testuser", "password": "password123"}
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
