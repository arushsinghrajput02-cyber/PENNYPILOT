import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app

# StaticPool ensures the in-memory SQLite connection is reused and persists across test queries
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create fresh tables for every test function and tear down afterwards."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Test client with overridden get_db dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Helper fixture to register a test user and obtain bearer authorization header."""
    user_payload = {
        "name": "Rohan Verma",
        "email": "rohan.test@pennypilot.in",
        "password": "Password123"
    }
    res = client.post("/api/auth/register", json=user_payload)
    data = res.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_auth_headers(client):
    """Helper fixture to register a second test user to test data isolation."""
    user_payload = {
        "name": "Priya Sen",
        "email": "priya.test@pennypilot.in",
        "password": "Password456"
    }
    res = client.post("/api/auth/register", json=user_payload)
    data = res.json()
    token = data["access_token"]
    return {"Authorization": f"Bearer {token}"}
