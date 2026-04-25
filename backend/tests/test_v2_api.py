from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models import Project, User


TEST_DATABASE_URL = "sqlite:///./test_v2_api.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def client():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def project_id():
    db = TestingSessionLocal()
    try:
        user = User(
            email=f"{uuid4()}@example.com",
            username="v2-test-user",
            hashed_password="not-used",
        )
        db.add(user)
        db.flush()

        project = Project(
            user_id=user.id,
            title="AI Incubator v2",
            framework="general",
            status="active",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        return project.id
    finally:
        db.close()


def test_workspace_bootstraps_one_center_idea_node(client, project_id):
    response = client.get(f"/api/v2/projects/{project_id}/workspace")

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(project_id)
    assert data["title"] == "AI Incubator v2"
    assert data["messages"] == []
    assert data["suggestions"] == []
    assert len(data["nodes"]) == 1

    root = data["nodes"][0]
    assert root["kind"] == "idea"
    assert root["parent_id"] is None
    assert root["title"] == "AI Incubator v2"


def test_turn_creates_messages_and_question_node(client, project_id):
    response = client.post(
        f"/api/v2/projects/{project_id}/turns",
        json={"content": "I want to build an AI research assistant."},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["user_message"]["role"] == "user"
    assert data["user_message"]["content"] == "I want to build an AI research assistant."
    assert data["assistant_message"]["role"] == "assistant"
    assert data["thinking_mode"] in {"diverge", "converge", "clarify", "challenge", "validate"}
    assert data["assistant_message"]["thinking_mode"] == data["thinking_mode"]

    messages = data["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]

    question_nodes = [node for node in data["nodes"] if node["kind"] == "question"]
    assert len(question_nodes) >= 1
    assert question_nodes[0]["parent_id"] is not None
    assert question_nodes[0]["question"]
