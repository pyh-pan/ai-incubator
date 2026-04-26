# Dual Agent Mindmap Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the current shallow one-question workspace with a two-agent, batch-question, XMind-style thinking workspace that supports background completion, multi-node answers, and node-scoped follow-ups.

**Architecture:** Keep the backend as the source of truth. Add schema-constrained Thinking Agent and Map Agent service layers that produce validated workspace operations. The frontend renders richer message/node metadata, a two-column resizable layout, XMind Clean map styling, and node popovers without owning business state.

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic v2, pytest, React 19, TypeScript, Vite, TanStack Query, Ant Design, MindElixir, Vitest/Testing Library.

---

## File Structure

Backend files:

- Create `backend/app/services/workspace_context_builder.py`: builds `WorkspaceContext` from project, messages, nodes, selected node, and user input.
- Create `backend/app/services/dual_agent_orchestrator.py`: coordinates Thinking Agent, Map Agent, validation, fallback, and operation application.
- Create `backend/app/services/thinking_agent.py`: schema models, model call wrapper, deterministic thinking fallback.
- Create `backend/app/services/map_agent.py`: schema models, map operation generation, deterministic map fallback, operation applier.
- Create `backend/tests/test_dual_agent_orchestrator.py`: core behavior for background completion, question batches, node answers, and fallback.
- Create `backend/tests/test_answer_matching.py`: batch-answer matching and confirmation behavior.
- Modify `backend/app/schemas/v2.py`: richer response/request schemas and metadata types.
- Modify `backend/app/api/v2.py`: workspace bootstrapping, `/nodes/{node_id}/answer`, answer-match confirmation endpoint.
- Modify `backend/app/services/incubator_orchestrator.py`: either delegate v2 flow to `dual_agent_orchestrator.py` or reduce it to legacy compatibility helpers.
- Modify `backend/app/models/v2.py`: add a focused `AnswerMatchConfirmation` model only if needed by Task 6.

Frontend files:

- Modify `frontend/src/types/incubator.ts`: add metadata, center context, answer match, and node answer types.
- Modify `frontend/src/api/incubator.ts`: add node-answer and match-confirm calls.
- Modify `frontend/src/hooks/useIncubatorSession.ts`: expose `answerNode`, `confirmAnswerMatch`, and richer pending states.
- Modify `frontend/src/pages/IncubatorWorkspacePage.tsx`: two-column resizable layout and remove `NodeInspector`.
- Modify `frontend/src/components/incubator/ChatPanel.tsx`: render typed message blocks, collapsible thinking traces, batches, and match confirmations.
- Replace `frontend/src/components/incubator/MindmapCanvas.tsx`: XMind Clean styling, selected node handling, popover state.
- Create `frontend/src/components/incubator/NodePopover.tsx`: center-node and ordinary-question popovers.
- Modify `frontend/src/components/incubator/thinkingMapAdapter.ts`: concise node topics and stable tree conversion.
- Create/modify frontend tests under `frontend/src/test/incubator/`.

## Task 1: Backend Schemas for Dual-Agent Workspace

**Files:**
- Modify: `backend/app/schemas/v2.py`
- Test: `backend/tests/test_v2_schemas.py`

- [ ] **Step 1: Write schema tests**

Append these tests to `backend/tests/test_v2_schemas.py`:

```python
from app.schemas.v2 import (
    AnswerMatchResponse,
    CenterContext,
    ThinkingAgentOutput,
    ThinkingQuestion,
    WorkspaceResponse,
)


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
```

- [ ] **Step 2: Run schema tests to verify failure**

Run:

```bash
cd backend
DATABASE_URL=sqlite:///./schema_test.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_v2_schemas.py -q -o addopts=''
```

Expected: fails because `ThinkingAgentOutput`, `ThinkingQuestion`, `CenterContext`, and `AnswerMatchResponse` do not exist.

- [ ] **Step 3: Add schema models**

Add these models to `backend/app/schemas/v2.py` near the existing v2 schemas:

```python
ContextSufficiency = Literal["unknown", "insufficient", "sufficient"]
AnswerMatchConfidence = Literal["high", "medium", "low"]


class CenterContext(BaseModel):
    original_idea: str
    idea_summary: str | None = None
    background_summary: str | None = None
    known_facts: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    target_users: list[str] = Field(default_factory=list)
    desired_outcomes: list[str] = Field(default_factory=list)
    unresolved_context_gaps: list[str] = Field(default_factory=list)
    context_sufficiency: ContextSufficiency = "unknown"


class ReasoningTrace(BaseModel):
    visible_summary: str
    audit_notes: dict[str, Any] = Field(default_factory=dict)


class BackgroundQuestion(BaseModel):
    question: str
    why_needed: str
    expected_signal: str


class ThinkingQuestion(BaseModel):
    question: str
    short_title: str
    why_this_matters: str
    expected_answer_type: str


class FollowUpQuestion(ThinkingQuestion):
    parent_question_id: UUID


class AnswerMatch(BaseModel):
    node_id: UUID
    extracted_answer: str
    confidence: AnswerMatchConfidence


class ThinkingAgentOutput(BaseModel):
    context_sufficiency: Literal["insufficient", "sufficient"]
    background_questions: list[BackgroundQuestion] = Field(default_factory=list)
    thinking_questions: list[ThinkingQuestion] = Field(default_factory=list)
    follow_up_questions: list[FollowUpQuestion] = Field(default_factory=list)
    answer_matches: list[AnswerMatch] = Field(default_factory=list)
    reasoning_trace: ReasoningTrace


class AnswerMatchResponse(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    matches: list[AnswerMatch]
    original_content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class NodeAnswerRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
```

Extend existing literals:

```python
NodeKind = Literal["idea", "question", "answer", "insight", "assumption", "decision", "risk", "next_step", "followup"]
NodeStatus = Literal["open", "answered", "suggested", "confirmed", "needs_context", "resolved"]
```

Extend `WorkspaceResponse`:

```python
class WorkspaceResponse(BaseModel):
    project_id: UUID
    title: str
    thinking_mode: ThinkingMode | None
    thinking_stage: ThinkingStage | None
    center_context: CenterContext
    messages: list[ConversationMessageResponse]
    nodes: list[ThinkingNodeResponse]
    suggestions: list[RestructureSuggestionResponse]
    answer_matches: list[AnswerMatchResponse] = Field(default_factory=list)
```

