from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from typing import get_args

from app.schemas.v2 import ConversationMessageResponse, RestructureSuggestionResponse, ThinkingNodeResponse, WorkspaceResponse
from app.schemas.v2 import ThinkingMode, ThinkingStage


def test_thinking_node_response_accepts_uuid_orm_fields():
    node = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        parent_id=uuid4(),
        kind="question",
        status="open",
        title="Target user",
        summary=None,
        question="Who is this for?",
        answer_summary=None,
        sort_order=0,
        layout=None,
        source_message_ids=[],
        confidence=100,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    response = ThinkingNodeResponse.model_validate(node)

    assert isinstance(response.id, UUID)
    assert isinstance(response.project_id, UUID)
    assert isinstance(response.parent_id, UUID)


def test_conversation_message_response_accepts_uuid_orm_fields():
    message = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        node_id=uuid4(),
        role="assistant",
        source="chat",
        content="Try this next.",
        thinking_mode="clarify",
        stage="discover",
        message_metadata=None,
        created_at=datetime.now(UTC),
    )

    response = ConversationMessageResponse.model_validate(message)

    assert isinstance(response.id, UUID)
    assert isinstance(response.project_id, UUID)
    assert isinstance(response.node_id, UUID)


def test_restructure_suggestion_response_accepts_uuid_orm_fields():
    suggestion = SimpleNamespace(
        id=uuid4(),
        project_id=uuid4(),
        status="pending",
        operations=[],
        rationale="Map cleanup",
        created_from_message_id=uuid4(),
        created_at=datetime.now(UTC),
        resolved_at=None,
    )

    response = RestructureSuggestionResponse.model_validate(suggestion)

    assert isinstance(response.id, UUID)
    assert isinstance(response.project_id, UUID)
    assert isinstance(response.created_from_message_id, UUID)


def test_workspace_and_message_response_use_tight_schema_types():
    assert WorkspaceResponse.__annotations__["project_id"] is UUID
    assert set(get_args(ConversationMessageResponse.__annotations__["thinking_mode"])) == {ThinkingMode, type(None)}
    assert set(get_args(ConversationMessageResponse.__annotations__["stage"])) == {ThinkingStage, type(None)}
    assert set(get_args(WorkspaceResponse.__annotations__["thinking_mode"])) == {ThinkingMode, type(None)}
    assert set(get_args(WorkspaceResponse.__annotations__["thinking_stage"])) == {ThinkingStage, type(None)}


def test_uuid_fields_serialize_to_json_strings():
    node_id = uuid4()
    project_id = uuid4()
    parent_id = uuid4()
    node = ThinkingNodeResponse(
        id=node_id,
        project_id=project_id,
        parent_id=parent_id,
        kind="question",
        status="open",
        title="Target user",
        summary=None,
        question="Who is this for?",
        answer_summary=None,
        sort_order=0,
        layout=None,
        source_message_ids=[],
        confidence=100,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )

    assert f'"id":"{node_id}"' in node.model_dump_json()
    assert f'"project_id":"{project_id}"' in node.model_dump_json()
    assert f'"parent_id":"{parent_id}"' in node.model_dump_json()

    workspace = WorkspaceResponse(
        project_id=project_id,
        title="V2 workspace",
        thinking_mode="clarify",
        thinking_stage="discover",
        messages=[],
        nodes=[],
        suggestions=[],
    )

    assert f'"project_id":"{project_id}"' in workspace.model_dump_json()
