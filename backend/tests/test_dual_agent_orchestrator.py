from datetime import datetime, timedelta
import json
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import ConversationMessageV2, Project, ThinkingNode
from app.schemas.v2 import BackgroundQuestion, FollowUpQuestion, ReasoningTrace, ThinkingAgentOutput, ThinkingQuestion
from app.services import thinking_agent
from app.services.dual_agent_orchestrator import _apply_node_operations
from app.services.map_agent import build_map_output
from app.services.thinking_agent import run_thinking_agent
from app.services.workspace_context_builder import build_center_context, build_workspace_context


@pytest.fixture(autouse=True)
def db_session(tmp_path):
    test_database_url = f"sqlite:///{tmp_path / 'dual_agent_test.db'}"
    engine = create_engine(test_database_url, connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = testing_session_local()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str):
        self.content = content
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        return _FakeResponse(self.content)


class _FakeChat:
    def __init__(self, content: str):
        self.completions = _FakeCompletions(content)


class _FakeClient:
    def __init__(self, content: str):
        self.chat = _FakeChat(content)


def test_build_center_context_uses_project_title_and_more_info(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="上传推理小说自动生成游戏",
        more_info="目标用户可能是推理小说作者。",
        framework="general",
        status="active",
    )
    db_session.add(project)
    db_session.commit()

    context = build_center_context(project)

    assert context.original_idea == "上传推理小说自动生成游戏"
    assert context.idea_summary == "上传推理小说自动生成游戏"
    assert "推理小说作者" in context.background_summary
    assert context.known_facts == ["目标用户可能是推理小说作者。"]
    assert context.context_sufficiency == "unknown"


def test_build_center_context_uses_summary_snapshot_center_context(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="Fallback title",
        more_info="Fallback background.",
        framework="general",
        status="active",
        summary_snapshot={
            "center_context": {
                "original_idea": "Snapshot idea",
                "idea_summary": "Snapshot summary",
                "background_summary": "Snapshot background",
                "known_facts": ["Fact from previous turn"],
                "assumptions": ["Assumption from previous turn"],
                "context_sufficiency": "sufficient",
            }
        },
    )
    db_session.add(project)
    db_session.commit()

    context = build_center_context(project)

    assert context.original_idea == "Snapshot idea"
    assert context.idea_summary == "Snapshot summary"
    assert context.background_summary == "Snapshot background"
    assert context.known_facts == ["Fact from previous turn"]
    assert context.assumptions == ["Assumption from previous turn"]
    assert context.context_sufficiency == "sufficient"


def test_build_center_context_falls_back_for_non_dict_summary_snapshot_center_context(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="Fallback title",
        more_info="Fallback background.",
        framework="general",
        status="active",
        summary_snapshot={"center_context": "invalid"},
    )
    db_session.add(project)
    db_session.commit()

    context = build_center_context(project)

    assert context.original_idea == "Fallback title"
    assert context.idea_summary == "Fallback title"
    assert context.background_summary == "Fallback background."
    assert context.known_facts == ["Fallback background."]
    assert context.context_sufficiency == "unknown"


def test_build_center_context_falls_back_for_invalid_dict_summary_snapshot_center_context(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="Fallback title",
        more_info="Fallback background.",
        framework="general",
        status="active",
        summary_snapshot={"center_context": {"context_sufficiency": "unknown"}},
    )
    db_session.add(project)
    db_session.commit()

    context = build_center_context(project)

    assert context.original_idea == "Fallback title"
    assert context.background_summary == "Fallback background."


def test_build_center_context_reads_legacy_top_level_summary_snapshot(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="Legacy summary idea",
        more_info="Fallback background.",
        framework="general",
        status="active",
        summary_snapshot={
            "facts": ["用户是推理小说作者"],
            "assumptions": ["作者愿意尝试互动化"],
            "open_questions": ["生成质量如何验证？"],
        },
    )
    db_session.add(project)
    db_session.commit()

    context = build_center_context(project)

    assert context.original_idea == "Legacy summary idea"
    assert context.known_facts == ["用户是推理小说作者"]
    assert context.assumptions == ["作者愿意尝试互动化"]
    assert context.unresolved_context_gaps == ["生成质量如何验证？"]