- [ ] **Step 4: Run schema tests to verify pass**

Run the same command from Step 2.

Expected: `tests/test_v2_schemas.py` passes.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/v2.py backend/tests/test_v2_schemas.py
git commit -m "feat: add dual-agent workspace schemas"
```

## Task 2: Workspace Context Builder and Center Context

**Files:**
- Create: `backend/app/services/workspace_context_builder.py`
- Modify: `backend/app/api/v2.py`
- Test: `backend/tests/test_dual_agent_orchestrator.py`

- [ ] **Step 1: Write context builder tests**

Create `backend/tests/test_dual_agent_orchestrator.py` with this fixture and tests:

```python
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import ConversationMessageV2, Project, ThinkingNode
from app.services.workspace_context_builder import build_center_context, build_workspace_context


TEST_DATABASE_URL = "sqlite:///./dual_agent_test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


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
    assert "推理小说作者" in context.background_summary
    assert context.context_sufficiency == "unknown"


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

    context = build_workspace_context(db_session, project, user_input={"source": "chat", "content": "补充信息", "answered_node_ids": []})

    assert context["project"]["original_idea"] == "小说生成游戏"
    assert len(context["map_state"]["open_question_nodes"]) == 1
    assert len(context["map_state"]["answered_nodes"]) == 1
```

- [ ] **Step 2: Run tests to verify failure**

```bash
cd backend
DATABASE_URL=sqlite:///./dual_agent_test.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_dual_agent_orchestrator.py -q -o addopts=''
```

Expected: fails because `workspace_context_builder.py` does not exist.

- [ ] **Step 3: Implement context builder**

Create `backend/app/services/workspace_context_builder.py`:

```python
from typing import Any

from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, Project, ThinkingNode
from app.schemas.v2 import CenterContext


def build_center_context(project: Project) -> CenterContext:
    snapshot = project.summary_snapshot or {}
    existing = snapshot.get("center_context") if isinstance(snapshot, dict) else None
    if isinstance(existing, dict):
        return CenterContext.model_validate(existing)

    return CenterContext(
        original_idea=project.title,
        idea_summary=project.title,
        background_summary=project.more_info,
        known_facts=[project.more_info] if project.more_info else [],
        context_sufficiency="unknown",
    )


def _node_context(node: ThinkingNode) -> dict[str, Any]:
    return {
        "id": str(node.id),
        "parent_id": str(node.parent_id) if node.parent_id else None,
        "title": node.title,
        "kind": node.kind,
        "status": node.status,
        "question": node.question,
        "summary": node.summary,
        "answer_summary": node.answer_summary,
        "metadata": node.layout or {},
    }


def build_workspace_context(
    db: Session,
    project: Project,
    user_input: dict[str, Any] | None = None,
    focused_node: ThinkingNode | None = None,
) -> dict[str, Any]:
    center_context = build_center_context(project)
    nodes = db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id).all()
    messages = (
        db.query(ConversationMessageV2)
        .filter(ConversationMessageV2.project_id == project.id)
        .order_by(ConversationMessageV2.created_at.desc())
        .limit(12)
        .all()
    )

    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            **center_context.model_dump(mode="json"),
        },
        "map_state": {
            "center_node": next((_node_context(node) for node in nodes if node.parent_id is None), None),
            "open_question_nodes": [_node_context(node) for node in nodes if node.kind in {"question", "followup"} and node.status == "open"],
            "answered_nodes": [_node_context(node) for node in nodes if node.status == "answered"],
            "focused_node": _node_context(focused_node) if focused_node else None,
        },
        "recent_conversation": [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "metadata": message.message_metadata or {},
            }
            for message in reversed(messages)
        ],
        "user_input": user_input or {"source": "chat", "content": "", "answered_node_ids": []},
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run the command from Step 2.

Expected: context builder tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/workspace_context_builder.py backend/tests/test_dual_agent_orchestrator.py
git commit -m "feat: build auditable workspace context"
```

## Task 3: Thinking Agent Fallback and Model Boundary

**Files:**
- Create: `backend/app/services/thinking_agent.py`
- Modify: `backend/tests/test_dual_agent_orchestrator.py`

- [ ] **Step 1: Write Thinking Agent fallback tests**

Append:

```python
from app.services.thinking_agent import run_thinking_agent


def test_thinking_agent_fallback_asks_background_questions_when_context_sparse():
    context = {
        "project": {
            "title": "小说生成游戏",
            "original_idea": "小说生成游戏",
            "background_summary": None,
            "known_facts": [],
            "context_sufficiency": "unknown",
        },
        "map_state": {"open_question_nodes": [], "answered_nodes": [], "focused_node": None},
        "recent_conversation": [],
        "user_input": {"source": "chat", "content": "", "answered_node_ids": []},
    }

    output = run_thinking_agent(context, ai_func=None)

    assert output.context_sufficiency == "insufficient"
    assert 3 <= len(output.background_questions) <= 6
    assert output.thinking_questions == []
    assert "背景" in output.reasoning_trace.visible_summary or "信息" in output.reasoning_trace.visible_summary


def test_thinking_agent_fallback_generates_question_batch_when_context_rich():
    context = {
        "project": {
            "title": "上传推理小说自动生成游戏",
            "original_idea": "上传推理小说自动生成游戏",
            "background_summary": "目标用户是推理小说作者，希望把作品转成可互动破案体验。",
            "known_facts": ["目标用户是推理小说作者", "核心体验是破案推理"],
            "target_users": ["推理小说作者"],
            "context_sufficiency": "sufficient",
        },
        "map_state": {"open_question_nodes": [], "answered_nodes": [], "focused_node": None},
        "recent_conversation": [],
        "user_input": {"source": "chat", "content": "", "answered_node_ids": []},
    }

    output = run_thinking_agent(context, ai_func=None)

    assert output.context_sufficiency == "sufficient"
    assert 3 <= len(output.thinking_questions) <= 5
    assert output.background_questions == []
    assert {question.short_title for question in output.thinking_questions}
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend
DATABASE_URL=sqlite:///./dual_agent_test.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_dual_agent_orchestrator.py -q -o addopts=''
```

Expected: fails because `thinking_agent.py` does not exist.

- [ ] **Step 3: Implement Thinking Agent fallback**

Create `backend/app/services/thinking_agent.py`:

```python
import json
from typing import Any, Callable

