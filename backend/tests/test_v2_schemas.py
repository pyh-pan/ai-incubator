from datetime import UTC, datetime
from types import SimpleNamespace
from typing import get_args
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.schemas.v2 import (
    AnswerMatchResponse,
    CenterContext,
    ConversationMessageResponse,
    MapOperation,
    RestructureSuggestionResponse,
    ThinkingAgentOutput,
    ThinkingNodeResponse,
    ThinkingQuestion,
    TurnRequest,
    WorkspaceResponse,
)
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


def test_thinking_agent_output_accepts_question_batch():
    output = ThinkingAgentOutput(
        context_sufficiency="sufficient",
        thinking_questions=[
            ThinkingQuestion(
                question="谁会最迫切地使用这个产品？他们现在如何解决？",
                short_title="目标用户",
                why_this_matters="先定位强需求人群，避免泛泛讨论功能。",
                expected_answer_type="具体用户画像和当前替代方案",
            )
        ],
        reasoning_trace={
            "visible_summary": "背景足够，先从目标用户切入。",
            "audit_notes": {"signal": "has idea and background"},
        },
    )

    assert output.context_sufficiency == "sufficient"
    assert output.thinking_questions[0].short_title == "目标用户"
    assert output.background_questions == []


def test_workspace_response_exposes_center_context_and_matches():
    response_fields = WorkspaceResponse.model_fields

    assert "center_context" in response_fields
    assert "answer_matches" in response_fields
    assert CenterContext.model_fields["context_sufficiency"]
    assert AnswerMatchResponse.model_fields["confidence"]


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
        center_context=CenterContext(original_idea="V2 workspace"),
        messages=[],
        nodes=[],
        suggestions=[],
    )

    assert f'"project_id":"{project_id}"' in workspace.model_dump_json()


def test_map_operation_rejects_invalid_node_id_uuid():
    with pytest.raises(ValidationError):
        MapOperation(type="update_node", node_id="not-a-uuid", summary="Updated summary")


def test_map_operation_rejects_invalid_parent_id_uuid():
    with pytest.raises(ValidationError):
        MapOperation(type="move_node", node_id=str(uuid4()), parent_id="not-a-uuid")


def test_map_operation_rejects_invalid_source_node_ids_uuid():
    with pytest.raises(ValidationError):
        MapOperation(type="merge_nodes", source_node_ids=[str(uuid4()), "not-a-uuid"])


def test_turn_request_rejects_invalid_node_id_uuid():
    with pytest.raises(ValidationError):
        TurnRequest(content="Continue", node_id="not-a-uuid")