def test_workspace_context_includes_open_and_answered_nodes(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    root = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        kind="idea",
        status="open",
        title="小说生成游戏",
        source_message_ids=[],
        confidence=100,
    )
    open_node = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        parent_id=root.id,
        kind="question",
        status="open",
        title="目标用户",
        question="谁最需要这个？",
        source_message_ids=[],
        confidence=80,
    )
    answered_node = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        parent_id=root.id,
        kind="question",
        status="answered",
        title="核心体验",
        question="核心体验是什么？",
        answer_summary="破案推理。",
        source_message_ids=[],
        confidence=80,
    )
    db_session.add_all([project, root, open_node, answered_node])
    db_session.commit()

    context = build_workspace_context(
        db_session,
        project,
        user_input={"source": "chat", "content": "补充信息", "answered_node_ids": []},
    )

    assert context["project"]["id"] == str(project.id)
    assert context["project"]["title"] == "小说生成游戏"
    assert context["project"]["original_idea"] == "小说生成游戏"
    assert context["map_state"]["center_node"]["id"] == str(root.id)
    assert len(context["map_state"]["open_question_nodes"]) == 1
    assert context["map_state"]["open_question_nodes"][0]["id"] == str(open_node.id)
    assert len(context["map_state"]["answered_nodes"]) == 1
    assert context["map_state"]["answered_nodes"][0]["id"] == str(answered_node.id)
    assert context["user_input"]["content"] == "补充信息"


def test_workspace_context_includes_open_followup_nodes(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    root = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        kind="idea",
        status="open",
        title="小说生成游戏",
        source_message_ids=[],
        confidence=100,
    )
    followup = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        parent_id=root.id,
        kind="followup",
        status="open",
        title="创作者收益",
        question="作者愿意为什么付费？",
        source_message_ids=[],
        confidence=80,
    )
    db_session.add_all([project, root, followup])
    db_session.commit()

    context = build_workspace_context(db_session, project)

    open_node_ids = {node["id"] for node in context["map_state"]["open_question_nodes"]}
    assert str(followup.id) in open_node_ids


def test_dual_agent_applier_persists_followup_operation_as_followup_node(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    root = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        kind="idea",
        status="open",
        title="小说生成游戏",
        source_message_ids=[],
        confidence=100,
    )
    parent_question = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        parent_id=root.id,
        kind="question",
        status="open",
        title="目标用户",
        question="谁最需要这个？",
        source_message_ids=[],
        confidence=80,
    )
    db_session.add_all([project, root, parent_question])
    db_session.flush()

    created_nodes = _apply_node_operations(
        db_session,
        project,
        [
            {
                "type": "create_question_node",
                "parent_id": str(root.id),
                "title": "核心体验",
                "detail_question": "核心体验是什么？",
                "status": "open",
            },
            {
                "type": "create_followup_node",
                "parent_id": str(parent_question.id),
                "title": "当前替代方案",
                "detail_question": "用户现在怎么解决？",
                "status": "open",
            },
        ],
    )
    db_session.commit()

    persisted_nodes = {
        node.title: node
        for node in db_session.query(ThinkingNode)
        .filter(ThinkingNode.id.in_([node.id for node in created_nodes]))
        .all()
    }
    assert persisted_nodes["核心体验"].kind == "question"
    assert persisted_nodes["当前替代方案"].kind == "followup"