from app.schemas.v2 import BackgroundQuestion, ReasoningTrace, ThinkingAgentOutput, ThinkingQuestion
from app.services.ai_service import get_ai_client, get_model


THINKING_AGENT_SYSTEM = """You are the Thinking Agent for AI Incubator.
Your job is to decide what should be asked, not how to draw the map.
First judge whether the user's idea and background are sufficient.
If insufficient, ask 3-6 specific background-completion questions.
If sufficient, ask 3-5 deep questions across the most important directions.
If a focused node was answered, ask 1-3 follow-up questions for that node.
Return only valid JSON matching the provided schema.
Do not ask generic filler questions.
"""


def _has_rich_context(context: dict[str, Any]) -> bool:
    project = context.get("project", {})
    background = project.get("background_summary") or ""
    facts = project.get("known_facts") or []
    target_users = project.get("target_users") or []
    return len(background) >= 24 or len(facts) >= 2 or bool(target_users)


def _background_fallback(context: dict[str, Any]) -> ThinkingAgentOutput:
    title = context.get("project", {}).get("title") or "当前想法"
    return ThinkingAgentOutput(
        context_sufficiency="insufficient",
        background_questions=[
            BackgroundQuestion(question=f"这个「{title}」最先服务哪一类具体用户？", why_needed="定位用户后才能判断问题是否真实强烈。", expected_signal="具体用户群体和使用场景"),
            BackgroundQuestion(question="用户现在遇到的痛点是什么？他们目前用什么替代方案解决？", why_needed="确认不是为了技术而技术。", expected_signal="现有替代方案和不满意点"),
            BackgroundQuestion(question="你希望生成出的游戏核心体验是什么：破案推理、角色扮演、剧情分支，还是别的？", why_needed="不同体验决定生成逻辑和质量标准。", expected_signal="首要体验优先级"),
            BackgroundQuestion(question="输入的小说通常是什么格式、长度、完整度？", why_needed="输入边界会影响自动提取人物、线索和谜题的可行性。", expected_signal="文本格式和内容质量"),
        ],
        reasoning_trace=ReasoningTrace(
            visible_summary="当前背景还不足以提出高质量产品问题，先补齐用户、痛点、核心体验和输入边界。",
            audit_notes={"fallback": True, "stage": "background_completion"},
        ),
    )


def _question_batch_fallback(context: dict[str, Any]) -> ThinkingAgentOutput:
    title = context.get("project", {}).get("title") or "当前想法"
    return ThinkingAgentOutput(
        context_sufficiency="sufficient",
        thinking_questions=[
            ThinkingQuestion(question=f"围绕「{title}」，第一批最迫切的用户是谁？他们为什么不用现有互动小说或游戏创作工具？", short_title="目标用户", why_this_matters="先找到强需求用户，避免功能泛化。", expected_answer_type="具体用户画像、当前替代方案、痛点强度"),
            ThinkingQuestion(question="自动生成的游戏必须保留小说里的哪种核心体验，才会让用户觉得它不是普通改写？", short_title="核心体验", why_this_matters="核心体验决定产品价值和生成策略。", expected_answer_type="体验优先级和不可牺牲的要素"),
            ThinkingQuestion(question="生成结果里哪些内容必须准确，哪些内容可以让用户后续编辑？", short_title="质量边界", why_this_matters="明确自动化边界可以降低不现实的质量预期。", expected_answer_type="必须自动正确的内容和可人工调整的内容"),
        ],
        reasoning_trace=ReasoningTrace(
            visible_summary="已有背景足以开始发散，先从用户、核心体验和质量边界三个方向建立第一层思维节点。",
            audit_notes={"fallback": True, "stage": "question_batch"},
        ),
    )


def run_thinking_agent(context: dict[str, Any], ai_func: Callable[[dict[str, Any]], ThinkingAgentOutput] | None = None) -> ThinkingAgentOutput:
    if ai_func:
        return ai_func(context)

    client = get_ai_client()
    if client is None:
        return _question_batch_fallback(context) if _has_rich_context(context) else _background_fallback(context)

    try:
        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {"role": "system", "content": THINKING_AGENT_SYSTEM},
                {"role": "user", "content": json.dumps({"context": context, "schema": ThinkingAgentOutput.model_json_schema()}, ensure_ascii=False)},
            ],
            temperature=0.35,
            response_format={"type": "json_object"},
        )
        return ThinkingAgentOutput.model_validate_json(response.choices[0].message.content or "{}")
    except Exception:
        return _question_batch_fallback(context) if _has_rich_context(context) else _background_fallback(context)
```

- [ ] **Step 4: Run tests to verify pass**

Run the command from Step 2.

Expected: Thinking Agent fallback tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/thinking_agent.py backend/tests/test_dual_agent_orchestrator.py
git commit -m "feat: add thinking agent fallback"
```

## Task 4: Map Agent Operation Builder

**Files:**
- Create: `backend/app/services/map_agent.py`
- Modify: `backend/tests/test_dual_agent_orchestrator.py`

- [ ] **Step 1: Write Map Agent tests**

Append:

```python
from app.schemas.v2 import ReasoningTrace, ThinkingAgentOutput, ThinkingQuestion
from app.services.map_agent import build_map_output


def test_map_agent_turns_question_batch_into_node_operations():
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
        reasoning_trace=ReasoningTrace(visible_summary="生成一个方向问题。", audit_notes={}),
    )

    output = build_map_output(
        context={"project": {"title": "小说生成游戏"}, "map_state": {"center_node": {"id": "root-id"}}},
        thinking_output=thinking_output,
    )

    assert output["node_operations"][0]["type"] == "create_question_node"
    assert output["node_operations"][0]["title"] == "目标用户"
    assert output["node_operations"][0]["detail_question"] == "第一批用户是谁？"
    assert output["conversation_events"][0]["message_metadata"]["message_type"] == "question_batch"
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend
DATABASE_URL=sqlite:///./dual_agent_test.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_dual_agent_orchestrator.py -q -o addopts=''
```

Expected: fails because `map_agent.py` does not exist.

- [ ] **Step 3: Implement Map Agent builder**

Create `backend/app/services/map_agent.py`:

