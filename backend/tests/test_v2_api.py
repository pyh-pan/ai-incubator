from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.core.security import create_access_token
from app.main import app
from app.models import ConversationMessageV2, Project, RestructureSuggestion, ThinkingNode, User
from app.services.incubator_orchestrator import run_turn
from app.schemas.v2 import AIMapUpdate, AIOrchestratorOutput, CurrentSummary, MapOperation, TurnRequest


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


def test_sparse_workspace_bootstraps_background_question_batch(client, project_id, auth_headers):
    response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == str(project_id)
    assert data["title"] == "AI Incubator v2"
    assert data["center_context"]["context_sufficiency"] == "insufficient"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "assistant"
    assert data["messages"][0]["content"]
    assert data["messages"][0]["message_metadata"]["message_type"] == "background_question_batch"
    assert 3 <= len(data["messages"][0]["message_metadata"]["background_questions"]) <= 6
    assert data["suggestions"] == []
    assert len(data["nodes"]) == 1

    root = next(node for node in data["nodes"] if node["parent_id"] is None)
    assert root["kind"] == "idea"
    assert root["title"] == "AI Incubator v2"
    assert [node["kind"] for node in data["nodes"]].count("question") == 0


def test_rich_workspace_bootstraps_question_nodes(client, user, auth_headers):
    db = TestingSessionLocal()
    try:
        project = Project(
            user_id=user.id,
            title="上传推理小说自动生成游戏",
            more_info="目标用户是推理小说作者，希望把作品转成可互动破案体验。核心体验是破案推理，输入是完整小说文本。",
            framework="general",
            status="active",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        rich_project_id = project.id
    finally:
        db.close()

    response = client.get(f"/api/v2/projects/{rich_project_id}/workspace", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["center_context"]["context_sufficiency"] == "sufficient"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["message_metadata"]["message_type"] == "question_batch"
    question_nodes = [node for node in data["nodes"] if node["kind"] == "question"]
    assert 3 <= len(question_nodes) <= 5
    assert all(node["parent_id"] is not None for node in question_nodes)


def test_node_answer_marks_node_answered_and_creates_followups(client, auth_headers):
    create_response = client.post(
        "/api/projects",
        json={
            "title": "上传推理小说自动生成游戏",
            "more_info": "目标用户是推理小说作者，希望把作品转成可互动破案体验。核心体验是破案推理，输入是完整小说文本。",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    workspace_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)
    assert workspace_response.status_code == 200
    question_node = next(node for node in workspace_response.json()["nodes"] if node["kind"] == "question")

    response = client.post(
        f"/api/v2/projects/{project_id}/nodes/{question_node['id']}/answer",
        json={"content": "作者最需要在发稿前验证读者能不能跟上核心诡计，所以第一版应先生成可玩的推理测试流程。"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    answered_node = next(node for node in data["nodes"] if node["id"] == question_node["id"])
    assert answered_node["status"] == "answered"
    assert answered_node["answer_summary"]

    children = [node for node in data["nodes"] if node["parent_id"] == question_node["id"]]
    assert 1 <= len(children) <= 3
    assert all(node["kind"] == "followup" for node in children)

    messages = data["messages"]
    user_message = next(message for message in messages if message["role"] == "user" and message["node_id"] == question_node["id"])
    assert user_message["source"] == "node"
    assert user_message["message_metadata"]["message_type"] == "user_answer"
    assert user_message["message_metadata"]["linked_node_ids"] == [question_node["id"]]
    assert any(
        message["role"] == "assistant"
        and message["message_metadata"]["message_type"] == "assistant_followup"
        for message in messages
    )


def test_node_answer_missing_or_other_project_node_returns_404(client, auth_headers):
    create_response = client.post(
        "/api/projects",
        json={"title": "Owned project", "more_info": "目标用户是独立开发者，核心体验是梳理产品想法。"},
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    missing_response = client.post(
        f"/api/v2/projects/{project_id}/nodes/{uuid4()}/answer",
        json={"content": "Answer"},
        headers=auth_headers,
    )
    assert missing_response.status_code == 404

    other_response = client.post(
        "/api/projects",
        json={
            "title": "Other project",
            "more_info": "目标用户是小说作者，希望把作品转成可互动破案体验。核心体验是验证剧情，输入是完整小说文本。",
        },
        headers=auth_headers,
    )
    assert other_response.status_code == 201
    other_project_id = other_response.json()["id"]
    other_workspace = client.get(f"/api/v2/projects/{other_project_id}/workspace", headers=auth_headers)
    assert other_workspace.status_code == 200
    other_node = next(node for node in other_workspace.json()["nodes"] if node["kind"] == "question")

    cross_project_response = client.post(
        f"/api/v2/projects/{project_id}/nodes/{other_node['id']}/answer",
        json={"content": "Answer"},
        headers=auth_headers,
    )
    assert cross_project_response.status_code == 404


def test_node_answer_rejects_center_node(client, project_id, auth_headers):
    workspace_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)
    assert workspace_response.status_code == 200
    center_node = next(node for node in workspace_response.json()["nodes"] if node["kind"] == "idea")

    response = client.post(
        f"/api/v2/projects/{project_id}/nodes/{center_node['id']}/answer",
        json={"content": "中心节点只承载初始想法和背景信息，不作为普通问题回答。"},
        headers=auth_headers,
    )

    assert response.status_code == 400


def test_chat_background_answer_updates_center_and_creates_question_batch(client, project_id, auth_headers):
    bootstrap_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)
    assert bootstrap_response.status_code == 200
    assert bootstrap_response.json()["center_context"]["context_sufficiency"] == "insufficient"

    response = client.post(
        f"/api/v2/projects/{project_id}/turns",
        json={
            "content": "目标用户是推理小说作者，核心体验是把完整小说文本变成可玩的破案推理流程，输入是完整小说文本。",
            "source": "chat",
        },
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["center_context"]["context_sufficiency"] == "sufficient"
    assert "推理小说作者" in data["center_context"]["background_summary"]
    assert [node for node in data["nodes"] if node["kind"] == "question"]
    assert data["assistant_message"]["message_metadata"]["message_type"] == "question_batch"


def test_chat_batch_answer_marks_matched_open_nodes(client, user, auth_headers):
    db = TestingSessionLocal()
    try:
        project = Project(
            user_id=user.id,
            title="上传推理小说自动生成游戏",
            more_info="目标用户是推理小说作者，希望把作品转成可互动破案体验。核心体验是破案推理，输入是完整小说文本。",
            framework="general",
            status="active",
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        rich_project_id = project.id
    finally:
        db.close()

    workspace_response = client.get(f"/api/v2/projects/{rich_project_id}/workspace", headers=auth_headers)
    assert workspace_response.status_code == 200
    question_nodes = [node for node in workspace_response.json()["nodes"] if node["kind"] == "question"]
    assert len(question_nodes) >= 2
    batch_content = "。".join(f"{node['title']}：我的回答是先做一个可验证的最小体验" for node in question_nodes[:2])

    response = client.post(
        f"/api/v2/projects/{rich_project_id}/turns",
        json={"content": batch_content, "source": "chat"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    answered_ids = {node["id"] for node in data["nodes"] if node["status"] == "answered"}
    assert {node["id"] for node in question_nodes[:2]}.issubset(answered_ids)
    user_message = next(message for message in data["messages"] if message["id"] == data["user_message"]["id"])
    assert user_message["message_metadata"]["message_type"] == "batch_answer"


def test_delete_project_after_workspace_bootstrap_removes_project(client, auth_headers):
    create_response = client.post(
        "/api/projects",
        json={
            "title": "Project to delete",
            "more_info": "目标用户是推理小说作者，希望把作品转成可互动破案体验。核心体验是破案推理，输入是完整小说文本。",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    project_id = create_response.json()["id"]

    workspace_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)
    assert workspace_response.status_code == 200
    assert len(workspace_response.json()["nodes"]) > 1

    delete_response = client.delete(f"/api/projects/{project_id}", headers=auth_headers)

    assert delete_response.status_code == 204
    list_response = client.get("/api/projects", headers=auth_headers)
    assert project_id not in [project["id"] for project in list_response.json()]


def test_repeated_workspace_fetch_does_not_create_duplicate_bootstrap_records(client, project_id, auth_headers):
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

        assistant_messages = (
            db.query(ConversationMessageV2)
            .filter(
                ConversationMessageV2.project_id == project_id,
                ConversationMessageV2.role == "assistant",
            )
            .all()
        )
        assert len(assistant_messages) == 1

        question_nodes = (
            db.query(ThinkingNode)
            .filter(
                ThinkingNode.project_id == project_id,
                ThinkingNode.kind == "question",
            )
            .all()
        )
        assert len(question_nodes) == 0
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


def test_turn_creates_chat_messages_and_background_questions(client, project_id, auth_headers):
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
    assert data["assistant_message"]["message_metadata"]["message_type"] == "background_question_batch"

    messages = data["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert data["center_context"]["context_sufficiency"] == "insufficient"


def test_turn_preserves_center_context_after_rich_bootstrap(client, auth_headers):
    response = client.post(
        "/api/projects",
        json={
            "title": "上传推理小说自动生成游戏",
            "more_info": "目标用户是推理小说作者，希望把作品转成可互动破案体验。核心体验是破案推理，输入是完整小说文本。",
        },
        headers=auth_headers,
    )
    project_id = response.json()["id"]
    workspace_response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)
    assert workspace_response.json()["center_context"]["context_sufficiency"] == "sufficient"

    turn_response = client.post(
        f"/api/v2/projects/{project_id}/turns",
        json={"content": "目标用户是推理小说作者。"},
        headers=auth_headers,
    )

    assert turn_response.status_code == 200
    assert turn_response.json()["center_context"]["context_sufficiency"] == "sufficient"


def test_run_turn_ignores_node_id_from_other_project(user):
    db = TestingSessionLocal()
    try:
        user = db.merge(user)
        project = Project(user_id=user.id, title="Owned project", framework="general", status="active")
        other_project = Project(user_id=user.id, title="Other project", framework="general", status="active")
        db.add_all([project, other_project])
        db.flush()
        other_node = ThinkingNode(
            project_id=other_project.id,
            kind="question",
            status="open",
            title="Other node",
            source_message_ids=[],
            confidence=80,
        )
        db.add(other_node)
        db.commit()
        db.refresh(project)
        db.refresh(other_node)

        run_turn(db, project, TurnRequest(content="Answer", node_id=other_node.id))

        message = (
            db.query(ConversationMessageV2)
            .filter(ConversationMessageV2.project_id == project.id, ConversationMessageV2.role == "user")
            .one()
        )
        assert message.node_id is None
    finally:
        db.close()


def test_run_turn_falls_back_to_root_for_cross_project_ai_parent(user):
    db = TestingSessionLocal()
    try:
        user = db.merge(user)
        project = Project(user_id=user.id, title="Owned project", framework="general", status="active")
        other_project = Project(user_id=user.id, title="Other project", framework="general", status="active")
        db.add_all([project, other_project])
        db.flush()
        other_parent = ThinkingNode(
            project_id=other_project.id,
            kind="idea",
            status="open",
            title="Other root",
            source_message_ids=[],
            confidence=100,
        )
        db.add(other_parent)
        db.commit()
        db.refresh(project)
        db.refresh(other_parent)

        def fake_ai(content, mode, context):
            return AIOrchestratorOutput(
                thinking_mode="clarify",
                stage="discover",
                mode_reason="test",
                assistant_message="assistant",
                next_question="next?",
                question_intent="test",
                map_updates=[
                    AIMapUpdate(
                        operation=MapOperation(
                            type="create_node",
                            parent_id=other_parent.id,
                            title="Unsafe parent",
                            kind="question",
                            question="Should not attach to other project.",
                        ),
                        risk="low",
                    )
                ],
                current_summary=CurrentSummary(facts=["fact"]),
            )

        run_turn(db, project, TurnRequest(content="Answer"), ai_func=fake_ai)

        root = (
            db.query(ThinkingNode)
            .filter(ThinkingNode.project_id == project.id, ThinkingNode.parent_id.is_(None))
            .one()
        )
        child = (
            db.query(ThinkingNode)
            .filter(ThinkingNode.project_id == project.id, ThinkingNode.title == "Unsafe parent")
            .one()
        )
        assert child.parent_id == root.id
    finally:
        db.close()


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
