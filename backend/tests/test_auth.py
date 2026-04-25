import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.models import User


# Use in-memory SQLite for testing
TEST_DATABASE_URL = "sqlite:///.test"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def client():
    """Create test client with database override."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)


def test_read_root(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert data["status"] == "running"


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser",
            "password": "testpass123",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_register_duplicate_email(client):
    """Test registration with duplicate email."""
    client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser1",
            "password": "testpass123",
        },
    )

    response = client.post(
        "/auth/register",
        json={
            "email": "test@example.com",
            "username": "testuser2",
            "password": "testpass123",
        },
    )
    assert response.status_code == 400


def test_login_success(client):
    """Test successful login."""
    # First register
    client.post(
        "/auth/register",
        json={
            "email": "login@example.com",
            "username": "loginuser",
            "password": "loginpass123",
        },
    )

    # Then login
    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "loginpass123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_credentials(client):
    """Test login with wrong credentials."""
    response = client.post(
        "/auth/login",
        json={
            "email": "wrong@example.com",
            "password": "wrongpass",
        },
    )
    assert response.status_code == 401


def test_ai_generate_question_endpoint(client):
    """Test AI question generation endpoint."""
    response = client.post(
        "/ai/generate-question",
        json={
            "framework": "product_manager",
            "context": "AI diary app",
            "label": "目标用户",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "context" in data


def test_ai_extract_points_endpoint(client):
    """Test AI point extraction endpoint fallback shape."""
    response = client.post(
        "/ai/extract-points",
        json={"answer": "Users want a simple diary tool."},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["points"], list)
    assert "summary" in data


def test_ai_followup_endpoint(client):
    """Test AI follow-up endpoint fallback shape."""
    response = client.post(
        "/ai/followup/test-node",
        json={"parent_answer": "Users need emotional insights.", "label": "情感分析"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "question" in data
    assert "context" in data