```python
from typing import Any

from app.schemas.v2 import ThinkingAgentOutput


def build_map_output(context: dict[str, Any], thinking_output: ThinkingAgentOutput) -> dict[str, Any]:
    center_node = (context.get("map_state") or {}).get("center_node") or {}
    center_id = center_node.get("id")

    node_operations: list[dict[str, Any]] = []
    conversation_events: list[dict[str, Any]] = []

    if thinking_output.background_questions:
        questions = [question.model_dump(mode="json") for question in thinking_output.background_questions]
        conversation_events.append(
            {
                "role": "assistant",
                "source": "system",
                "content": "\n".join(f"{index + 1}. {item['question']}" for index, item in enumerate(questions)),
                "message_metadata": {
                    "message_type": "background_question_batch",
                    "background_questions": questions,
                    "visible_reasoning_summary": thinking_output.reasoning_trace.visible_summary,
                    "collapsed_by_default": True,
                },
            }
        )
        return {
            "center_node_patch": {
                "context_sufficiency": "insufficient",
                "unresolved_context_gaps": [question.expected_signal for question in thinking_output.background_questions],
            },
            "node_operations": node_operations,
            "conversation_events": conversation_events,
        }

    if thinking_output.thinking_questions:
        questions = [question.model_dump(mode="json") for question in thinking_output.thinking_questions]
        for question in thinking_output.thinking_questions:
            node_operations.append(
                {
                    "type": "create_question_node",
                    "parent_id": center_id,
                    "title": question.short_title,
                    "detail_question": question.question,
                    "rationale": question.why_this_matters,
                    "expected_answer_type": question.expected_answer_type,
                    "status": "open",
                }
            )
        conversation_events.append(
            {
                "role": "assistant",
                "source": "system",
                "content": "\n".join(f"{index + 1}. {item['question']}" for index, item in enumerate(questions)),
                "message_metadata": {
                    "message_type": "question_batch",
                    "question_batch": questions,
                    "visible_reasoning_summary": thinking_output.reasoning_trace.visible_summary,
                    "collapsed_by_default": True,
                },
            }
        )

    return {
        "center_node_patch": {"context_sufficiency": thinking_output.context_sufficiency},
        "node_operations": node_operations,
        "conversation_events": conversation_events,
    }
```

- [ ] **Step 4: Run tests to verify pass**

Run the command from Step 2.

Expected: Map Agent tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/map_agent.py backend/tests/test_dual_agent_orchestrator.py
git commit -m "feat: add map agent operation builder"
```

## Task 5: Dual-Agent Workspace Bootstrapping

**Files:**
- Create: `backend/app/services/dual_agent_orchestrator.py`
- Modify: `backend/app/api/v2.py`
- Modify: `backend/tests/test_v2_api.py`

- [ ] **Step 1: Write API tests for initial stages**

Update `backend/tests/test_v2_api.py`:

```python
def test_sparse_workspace_bootstraps_background_question_batch(client, project_id, auth_headers):
    response = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["center_context"]["context_sufficiency"] == "insufficient"
    assert len(data["messages"]) == 1
    assert data["messages"][0]["message_metadata"]["message_type"] == "background_question_batch"
    assert 3 <= len(data["messages"][0]["message_metadata"]["background_questions"]) <= 6
    assert [node["kind"] for node in data["nodes"]].count("question") == 0


def test_rich_workspace_bootstraps_question_nodes(client, auth_headers):
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

    assert workspace_response.status_code == 200
    data = workspace_response.json()
    assert data["center_context"]["context_sufficiency"] == "sufficient"
    question_nodes = [node for node in data["nodes"] if node["kind"] == "question"]
    assert 3 <= len(question_nodes) <= 5
    assert data["messages"][0]["message_metadata"]["message_type"] == "question_batch"
```

Remove or update older assertions that expect exactly one initial assistant message plus exactly one question node.

- [ ] **Step 2: Run API tests to verify failure**

```bash
cd backend
DATABASE_URL=sqlite:///./test_v2_api.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_v2_api.py -q -o addopts=''
```

Expected: fails because workspace does not use the dual-agent bootstrap response.

- [ ] **Step 3: Implement dual-agent orchestrator and wire workspace**

Create `backend/app/services/dual_agent_orchestrator.py`:

```python
from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, IncubatorRun, Project, ThinkingNode
from app.schemas.v2 import CenterContext
from app.services.incubator_orchestrator import ensure_root_node
from app.services.map_agent import build_map_output
from app.services.thinking_agent import run_thinking_agent
from app.services.workspace_context_builder import build_center_context, build_workspace_context


def _save_center_context(project: Project, center_context: CenterContext) -> None:
    snapshot = project.summary_snapshot or {}
    snapshot["center_context"] = center_context.model_dump(mode="json")
    project.summary_snapshot = snapshot


def _apply_node_operations(db: Session, project: Project, operations: list[dict]) -> list[ThinkingNode]:
    created: list[ThinkingNode] = []
    next_sort_order = db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id).count()
    for operation in operations:
        if operation["type"] not in {"create_question_node", "create_followup_node"}:
            continue
        node = ThinkingNode(
            project_id=project.id,
            parent_id=operation.get("parent_id"),
            kind="question",
            status=operation.get("status") or "open",
            title=operation["title"],
            summary=operation.get("rationale"),
            question=operation.get("detail_question"),
            sort_order=next_sort_order,
            layout={
                "rationale": operation.get("rationale"),
                "expected_answer_type": operation.get("expected_answer_type"),
            },
            source_message_ids=[],
            confidence=85,
        )
        next_sort_order += 1
        db.add(node)
        created.append(node)
    return created


def bootstrap_workspace_if_needed(db: Session, project: Project) -> bool:
    existing_message = db.query(ConversationMessageV2.id).filter(ConversationMessageV2.project_id == project.id).first()
    if existing_message:
        return False

    ensure_root_node(db, project)
    context = build_workspace_context(db, project)
    thinking_output = run_thinking_agent(context)
    map_output = build_map_output(context, thinking_output)

    center_context = build_center_context(project)
    patch = map_output.get("center_node_patch") or {}
    center_context.context_sufficiency = patch.get("context_sufficiency", center_context.context_sufficiency)
    center_context.unresolved_context_gaps = patch.get("unresolved_context_gaps", center_context.unresolved_context_gaps)
    _save_center_context(project, center_context)

    for event in map_output["conversation_events"]:
        db.add(ConversationMessageV2(project_id=project.id, **event))

    _apply_node_operations(db, project, map_output["node_operations"])
    db.add(
        IncubatorRun(
            project_id=project.id,
            input_payload={"context": context, "bootstrap": True},
            output_payload={"thinking": thinking_output.model_dump(mode="json"), "map": map_output},
            model="dual-agent",
            latency_ms=0,
        )
    )
    return True