def test_workspace_context_recent_conversation_returns_last_12_chronologically(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    base_time = datetime(2026, 4, 26, 10, 0, 0)
    messages = [
        ConversationMessageV2(
            id=uuid4(),
            project_id=project.id,
            role="user" if index % 2 == 0 else "assistant",
            source="chat",
            content=f"message-{index:02d}",
            created_at=base_time + timedelta(minutes=index),
        )
        for index in range(15)
    ]
    db_session.add(project)
    db_session.add_all(messages)
    db_session.commit()

    context = build_workspace_context(db_session, project)

    assert [message["content"] for message in context["recent_conversation"]] == [
        f"message-{index:02d}" for index in range(3, 15)
    ]


def test_workspace_context_defaults_user_input(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    db_session.add(project)
    db_session.commit()

    context = build_workspace_context(db_session, project)

    assert context["user_input"] == {"source": "chat", "content": "", "answered_node_ids": []}


def test_workspace_context_includes_focused_node(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    focused_node = ThinkingNode(
        id=uuid4(),
        project_id=project.id,
        kind="question",
        status="open",
        title="核心体验",
        question="核心体验是什么？",
        source_message_ids=[],
        confidence=80,
    )
    db_session.add_all([project, focused_node])
    db_session.commit()

    context = build_workspace_context(db_session, project, focused_node=focused_node)

    assert context["map_state"]["focused_node"]["id"] == str(focused_node.id)
    assert context["map_state"]["focused_node"]["question"] == "核心体验是什么？"


def test_workspace_context_ignores_focused_node_from_other_project(db_session):
    project = Project(
        id=uuid4(),
        user_id=uuid4(),
        title="小说生成游戏",
        framework="general",
        status="active",
    )
    other_project_id = uuid4()
    focused_node = ThinkingNode(
        id=uuid4(),
        project_id=other_project_id,
        kind="question",
        status="open",
        title="其他项目问题",
        question="不应该进入上下文",
        source_message_ids=[],
        confidence=80,
    )
    db_session.add(project)
    db_session.add(focused_node)
    db_session.commit()

    context = build_workspace_context(db_session, project, focused_node=focused_node)

    assert context["map_state"]["focused_node"] is None


def test_thinking_agent_fallback_asks_background_questions_when_context_sparse(monkeypatch):
    monkeypatch.setattr(thinking_agent, "get_ai_client", lambda: None)
    context = {
        "project": {
            "title": "上传推理小说自动生成游戏",
            "original_idea": "上传推理小说自动生成游戏",
        }
    }

    output = run_thinking_agent(context, ai_func=None)

    assert output.context_sufficiency == "insufficient"
    assert 3 <= len(output.background_questions) <= 6
    assert output.thinking_questions == []
    assert "background" in output.reasoning_trace.visible_summary.lower() or "信息" in output.reasoning_trace.visible_summary
    joined_questions = " ".join(question.question for question in output.background_questions)
    assert "用户" in joined_questions
    assert "痛点" in joined_questions or "替代" in joined_questions
    assert "核心体验" in joined_questions
    assert "输入" in joined_questions


def test_thinking_agent_fallback_generates_question_batch_when_context_rich(monkeypatch):
    monkeypatch.setattr(thinking_agent, "get_ai_client", lambda: None)
    context = {
        "project": {
            "original_idea": "上传推理小说自动生成推理游戏",
            "background_summary": "作者希望把完整推理小说转换成可互动的破案体验。",
            "known_facts": ["作者会上传现有小说", "系统需要保留关键线索和真相"],
            "target_users": ["推理小说作者", "互动叙事玩家"],
        }
    }

    output = run_thinking_agent(context, ai_func=None)

    assert output.context_sufficiency == "sufficient"
    assert len(output.thinking_questions) == 3
    assert output.background_questions == []
    assert all(question.short_title for question in output.thinking_questions)
    joined_questions = " ".join(
        f"{question.short_title} {question.question}" for question in output.thinking_questions
    )
    assert "用户" in joined_questions
    assert "核心体验" in joined_questions
    assert "质量" in joined_questions


def test_thinking_agent_rejects_empty_ai_output_and_falls_back(monkeypatch):
    payload = json.dumps(
        {
            "context_sufficiency": "sufficient",
            "background_questions": [],
            "thinking_questions": [],
            "follow_up_questions": [],
            "answer_matches": [],
            "reasoning_trace": {"visible_summary": "empty", "audit_notes": {}},
        }
    )
    monkeypatch.setattr(thinking_agent, "get_ai_client", lambda: _FakeClient(payload))
    monkeypatch.setattr(thinking_agent, "get_model", lambda: "test-model")
    context = {
        "project": {
            "original_idea": "上传推理小说自动生成推理游戏",
            "background_summary": "作者希望把完整推理小说转换成可互动的破案体验。",
            "known_facts": ["作者会上传现有小说"],
            "target_users": ["推理小说作者"],
        }
    }

    output = run_thinking_agent(context)

    assert output.context_sufficiency == "sufficient"
    assert len(output.thinking_questions) == 3
    assert output.reasoning_trace.audit_notes["fallback"] is True


def test_thinking_agent_rejects_wrong_branch_ai_output_and_falls_back(monkeypatch):
    payload = json.dumps(
        {
            "context_sufficiency": "insufficient",
            "background_questions": [
                {
                    "question": "谁是用户？",
                    "why_needed": "test",
                    "expected_signal": "test",
                },
                {
                    "question": "痛点是什么？",
                    "why_needed": "test",
                    "expected_signal": "test",
                },
                {
                    "question": "输入是什么？",
                    "why_needed": "test",
                    "expected_signal": "test",
                },
            ],
            "thinking_questions": [],
            "follow_up_questions": [],
            "answer_matches": [],
            "reasoning_trace": {"visible_summary": "wrong branch", "audit_notes": {}},
        }
    )
    monkeypatch.setattr(thinking_agent, "get_ai_client", lambda: _FakeClient(payload))
    monkeypatch.setattr(thinking_agent, "get_model", lambda: "test-model")
    context = {
        "project": {
            "original_idea": "上传推理小说自动生成推理游戏",
            "background_summary": "作者希望把完整推理小说转换成可互动的破案体验。",
            "known_facts": ["作者会上传现有小说"],
            "target_users": ["推理小说作者"],
        }
    }

    output = run_thinking_agent(context)

    assert output.context_sufficiency == "sufficient"
    assert len(output.thinking_questions) == 3
    assert output.background_questions == []
    assert output.reasoning_trace.audit_notes["fallback"] is True


def test_thinking_agent_fallback_generates_followups_for_focused_node(monkeypatch):
    monkeypatch.setattr(thinking_agent, "get_ai_client", lambda: None)
    parent_id = uuid4()
    context = {
        "project": {
            "original_idea": "上传推理小说自动生成推理游戏",
            "background_summary": "作者希望把完整推理小说转换成可互动的破案体验。",
            "known_facts": ["作者会上传现有小说"],
            "target_users": ["推理小说作者"],
        },
        "map_state": {
            "focused_node": {
                "id": str(parent_id),
                "kind": "question",
                "status": "answered",
                "title": "核心体验",
                "question": "核心体验是什么？",
                "answer_summary": "把小说线索转成玩家可以逐步推理的案件。",
            }
        },
        "user_input": {"content": "玩家需要通过证据链推理出真相。"},
    }

    output = run_thinking_agent(context, ai_func=None)

    assert output.context_sufficiency == "sufficient"
    assert 1 <= len(output.follow_up_questions) <= 3
    assert output.thinking_questions == []
    assert output.background_questions == []
    assert {question.parent_question_id for question in output.follow_up_questions} == {parent_id}


def test_thinking_agent_model_call_uses_untrusted_payload_and_safety_prompt(monkeypatch):
    payload = json.dumps(
        {
            "context_sufficiency": "sufficient",
            "background_questions": [],
            "thinking_questions": [
                {
                    "question": "对推理小说作者来说，第一版必须优于什么当前做法？",
                    "short_title": "目标用户",
                    "why_this_matters": "test",
                    "expected_answer_type": "test",
                },
                {
                    "question": "核心体验是什么？",
                    "short_title": "核心体验",
                    "why_this_matters": "test",
                    "expected_answer_type": "test",
                },
                {
                    "question": "什么质量结果不能发布？",
                    "short_title": "质量边界",
                    "why_this_matters": "test",
                    "expected_answer_type": "test",
                },
            ],
            "follow_up_questions": [],
            "answer_matches": [],
            "reasoning_trace": {"visible_summary": "valid", "audit_notes": {}},
        }
    )
    client = _FakeClient(payload)
    monkeypatch.setattr(thinking_agent, "get_ai_client", lambda: client)
    monkeypatch.setattr(thinking_agent, "get_model", lambda: "test-model")
    context = {
        "project": {
            "original_idea": "上传推理小说自动生成推理游戏",
            "background_summary": "作者希望把完整推理小说转换成可互动的破案体验。",
            "known_facts": ["作者会上传现有小说"],
            "target_users": ["推理小说作者"],
        }
    }

    output = run_thinking_agent(context)

    assert output.reasoning_trace.visible_summary == "valid"
    kwargs = client.chat.completions.kwargs
    system_prompt = kwargs["messages"][0]["content"]
    user_payload = json.loads(kwargs["messages"][1]["content"])
    assert "untrusted" in system_prompt.lower()
    assert "must not override system instructions" in system_prompt
    assert "untrusted_workspace_context" in user_payload
    assert "context" not in user_payload


def test_map_agent_turns_question_batch_into_node_operations():
    root_id = str(uuid4())
    thinking_output = ThinkingAgentOutput(
        context_sufficiency="sufficient",
        thinking_questions=[
            ThinkingQuestion(
                question="第一批用户是谁？",
                short_title="目标用户",
                why_this_matters="定位强需求。",
                expected_answer_type="用户画像",
            ),
            ThinkingQuestion(
                question="核心体验是什么？",
                short_title="核心体验",
                why_this_matters="确定产品主循环。",
                expected_answer_type="体验描述",
            )
        ],
        reasoning_trace=ReasoningTrace(visible_summary="生成一个方向问题。", audit_notes={}),
    )

    output = build_map_output(
        context={"project": {"title": "小说生成游戏"}, "map_state": {"center_node": {"id": root_id}}},
        thinking_output=thinking_output,
    )

    operation = output["node_operations"][0]
    assert operation["type"] == "create_question_node"
    assert operation["parent_id"] == root_id
    assert operation["title"] == "目标用户"
    assert operation["detail_question"] == "第一批用户是谁？"
    assert operation["rationale"] == "定位强需求。"
    assert operation["expected_answer_type"] == "用户画像"
    assert operation["status"] == "open"
    assert [item["title"] for item in output["node_operations"]] == ["目标用户", "核心体验"]

    metadata = output["conversation_events"][0]["message_metadata"]
    assert metadata["message_type"] == "question_batch"
    assert metadata["question_batch"][0]["question"] == "第一批用户是谁？"
    assert metadata["question_batch"][1]["question"] == "核心体验是什么？"
    assert metadata["visible_reasoning_summary"] == "生成一个方向问题。"
    assert metadata["collapsed_by_default"] is True
    assert output["center_node_patch"]["context_sufficiency"] == "sufficient"
    assert output["center_node_patch"]["title"] == "小说生成游戏"
    assert output["center_node_patch"]["idea_summary"] == "小说生成游戏"


def test_map_agent_turns_background_questions_into_conversation_event():
    root_id = str(uuid4())
    thinking_output = ThinkingAgentOutput(
        context_sufficiency="insufficient",
        background_questions=[
            BackgroundQuestion(
                question="谁已经明确需要这个小说生成游戏？",
                why_needed="需要先确认目标用户。",
                expected_signal="目标用户画像",
            )
        ],
        reasoning_trace=ReasoningTrace(visible_summary="需要补足背景信息。", audit_notes={}),
    )

    output = build_map_output(
        context={"project": {"title": "小说生成游戏"}, "map_state": {"center_node": {"id": root_id}}},
        thinking_output=thinking_output,
    )

    assert output["node_operations"] == []
    assert output["center_node_patch"]["context_sufficiency"] == "insufficient"
    assert output["center_node_patch"]["unresolved_context_gaps"] == ["目标用户画像"]
    assert output["center_node_patch"]["title"] == "小说生成游戏"
    assert output["center_node_patch"]["idea_summary"] == "小说生成游戏"

    event = output["conversation_events"][0]
    assert event["role"] == "assistant"
    assert event["source"] == "system"

    metadata = event["message_metadata"]
    assert metadata["message_type"] == "background_question_batch"
    assert metadata["background_questions"][0] == {
        "question": "谁已经明确需要这个小说生成游戏？",
        "why_needed": "需要先确认目标用户。",
        "expected_signal": "目标用户画像",
    }
    assert metadata["visible_reasoning_summary"] == "需要补足背景信息。"
    assert metadata["collapsed_by_default"] is True


def test_map_agent_does_not_create_question_nodes_without_center_node():
    thinking_output = ThinkingAgentOutput(
        context_sufficiency="sufficient",
        thinking_questions=[
            ThinkingQuestion(
                question="第一批用户是谁？",
                short_title="目标用户",
                why_this_matters="定位强需求。",
                expected_answer_type="用户画像",
            )
        ],
        reasoning_trace=ReasoningTrace(visible_summary="保留问题展示但不建图。", audit_notes={}),
    )

    output = build_map_output(
        context={"project": {"title": "小说生成游戏"}, "map_state": {"center_node": {}}},
        thinking_output=thinking_output,
    )

    assert output["node_operations"] == []
    assert output["center_node_patch"]["context_sufficiency"] == "sufficient"
    assert output["center_node_patch"]["title"] == "小说生成游戏"
    assert output["center_node_patch"]["idea_summary"] == "小说生成游戏"
    metadata = output["conversation_events"][0]["message_metadata"]
    assert metadata["message_type"] == "question_batch"
    assert metadata["question_batch"][0]["question"] == "第一批用户是谁？"
    assert metadata["visible_reasoning_summary"] == "保留问题展示但不建图。"
    assert metadata["collapsed_by_default"] is True


def test_map_agent_turns_follow_up_questions_into_followup_operations():
    parent_id = uuid4()
    thinking_output = ThinkingAgentOutput(
        context_sufficiency="sufficient",
        follow_up_questions=[
            FollowUpQuestion(
                parent_question_id=parent_id,
                question="这个用户当前怎么解决？",
                short_title="替代方案",
                why_this_matters="确认强痛点。",
                expected_answer_type="现有流程",
            )
        ],
        reasoning_trace=ReasoningTrace(visible_summary="针对已答节点追问。", audit_notes={}),
    )

    output = build_map_output(
        context={"project": {"title": "小说生成游戏"}, "map_state": {"center_node": {"id": str(uuid4())}}},
        thinking_output=thinking_output,
    )

    operation = output["node_operations"][0]
    assert operation["type"] == "create_followup_node"
    assert operation["parent_id"] == str(parent_id)
    assert operation["title"] == "替代方案"
    assert operation["detail_question"] == "这个用户当前怎么解决？"
    assert operation["rationale"] == "确认强痛点。"
    assert operation["expected_answer_type"] == "现有流程"
    assert operation["status"] == "open"

    metadata = output["conversation_events"][0]["message_metadata"]
    assert metadata["message_type"] == "assistant_followup"
    assert metadata["linked_node_ids"] == [str(parent_id)]
    assert metadata["question_batch"][0]["question"] == "这个用户当前怎么解决？"
    assert metadata["follow_up_questions"][0]["parent_question_id"] == str(parent_id)
    assert metadata["visible_reasoning_summary"] == "针对已答节点追问。"
    assert metadata["collapsed_by_default"] is True
    assert output["center_node_patch"]["context_sufficiency"] == "sufficient"
    assert output["center_node_patch"]["title"] == "小说生成游戏"
    assert output["center_node_patch"]["idea_summary"] == "小说生成游戏"
