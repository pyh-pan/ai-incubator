from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import Project, RestructureSuggestion, ThinkingNode, User


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
def user():
    db = TestingSessionLocal()
    try:
        user = User(
            email=f"{uuid4()}@example.com",
            username=f"v2-test-user-{uuid4()}",
            hashed_password="not-used",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


@pytest.fixture
def auth_headers(user):
    return {"Authorization": f"Bearer {create_access_token(subject=user.id)}"}


@pytest.fixture
def project_id(user):
    db = TestingSessionLocal()
    try:
        user = db.merge(user)
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


def test_workspace_bootstraps_one_center_idea_node(client, project_id, auth_headers):
    response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)

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


def test_repeated_workspace_fetch_does_not_create_duplicate_root_nodes(client, project_id, auth_headers):
    first_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)
    second_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    db = TestingSessionLocal()
    try:
        parentless_nodes = (
            db.query(ThinkingNode)
            .filter(
                ThinkingNode.project_id == project_id,
                ThinkingNode.parent_id.is_(None),
            )
            .all()
        )
        assert len(parentless_nodes) == 1
    finally:
        db.close()


def test_workspace_reuses_existing_parentless_non_idea_node(client, project_id, auth_headers):
    db = TestingSessionLocal()
    try:
        existing_root = ThinkingNode(
            project_id=project_id,
            parent_id=None,
            kind="question",
            status="open",
            title="Existing root question",
            sort_order=0,
            layout={"x": 0, "y": 0},
            source_message_ids=[],
            confidence=90,
        )
        db.add(existing_root)
        db.commit()
    finally:
        db.close()

    response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    parentless_nodes = [node for node in data["nodes"] if node["parent_id"] is None]
    assert len(parentless_nodes) == 1
    assert parentless_nodes[0]["kind"] == "question"
    assert parentless_nodes[0]["title"] == "Existing root question"


def test_create_project_without_framework_defaults_to_general(client, auth_headers):
    response = client.post(
        "/projects",
        json={
            "title": "Legacy default framework",
            "more_info": "Early users are solo founders validating fuzzy product ideas.",
        },
        headers=auth_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Legacy default framework"
    assert data["more_info"] == "Early users are solo founders validating fuzzy product ideas."
    assert data["framework"] == "general"


def test_turn_creates_messages_and_question_node(client, project_id, auth_headers):
    response = client.post(
        f"/api/v2/projects/{project_id}/turns",
        json={"content": "I want to build an AI research assistant."},
        headers=auth_headers,
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


def test_reject_missing_suggestion_returns_404(client, auth_headers):
    response = client.post(f"/api/v2/restructure-suggestions/{uuid4()}/reject", headers=auth_headers)

    assert response.status_code == 404


def test_workspace_rejects_missing_token(client, project_id):
    response = client.get(f"/api/v2/projects/{project_id}/workspace")

    assert response.status_code == 401


def test_workspace_rejects_other_users_project(client, project_id):
    other_user_id = uuid4()
    headers = {"Authorization": f"Bearer {create_access_token(subject=other_user_id)}"}

    response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=headers)

    assert response.status_code == 404


def test_reject_suggestion_marks_resolved_and_hides_it(client, project_id, auth_headers):
    db = TestingSessionLocal()
    try:
        suggestion = RestructureSuggestion(
            project_id=project_id,
            status="pending",
            operations=[],
            rationale="No longer useful.",
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        suggestion_id = suggestion.id
    finally:
        db.close()

    response = client.post(f"/api/v2/restructure-suggestions/{suggestion_id}/reject", headers=auth_headers)

    assert response.status_code == 200
    assert response.json()["suggestions"] == []

    db = TestingSessionLocal()
    try:
        resolved = db.query(RestructureSuggestion).filter(RestructureSuggestion.id == suggestion_id).one()
        assert resolved.status == "rejected"
        assert resolved.resolved_at is not None
    finally:
        db.close()


def test_accept_suggestion_applies_operation_and_hides_it(client, project_id, auth_headers):
    db = TestingSessionLocal()
    try:
        root = ThinkingNode(
            project_id=project_id,
            parent_id=None,
            kind="idea",
            status="confirmed",
            title="Original title",
            sort_order=0,
            layout={"x": 0, "y": 0},
            source_message_ids=[],
            confidence=100,
        )
        db.add(root)
        db.flush()

        suggestion = RestructureSuggestion(
            project_id=project_id,
            status="pending",
            operations=[{"type": "rename_node", "node_id": str(root.id), "title": "Sharper title"}],
            rationale="The title is now more specific.",
        )
        db.add(suggestion)
        db.commit()
        db.refresh(suggestion)
        suggestion_id = suggestion.id
        root_id = root.id
    finally:
        db.close()

    response = client.post(f"/api/v2/restructure-suggestions/{suggestion_id}/accept", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["suggestions"] == []
    assert any(node["id"] == str(root_id) and node["title"] == "Sharper title" for node in data["nodes"])

    db = TestingSessionLocal()
    try:
        resolved = db.query(RestructureSuggestion).filter(RestructureSuggestion.id == suggestion_id).one()
        assert resolved.status == "accepted"
        assert resolved.resolved_at is not None
    finally:
        db.close()