```

Modify `backend/app/api/v2.py`:

```python
from app.services.dual_agent_orchestrator import bootstrap_workspace_if_needed
from app.services.workspace_context_builder import build_center_context


def build_workspace(db: Session, project: Project) -> dict:
    _, root_created = ensure_root_node(db, project)
    bootstrapped = bootstrap_workspace_if_needed(db, project)
    if root_created or bootstrapped:
        db.commit()
        db.refresh(project)
    ...
    return {
        "project_id": project.id,
        "title": project.title,
        "thinking_mode": project.thinking_mode,
        "thinking_stage": project.thinking_stage,
        "center_context": build_center_context(project),
        "messages": messages,
        "nodes": nodes,
        "suggestions": suggestions,
        "answer_matches": [],
    }
```

- [ ] **Step 4: Run API tests to verify pass**

Run the command from Step 2.

Expected: v2 API tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/dual_agent_orchestrator.py backend/app/api/v2.py backend/tests/test_v2_api.py
git commit -m "feat: bootstrap workspace with dual agents"
```

## Task 6: Node Answer API and Follow-Up Nodes

**Files:**
- Modify: `backend/app/api/v2.py`
- Modify: `backend/app/services/dual_agent_orchestrator.py`
- Modify: `backend/app/services/thinking_agent.py`
- Test: `backend/tests/test_v2_api.py`

- [ ] **Step 1: Write node answer API test**

Append to `backend/tests/test_v2_api.py`:

```python
def test_node_answer_marks_node_answered_and_creates_followups(client, auth_headers):
    project_response = client.post(
        "/api/projects",
        json={
            "title": "上传推理小说自动生成游戏",
            "more_info": "目标用户是推理小说作者，希望生成破案推理游戏。",
        },
        headers=auth_headers,
    )
    project_id = project_response.json()["id"]
    workspace = client.get(f"/api/v2/projects/{project_id}/workspace", headers=auth_headers).json()
    node_id = next(node["id"] for node in workspace["nodes"] if node["kind"] == "question")

    response = client.post(
        f"/api/v2/projects/{project_id}/nodes/{node_id}/answer",
        json={"content": "第一批用户是推理小说作者，他们想把已有作品做成互动破案体验。"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    answered = next(node for node in data["nodes"] if node["id"] == node_id)
    assert answered["status"] == "answered"
    assert answered["answer_summary"]
    children = [node for node in data["nodes"] if node["parent_id"] == node_id]
    assert 1 <= len(children) <= 3
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend
DATABASE_URL=sqlite:///./test_v2_api.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_v2_api.py::test_node_answer_marks_node_answered_and_creates_followups -q -o addopts=''
```

Expected: 404 because node answer route does not exist.

- [ ] **Step 3: Implement focused node answer flow**

In `backend/app/services/thinking_agent.py`, add fallback branch in `run_thinking_agent` before broad context fallback:

```python
def _followup_fallback(context: dict[str, Any]) -> ThinkingAgentOutput:
    focused = (context.get("map_state") or {}).get("focused_node") or {}
    parent_id = focused.get("id")
    title = focused.get("title") or "这个问题"
    return ThinkingAgentOutput(
        context_sufficiency="sufficient",
        follow_up_questions=[
            FollowUpQuestion(
                parent_question_id=parent_id,
                question=f"关于「{title}」的回答，哪个假设最需要尽快验证？",
                short_title="验证假设",
                why_this_matters="回答后应转向可验证的关键不确定性。",
                expected_answer_type="一个可观察的验证信号",
            )
        ],
        reasoning_trace=ReasoningTrace(
            visible_summary="用户回答了具体节点，下一步围绕该分支生成追问。",
            audit_notes={"fallback": True, "stage": "node_followup"},
        ),
    )
```

Then in `run_thinking_agent`:

```python
focused = (context.get("map_state") or {}).get("focused_node")
if focused and (context.get("user_input") or {}).get("content"):
    return _followup_fallback(context)
```

In `dual_agent_orchestrator.py`, add:

```python
def answer_node(db: Session, project: Project, node: ThinkingNode, content: str) -> bool:
    user_message = ConversationMessageV2(
        project_id=project.id,
        node_id=node.id,
        role="user",
        source="node",
        content=content,
        message_metadata={"message_type": "user_answer", "linked_node_ids": [str(node.id)]},
    )
    db.add(user_message)
    node.status = "answered"
    node.answer_summary = content[:500]
    db.flush()

    context = build_workspace_context(
        db,
        project,
        user_input={"source": "node", "content": content, "answered_node_ids": [str(node.id)]},
        focused_node=node,
    )
    thinking_output = run_thinking_agent(context)
    for followup in thinking_output.follow_up_questions:
        child = ThinkingNode(
            project_id=project.id,
            parent_id=node.id,
            kind="question",
            status="open",
            title=followup.short_title,
            summary=followup.why_this_matters,
            question=followup.question,
            sort_order=db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id).count(),
            layout={"rationale": followup.why_this_matters, "expected_answer_type": followup.expected_answer_type},
            source_message_ids=[str(user_message.id)],
            confidence=85,
        )
        db.add(child)

    db.add(
        ConversationMessageV2(
            project_id=project.id,
            role="assistant",
            source="system",
            content="\n".join(question.question for question in thinking_output.follow_up_questions),
            message_metadata={
                "message_type": "assistant_followup",
                "linked_node_ids": [str(node.id)],
                "visible_reasoning_summary": thinking_output.reasoning_trace.visible_summary,
                "collapsed_by_default": True,
            },
        )
    )
    return True
```

In `backend/app/api/v2.py`, add:

```python
@router.post("/projects/{project_id}/nodes/{node_id}/answer", response_model=WorkspaceResponse)
def answer_project_node(project_id: UUID, node_id: UUID, request: NodeAnswerRequest, user_id: UUID = Depends(get_current_user_id), db: Session = Depends(get_db)) -> dict:
    project = get_project_or_404(db, project_id, user_id)
    node = db.query(ThinkingNode).filter(ThinkingNode.id == node_id, ThinkingNode.project_id == project.id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    answer_node(db, project, node, request.content)
    db.commit()
    return build_workspace(db, project)
```

