from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import UUID, uuid4

from app.schemas.v2 import ConversationMessageResponse, RestructureSuggestionResponse, ThinkingNodeResponse


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