- [ ] **Step 4: Run test to verify pass**

Run Step 2 command.

Expected: node answer test passes.

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v2.py backend/app/services/dual_agent_orchestrator.py backend/app/services/thinking_agent.py backend/tests/test_v2_api.py
git commit -m "feat: answer map nodes with followups"
```

## Task 7: Batch Answer Matching

**Files:**
- Modify: `backend/app/services/dual_agent_orchestrator.py`
- Modify: `backend/app/api/v2.py`
- Test: `backend/tests/test_answer_matching.py`

- [ ] **Step 1: Write batch answer tests**

Create `backend/tests/test_answer_matching.py`:

```python
from app.services.dual_agent_orchestrator import match_answers_to_nodes


def test_batch_answer_matches_multiple_nodes_by_title_and_question():
    nodes = [
        {"id": "node-user", "title": "目标用户", "question": "第一批用户是谁？"},
        {"id": "node-experience", "title": "核心体验", "question": "核心体验是什么？"},
    ]
    content = "目标用户是推理小说作者。核心体验应该是破案推理，不是剧情分支。"

    matches = match_answers_to_nodes(content, nodes)

    assert [match["node_id"] for match in matches] == ["node-user", "node-experience"]
    assert all(match["confidence"] in {"high", "medium"} for match in matches)
```

- [ ] **Step 2: Run test to verify failure**

```bash
cd backend
DATABASE_URL=sqlite:///./answer_matching_test.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_answer_matching.py -q -o addopts=''
```

Expected: fails because `match_answers_to_nodes` does not exist.

- [ ] **Step 3: Implement deterministic matcher**

In `dual_agent_orchestrator.py`, add:

```python
def match_answers_to_nodes(content: str, nodes: list[dict]) -> list[dict]:
    matches: list[dict] = []
    normalized_content = content.replace("：", ":")
    for node in nodes:
        title = node.get("title") or ""
        question = node.get("question") or ""
        if title and title in normalized_content:
            matches.append({"node_id": node["id"], "extracted_answer": content, "confidence": "high"})
            continue
        if title and any(part for part in title.split() if part and part in normalized_content):
            matches.append({"node_id": node["id"], "extracted_answer": content, "confidence": "medium"})
            continue
        if "用户" in question and "用户" in normalized_content:
            matches.append({"node_id": node["id"], "extracted_answer": content, "confidence": "medium"})
            continue
        if "体验" in question and "体验" in normalized_content:
            matches.append({"node_id": node["id"], "extracted_answer": content, "confidence": "medium"})
    return matches
```

In the existing `/turns` route flow, when `source == "chat"` and open question nodes exist:

- Create a user message.
- Run matcher against open nodes.
- For high-confidence matches, call `answer_node` for each matched node.
- For medium-confidence multiple matches, create an assistant message with `message_type: "match_confirmation"` and `linked_node_ids` in metadata. Return the updated workspace with that confirmation message visible in the left panel. Persisting a separate confirmation table is outside this first pass.

- [ ] **Step 4: Run tests to verify pass**

Run Step 2 command and `tests/test_v2_api.py`.

Expected: answer matcher and v2 API tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/dual_agent_orchestrator.py backend/app/api/v2.py backend/tests/test_answer_matching.py
git commit -m "feat: match batch answers to map nodes"
```

## Task 8: Frontend Types, API, and Session Hook

**Files:**
- Modify: `frontend/src/types/incubator.ts`
- Modify: `frontend/src/api/incubator.ts`
- Modify: `frontend/src/hooks/useIncubatorSession.ts`

- [ ] **Step 1: Establish type/API verification**

Use the frontend TypeScript build as the verification for this type/API task. No extra test file is needed because this task only adds client contracts and hook exports; component behavior is covered in later tasks.

- [ ] **Step 2: Update frontend types**

Modify `frontend/src/types/incubator.ts`:

```ts
export type ThinkingNodeKind = 'idea' | 'question' | 'answer' | 'insight' | 'assumption' | 'decision' | 'risk' | 'next_step' | 'followup'
export type ThinkingNodeStatus = 'open' | 'answered' | 'suggested' | 'confirmed' | 'needs_context' | 'resolved'
export type MessageType = 'thinking_trace' | 'background_question_batch' | 'question_batch' | 'user_answer' | 'match_confirmation' | 'assistant_followup'

export interface CenterContext {
  original_idea: string
  idea_summary: string | null
  background_summary: string | null
  known_facts: string[]
  assumptions: string[]
  constraints: string[]
  target_users: string[]
  desired_outcomes: string[]
  unresolved_context_gaps: string[]
  context_sufficiency: 'unknown' | 'insufficient' | 'sufficient'
}

export interface QuestionBatchItem {
  question: string
  short_title?: string
  why_this_matters?: string
  why_needed?: string
  expected_answer_type?: string
  expected_signal?: string
}

export interface ConversationMetadata {
  message_type?: MessageType
  linked_node_ids?: string[]
  collapsed_by_default?: boolean
  visible_reasoning_summary?: string
  background_questions?: QuestionBatchItem[]
  question_batch?: QuestionBatchItem[]
  match_confirmation_id?: string
}

export interface ConversationMessageV2 {
  id: string
  project_id: string
  node_id: string | null
  role: 'user' | 'assistant'
  source: 'chat' | 'node' | 'system'
  content: string
  thinking_mode: ThinkingMode | null
  stage: ThinkingStage | null
  message_metadata: ConversationMetadata | null
  created_at: string
}

export interface AnswerMatch {
  node_id: string
  extracted_answer: string
  confidence: 'high' | 'medium' | 'low'
}

export interface AnswerMatchResponse {
  id: string
  project_id: string
  status: string
  matches: AnswerMatch[]
  original_content: string
  created_at: string
}

export interface WorkspaceResponse {
  project_id: string
  title: string
  thinking_mode: ThinkingMode | null
  thinking_stage: ThinkingStage | null
  center_context: CenterContext
  messages: ConversationMessageV2[]
  nodes: ThinkingNode[]
  suggestions: RestructureSuggestion[]
  answer_matches: AnswerMatchResponse[]
}

export interface NodeAnswerRequest {
  content: string
}
```

- [ ] **Step 3: Add API calls**

Modify `frontend/src/api/incubator.ts`:

```ts
import type { NodeAnswerRequest, TurnRequest, TurnResponse, WorkspaceResponse } from '../types/incubator'

answerNode: async (projectId: string, nodeId: string, data: NodeAnswerRequest) => {
  const response = await apiClient.post<WorkspaceResponse>(`/v2/projects/${projectId}/nodes/${nodeId}/answer`, data)
  return response.data
},

confirmAnswerMatch: async (matchId: string) => {
  const response = await apiClient.post<WorkspaceResponse>(`/v2/answer-matches/${matchId}/confirm`)
  return response.data
},
```

- [ ] **Step 4: Update hook**

In `frontend/src/hooks/useIncubatorSession.ts`, add mutations:

```ts
const nodeAnswerMutation = useMutation({
  mutationFn: ({ nodeId, content }: { nodeId: string; content: string }) =>
    incubatorApi.answerNode(projectId!, nodeId, { content }),
  onSuccess: (data) => {
    queryClient.setQueryData<WorkspaceResponse>(['v2-workspace', projectId], data)
  },
  onError: (error: ApiError) => {
    message.error(error.response?.data?.detail || '回答节点失败，请重试')
  },
})

const matchConfirmMutation = useMutation({
  mutationFn: (matchId: string) => incubatorApi.confirmAnswerMatch(matchId),
  onSuccess: (data) => {
    queryClient.setQueryData<WorkspaceResponse>(['v2-workspace', projectId], data)
  },
  onError: (error: ApiError) => {
    message.error(error.response?.data?.detail || '确认匹配失败，请重试')
  },
})
```

Return:

```ts
answerNode: (nodeId: string, content: string) => nodeAnswerMutation.mutate({ nodeId, content }),
confirmAnswerMatch: (matchId: string) => matchConfirmMutation.mutate(matchId),
isThinking: turnMutation.isPending || suggestionMutation.isPending || nodeAnswerMutation.isPending || matchConfirmMutation.isPending,
```

- [ ] **Step 5: Run frontend build**

```bash
cd frontend
npm run build
```

Expected: TypeScript build passes.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types/incubator.ts frontend/src/api/incubator.ts frontend/src/hooks/useIncubatorSession.ts
git commit -m "feat: add frontend dual-agent API types"
```

## Task 9: Two-Column Resizable Workspace

**Files:**
- Modify: `frontend/src/pages/IncubatorWorkspacePage.tsx`
- Keep but stop using: `frontend/src/components/incubator/NodeInspector.tsx`

- [ ] **Step 1: Modify workspace layout**

Replace the three-column grid in `IncubatorWorkspacePage.tsx` with resizable two-column state:

```tsx
const [leftWidth, setLeftWidth] = useState(340)
const [isResizing, setIsResizing] = useState(false)

const startResize = () => setIsResizing(true)

useEffect(() => {
  if (!isResizing) return
  const onMouseMove = (event: MouseEvent) => {
    setLeftWidth(Math.min(520, Math.max(280, event.clientX - 16)))
  }
  const onMouseUp = () => setIsResizing(false)
  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
  return () => {
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }
}, [isResizing])
```

Render:

```tsx
<main className="flex-1 min-h-0 relative flex">
  <div style={{ width: leftWidth }} className="min-w-[280px] max-w-[520px] shrink-0">
    <ChatPanel ... />
  </div>
  <button
    type="button"
    aria-label="调整对话栏宽度"
    onMouseDown={startResize}
    className="w-1.5 cursor-col-resize bg-slate-200 hover:bg-sky-400"
  />
  <div className="min-w-0 flex-1">
    <MindmapCanvas
      centerContext={workspace.center_context}
      nodes={workspace.nodes}
      selectedNodeId={selectedNode?.id ?? null}
      onSelectNode={setSelectedNode}
      onClearSelection={() => setSelectedNode(null)}
      onAnswerNode={answerNode}
    />
  </div>
  <RestructureSuggestionPanel ... />
</main>
```

Remove `NodeInspector` import and usage.

- [ ] **Step 2: Run frontend build**

```bash
cd frontend
npm run build
```

Expected: build passes, no unused `NodeInspector` import.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/IncubatorWorkspacePage.tsx
git commit -m "feat: use two-column resizable workspace"
```

## Task 10: Typed Conversation Panel

**Files:**
- Modify: `frontend/src/components/incubator/ChatPanel.tsx`

- [ ] **Step 1: Implement message render helpers**

Add helpers inside `ChatPanel.tsx`:

```tsx
function ThinkingSummary({ summary }: { summary: string }) {
  const [open, setOpen] = useState(false)
  return (
    <div className="rounded-md bg-slate-50 border border-slate-200 px-3 py-2 text-xs text-slate-500">
      <button type="button" className="font-medium text-slate-600" onClick={() => setOpen(!open)}>
        {open ? '收起思考过程' : '查看思考过程'}
      </button>
      {open && <p className="mt-2 leading-5 whitespace-pre-wrap">{summary}</p>}
    </div>
  )
}

function QuestionList({ title, items }: { title: string; items: QuestionBatchItem[] }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-800">
      <div className="font-semibold mb-2">{title}</div>
      <ol className="space-y-2 list-decimal pl-5">
        {items.map((item, index) => (
          <li key={`${item.question}-${index}`}>
            <div className="font-medium">{item.short_title || item.question}</div>
            {item.short_title && <div className="text-slate-600 mt-1">{item.question}</div>}
            {(item.why_this_matters || item.why_needed) && (
              <div className="text-xs text-slate-500 mt-1">{item.why_this_matters || item.why_needed}</div>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}
```

Render metadata-aware assistant messages:

```tsx
const metadata = msg.message_metadata
if (metadata?.visible_reasoning_summary) {
  blocks.push(<ThinkingSummary key={`${msg.id}-thinking`} summary={metadata.visible_reasoning_summary} />)
}
if (metadata?.message_type === 'background_question_batch' && metadata.background_questions) {
  blocks.push(<QuestionList key={`${msg.id}-background`} title="先补充这些背景信息" items={metadata.background_questions} />)
}
if (metadata?.message_type === 'question_batch' && metadata.question_batch) {
  blocks.push(<QuestionList key={`${msg.id}-questions`} title="建议从这些方向开始思考" items={metadata.question_batch} />)
}
```

Keep existing bubble rendering for messages without metadata.

- [ ] **Step 2: Build**

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/incubator/ChatPanel.tsx
git commit -m "feat: render structured AI conversation blocks"
```

## Task 11: XMind Clean Map and Node Popovers

**Files:**
- Modify: `frontend/src/components/incubator/MindmapCanvas.tsx`
- Create: `frontend/src/components/incubator/NodePopover.tsx`
- Modify: `frontend/src/components/incubator/thinkingMapAdapter.ts`

- [ ] **Step 1: Create NodePopover**

Create `NodePopover.tsx`:

```tsx
import { Button, Input, Tag } from 'antd'
import { useState } from 'react'
import type { CenterContext, ThinkingNode } from '../../types/incubator'

interface NodePopoverProps {
  node: ThinkingNode
  centerContext: CenterContext
  onAnswerNode: (nodeId: string, content: string) => void
  onClose: () => void
}

export default function NodePopover({ node, centerContext, onAnswerNode, onClose }: NodePopoverProps) {
  const [answer, setAnswer] = useState('')
  const rationale = typeof node.layout?.rationale === 'string' ? node.layout.rationale : node.summary
  const expectedAnswerType = typeof node.layout?.expected_answer_type === 'string' ? node.layout.expected_answer_type : null

  if (node.kind === 'idea') {
    return (
      <div className="absolute left-8 top-8 z-20 w-[420px] rounded-lg border border-slate-200 bg-white shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
          <div className="font-semibold text-slate-900">项目背景</div>
          <Button type="text" size="small" onClick={onClose}>关闭</Button>
        </div>
        <div className="space-y-3 p-4 text-sm text-slate-700">
          <div><span className="font-medium">原始想法：</span>{centerContext.original_idea}</div>
          {centerContext.background_summary && <div><span className="font-medium">背景：</span>{centerContext.background_summary}</div>}
          {centerContext.unresolved_context_gaps.length > 0 && (
            <div>
              <div className="font-medium">仍需补充</div>
              <ul className="mt-1 list-disc pl-5">
                {centerContext.unresolved_context_gaps.map((gap) => <li key={gap}>{gap}</li>)}
              </ul>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="absolute right-8 top-8 z-20 w-[420px] rounded-lg border border-slate-200 bg-white shadow-xl">
      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
        <div className="font-semibold text-slate-900">{node.title}</div>
        <Button type="text" size="small" onClick={onClose}>关闭</Button>
      </div>
      <div className="space-y-3 p-4">
        <Tag color={node.status === 'answered' ? 'green' : 'blue'}>{node.status}</Tag>
        {node.question && <p className="text-sm leading-6 text-slate-800">{node.question}</p>}
        {rationale && <p className="rounded-md bg-slate-50 p-3 text-xs leading-5 text-slate-600">{rationale}</p>}
        {expectedAnswerType && <p className="text-xs text-slate-500">期望回答：{expectedAnswerType}</p>}
        {node.answer_summary && <p className="rounded-md bg-emerald-50 p-3 text-sm text-emerald-800">{node.answer_summary}</p>}
        <Input.TextArea rows={4} value={answer} onChange={(event) => setAnswer(event.target.value)} placeholder="输入你对这个问题的回答..." />
        <Button type="primary" block disabled={!answer.trim()} onClick={() => { onAnswerNode(node.id, answer); setAnswer('') }}>
          确认回答
        </Button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Style MindElixir nodes**

In `MindmapCanvas.tsx`, add `centerContext`, `onAnswerNode`, and `onClearSelection` props. Render `NodePopover` over the canvas when a node is selected.

Use container classes:

```tsx
<section className="relative h-full w-full overflow-hidden bg-[#f7fafc]">
  <div ref={containerRef} className="h-full w-full xmind-clean-map" />
  {selectedNode && (
    <NodePopover node={selectedNode} centerContext={centerContext} onAnswerNode={onAnswerNode} onClose={onClearSelection} />
  )}
</section>
```

Add map styling to `frontend/src/index.css`:

```css
.xmind-clean-map .map-canvas {
  background: #f7fafc;
}
.xmind-clean-map .map-node {
  border-radius: 12px;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.08);
}
```

- [ ] **Step 3: Build**

```bash
cd frontend
npm run build
```

Expected: build passes.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/incubator/MindmapCanvas.tsx frontend/src/components/incubator/NodePopover.tsx frontend/src/components/incubator/thinkingMapAdapter.ts frontend/src/index.css
git commit -m "feat: add xmind clean map popovers"
```

## Task 12: Verification and Browser QA

**Files:**
- No source changes unless QA finds bugs.

- [ ] **Step 1: Run backend targeted tests**

```bash
cd backend
DATABASE_URL=sqlite:///./baseline_test.db SECRET_KEY=test-secret .venv/bin/python -m pytest tests/test_dual_agent_orchestrator.py tests/test_answer_matching.py tests/test_v2_api.py -q -o addopts=''
```

Expected: all selected backend tests pass.

- [ ] **Step 2: Run frontend verification**

```bash
cd frontend
npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 3: Start services**

```bash
cd backend
DATABASE_URL=sqlite:///./dev.db SECRET_KEY=dev-secret .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

```bash
cd frontend
npm run dev -- --host 127.0.0.1 --port 5174
```

Expected: backend listens on `127.0.0.1:8000`; frontend listens on `127.0.0.1:5174`.

- [ ] **Step 4: Browser QA with gstack /browse**

Use gstack browse per project instructions:

```bash
CONTAINER=1 PATH=/home/pan/.bun/bin:$PATH /home/pan/.codex/skills/gstack/browse/dist/browse goto 'http://127.0.0.1:5174/'
```

Manual checks:

- Register or log in.
- Create sparse project with title only.
- Confirm left panel shows 3-6 background questions and map shows center node only.
- Create rich project with background.
- Confirm right map shows center node plus 3-5 question nodes.
- Click a question node and confirm popover shows full question/rationale/answer input.
- Submit node answer and confirm child follow-up nodes appear.
- Paste a left-panel batch answer covering multiple node titles and confirm matches or confirmation UI.
- Drag left panel width and confirm map remains usable.

- [ ] **Step 5: Final status**

Record verification commands and any failures in the final response.
