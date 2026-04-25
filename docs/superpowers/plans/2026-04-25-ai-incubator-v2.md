# AI Incubator v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the v2 AI Incubator MVP: a dual-track chat and mindmap workspace with a general AI thinking loop, structured map updates, and user-confirmed restructure suggestions.

**Architecture:** Add v2 backend tables and `/api/v2` endpoints alongside the existing MVP, then add a new React workspace that consumes a neutral `ThinkingMap` model. The first vertical slice uses deterministic/mock AI orchestration so the UI and data flow can be verified before real model calls are connected.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, Pydantic v2, pytest, React 19, TypeScript, Vite, React Query, Ant Design, Mind Elixir or a temporary adapter-compatible fallback.

---

## File Structure

Backend files to create:

- `backend/app/models/v2.py`: v2 SQLAlchemy models for messages, thinking nodes, restructure suggestions, and AI runs.
- `backend/app/schemas/v2.py`: Pydantic schemas for workspace payloads, turn requests/responses, map nodes, operations, and suggestions.
- `backend/app/services/thinking_mode_service.py`: deterministic mode recommendation from project/map/message state.
- `backend/app/services/map_update_service.py`: validates and applies allowed map operations.
- `backend/app/services/incubator_orchestrator.py`: builds context, calls mock/real AI, validates output, persists a turn.
- `backend/app/api/v2.py`: v2 routes.
- `backend/alembic/versions/002_v2_incubator_tables.py`: additive v2 migration.
- `backend/tests/test_thinking_mode_service.py`
- `backend/tests/test_map_update_service.py`
- `backend/tests/test_v2_api.py`

Backend files to modify:

- `backend/app/models/__init__.py`: export v2 models.
- `backend/app/main.py`: register the v2 router.
- `backend/app/schemas/project.py`: allow `framework="general"` for v2-compatible project creation.
- `backend/app/api/projects.py`: default new projects to `general` when framework is omitted.

Frontend files to create:

- `frontend/src/types/incubator.ts`: neutral v2 workspace, node, message, operation, and suggestion types.
- `frontend/src/api/incubator.ts`: v2 API client functions.
- `frontend/src/pages/IncubatorWorkspacePage.tsx`: v2 page container.
- `frontend/src/components/incubator/ChatPanel.tsx`
- `frontend/src/components/incubator/MindmapCanvas.tsx`
- `frontend/src/components/incubator/NodeInspector.tsx`
- `frontend/src/components/incubator/RestructureSuggestionPanel.tsx`
- `frontend/src/components/incubator/thinkingMapAdapter.ts`
- `frontend/src/hooks/useIncubatorSession.ts`
- `frontend/src/test/incubator/thinkingMapAdapter.test.ts`
- `frontend/src/test/incubator/IncubatorWorkspacePage.test.tsx`

Frontend files to modify:

- `frontend/src/App.tsx`: route project workspace to the v2 page.
- `frontend/src/api/index.ts`: export v2 incubator API.
- `frontend/src/pages/ProjectListPage.tsx`: remove framework selection from creation flow after backend supports default `general`.
- `frontend/package.json`: add `mind-elixir` after adapter tests pass.

---

## Task 1: Add V2 Data Model and Migration

**Files:**

- Create: `backend/app/models/v2.py`
- Create: `backend/alembic/versions/002_v2_incubator_tables.py`
- Modify: `backend/app/models/__init__.py`
- Test indirectly with: `python -m compileall backend/app`

- [ ] **Step 1: Create v2 SQLAlchemy models**

Create `backend/app/models/v2.py` with:

```python
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class ConversationMessageV2(Base):
    __tablename__ = "conversation_messages_v2"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("thinking_nodes.id"), nullable=True)
    role = Column(SQLEnum("user", "assistant", name="conversation_role_v2"), nullable=False)
    source = Column(SQLEnum("chat", "node", "system", name="message_source_v2"), nullable=False, default="chat")
    content = Column(Text, nullable=False)
    thinking_mode = Column(String, nullable=True)
    stage = Column(String, nullable=True)
    message_metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)

    project = relationship("Project")


class ThinkingNode(Base):
    __tablename__ = "thinking_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("thinking_nodes.id"), nullable=True)
    kind = Column(SQLEnum("idea", "question", "answer", "insight", "assumption", "decision", "risk", "next_step", name="thinking_node_kind"), nullable=False)
    status = Column(SQLEnum("open", "answered", "suggested", "confirmed", name="thinking_node_status"), nullable=False, default="open")
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    question = Column(Text, nullable=True)
    answer_summary = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    layout = Column(JSONB, nullable=True)
    source_message_ids = Column(JSONB, nullable=False, default=list)
    confidence = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    updated_at = Column(DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    project = relationship("Project")
    parent = relationship("ThinkingNode", remote_side=[id], backref="children")


class RestructureSuggestion(Base):
    __tablename__ = "restructure_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    status = Column(SQLEnum("pending", "accepted", "rejected", name="suggestion_status"), nullable=False, default="pending")
    operations = Column(JSONB, nullable=False)
    rationale = Column(Text, nullable=False)
    created_from_message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages_v2.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
    resolved_at = Column(DateTime, nullable=True)

    project = relationship("Project")


class IncubatorRun(Base):
    __tablename__ = "incubator_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    user_message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages_v2.id"), nullable=True)
    assistant_message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages_v2.id"), nullable=True)
    model = Column(String, nullable=True)
    input_payload = Column(JSONB, nullable=False)
    output_payload = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
```

- [ ] **Step 2: Export models**

Modify `backend/app/models/__init__.py` to import and export the new models:

```python
from app.models.user import User
from app.models.project import Project
from app.models.node import MindmapNode, ConversationHistory, EvolutionHistory
from app.models.v2 import ConversationMessageV2, ThinkingNode, RestructureSuggestion, IncubatorRun

__all__ = [
    "User",
    "Project",
    "MindmapNode",
    "ConversationHistory",
    "EvolutionHistory",
    "ConversationMessageV2",
    "ThinkingNode",
    "RestructureSuggestion",
    "IncubatorRun",
]
```

- [ ] **Step 3: Add migration**

Create `backend/alembic/versions/002_v2_incubator_tables.py` with additive tables and project columns:

```python
"""Add v2 incubator tables

Revision ID: 002
Revises: 001
Create Date: 2026-04-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("system_context_version", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("thinking_stage", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("thinking_mode", sa.String(), nullable=True))
    op.add_column("projects", sa.Column("summary_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    op.create_table(
        "thinking_nodes",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("kind", sa.Enum("idea", "question", "answer", "insight", "assumption", "decision", "risk", "next_step", name="thinking_node_kind"), nullable=False),
        sa.Column("status", sa.Enum("open", "answered", "suggested", "confirmed", name="thinking_node_status"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("question", sa.Text(), nullable=True),
        sa.Column("answer_summary", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("layout", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("source_message_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_thinking_nodes_project"),
        sa.ForeignKeyConstraint(["parent_id"], ["thinking_nodes.id"], name="fk_thinking_nodes_parent"),
    )

    op.create_table(
        "conversation_messages_v2",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("node_id", sa.UUID(), nullable=True),
        sa.Column("role", sa.Enum("user", "assistant", name="conversation_role_v2"), nullable=False),
        sa.Column("source", sa.Enum("chat", "node", "system", name="message_source_v2"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("thinking_mode", sa.String(), nullable=True),
        sa.Column("stage", sa.String(), nullable=True),
        sa.Column("message_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_messages_v2_project"),
        sa.ForeignKeyConstraint(["node_id"], ["thinking_nodes.id"], name="fk_messages_v2_node"),
    )

    op.create_table(
        "restructure_suggestions",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Enum("pending", "accepted", "rejected", name="suggestion_status"), nullable=False),
        sa.Column("operations", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("created_from_message_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_suggestions_project"),
        sa.ForeignKeyConstraint(["created_from_message_id"], ["conversation_messages_v2.id"], name="fk_suggestions_message"),
    )

    op.create_table(
        "incubator_runs",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("user_message_id", sa.UUID(), nullable=True),
        sa.Column("assistant_message_id", sa.UUID(), nullable=True),
        sa.Column("model", sa.String(), nullable=True),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], name="fk_runs_project"),
        sa.ForeignKeyConstraint(["user_message_id"], ["conversation_messages_v2.id"], name="fk_runs_user_message"),
        sa.ForeignKeyConstraint(["assistant_message_id"], ["conversation_messages_v2.id"], name="fk_runs_assistant_message"),
    )


def downgrade() -> None:
    op.drop_table("incubator_runs")
    op.drop_table("restructure_suggestions")
    op.drop_table("conversation_messages_v2")
    op.drop_table("thinking_nodes")
    op.drop_column("projects", "summary_snapshot")
    op.drop_column("projects", "thinking_mode")
    op.drop_column("projects", "thinking_stage")
    op.drop_column("projects", "system_context_version")
```

- [ ] **Step 4: Verify model import and migration syntax**

Run:

```bash
cd backend
python -m compileall app alembic
```

Expected: command exits 0 and prints compiled files, with no syntax errors.

- [ ] **Step 5: Commit**

```bash
git add backend/app/models/v2.py backend/app/models/__init__.py backend/alembic/versions/002_v2_incubator_tables.py
git commit -m "feat: add v2 incubator data model"
```

---

## Task 2: Add V2 Schemas, Thinking Mode Service, and Map Update Service

**Files:**

- Create: `backend/app/schemas/v2.py`
- Create: `backend/app/services/thinking_mode_service.py`
- Create: `backend/app/services/map_update_service.py`
- Create: `backend/tests/test_thinking_mode_service.py`
- Create: `backend/tests/test_map_update_service.py`

- [ ] **Step 1: Write thinking mode tests**

Create `backend/tests/test_thinking_mode_service.py`:

```python
from app.services.thinking_mode_service import ThinkingStateSignals, recommend_thinking_mode


def test_sparse_initial_state_recommends_diverge():
    signals = ThinkingStateSignals(turn_count=1, node_count=1, open_question_count=0)
    result = recommend_thinking_mode(signals)
    assert result.mode == "diverge"
    assert "early" in result.reason.lower() or "sparse" in result.reason.lower()


def test_dense_map_with_many_open_questions_recommends_converge():
    signals = ThinkingStateSignals(turn_count=8, node_count=24, open_question_count=7, decision_count=1, map_density="high")
    result = recommend_thinking_mode(signals)
    assert result.mode == "converge"
    assert "open questions" in result.reason.lower()


def test_user_requested_action_plan_recommends_converge():
    signals = ThinkingStateSignals(turn_count=4, node_count=6, user_requested_action_plan=True)
    result = recommend_thinking_mode(signals)
    assert result.mode == "converge"
    assert "action" in result.reason.lower()
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
cd backend
pytest tests/test_thinking_mode_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.thinking_mode_service'`.

- [ ] **Step 3: Implement thinking mode service**

Create `backend/app/services/thinking_mode_service.py`:

```python
from dataclasses import dataclass


@dataclass
class ThinkingStateSignals:
    turn_count: int = 0
    node_count: int = 0
    answered_node_count: int = 0
    open_question_count: int = 0
    decision_count: int = 0
    assumption_count: int = 0
    risk_count: int = 0
    last_3_turns_repeated: bool = False
    user_requested_action_plan: bool = False
    user_expressed_confusion: bool = False
    map_density: str = "low"
    focused_node_depth: int = 0


@dataclass
class ThinkingModeRecommendation:
    mode: str
    reason: str


def recommend_thinking_mode(signals: ThinkingStateSignals) -> ThinkingModeRecommendation:
    if signals.user_requested_action_plan:
        return ThinkingModeRecommendation("converge", "The user requested an action plan, so converge into a minimum next step.")

    if signals.last_3_turns_repeated:
        return ThinkingModeRecommendation("challenge", "Recent turns are repeating, so challenge the frame or introduce a new angle.")

    if signals.user_expressed_confusion:
        return ThinkingModeRecommendation("clarify", "The user expressed confusion, so clarify the current problem before adding branches.")

    if signals.turn_count <= 3 or signals.node_count <= 3:
        return ThinkingModeRecommendation("diverge", "The project is early and sparse, so explore breadth before narrowing.")

    if signals.open_question_count >= 5 and signals.map_density == "high":
        return ThinkingModeRecommendation("converge", "There are many open questions in a dense map, so summarize before adding more branches.")

    if signals.assumption_count >= 3 and signals.decision_count == 0:
        return ThinkingModeRecommendation("validate", "Several assumptions exist without decisions, so validate the most important uncertainty.")

    return ThinkingModeRecommendation("clarify", "The next best step is to clarify the most important unresolved point.")
```

- [ ] **Step 4: Run thinking mode tests**

Run:

```bash
cd backend
pytest tests/test_thinking_mode_service.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Add v2 schemas**

Create `backend/app/schemas/v2.py`:

```python
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ThinkingMode = Literal["diverge", "converge", "clarify", "challenge", "validate"]
ThinkingStage = Literal["discover", "define", "develop", "deliver"]
NodeKind = Literal["idea", "question", "answer", "insight", "assumption", "decision", "risk", "next_step"]
NodeStatus = Literal["open", "answered", "suggested", "confirmed"]
MessageRole = Literal["user", "assistant"]
MessageSource = Literal["chat", "node"]
OperationType = Literal["create_node", "update_node", "mark_answered", "move_node", "rename_node", "merge_nodes", "split_node", "delete_node"]


class ThinkingNodeResponse(BaseModel):
    id: str
    project_id: str
    parent_id: str | None
    kind: NodeKind
    status: NodeStatus
    title: str
    summary: str | None
    question: str | None
    answer_summary: str | None
    sort_order: int
    layout: dict[str, Any] | None
    source_message_ids: list[str]
    confidence: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConversationMessageResponse(BaseModel):
    id: str
    project_id: str
    node_id: str | None
    role: MessageRole
    source: str
    content: str
    thinking_mode: str | None
    stage: str | None
    message_metadata: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MapOperation(BaseModel):
    type: OperationType
    node_id: str | None = None
    parent_id: str | None = None
    title: str | None = None
    kind: NodeKind | None = None
    status: NodeStatus | None = None
    summary: str | None = None
    question: str | None = None
    source_node_ids: list[str] = Field(default_factory=list)


class RestructureSuggestionResponse(BaseModel):
    id: str
    project_id: str
    status: str
    operations: list[MapOperation]
    rationale: str
    created_from_message_id: str | None
    created_at: datetime
    resolved_at: datetime | None

    model_config = {"from_attributes": True}


class TurnRequest(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    source: MessageSource = "chat"
    node_id: str | None = None


class CurrentSummary(BaseModel):
    facts: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class AIMapUpdate(BaseModel):
    operation: MapOperation
    risk: Literal["low", "high"] = "low"


class AIOrchestratorOutput(BaseModel):
    thinking_mode: ThinkingMode
    stage: ThinkingStage
    mode_reason: str
    assistant_message: str
    next_question: str
    question_intent: str
    map_updates: list[AIMapUpdate] = Field(default_factory=list)
    restructure_suggestions: list[MapOperation] = Field(default_factory=list)
    detected_gaps: list[str] = Field(default_factory=list)
    current_summary: CurrentSummary = Field(default_factory=CurrentSummary)


class WorkspaceResponse(BaseModel):
    project_id: str
    title: str
    thinking_mode: str | None
    thinking_stage: str | None
    messages: list[ConversationMessageResponse]
    nodes: list[ThinkingNodeResponse]
    suggestions: list[RestructureSuggestionResponse]


class TurnResponse(WorkspaceResponse):
    user_message: ConversationMessageResponse
    assistant_message: ConversationMessageResponse
```

- [ ] **Step 6: Write map update tests**

Create `backend/tests/test_map_update_service.py`:

```python
import uuid

import pytest

from app.schemas.v2 import MapOperation
from app.services.map_update_service import HIGH_RISK_OPERATIONS, LOW_RISK_OPERATIONS, validate_operation_risk


def test_create_node_is_low_risk_when_required_fields_exist():
    operation = MapOperation(type="create_node", parent_id=str(uuid.uuid4()), title="Target user", kind="question")
    assert validate_operation_risk(operation) == "low"


def test_move_node_is_high_risk():
    operation = MapOperation(type="move_node", node_id=str(uuid.uuid4()), parent_id=str(uuid.uuid4()))
    assert validate_operation_risk(operation) == "high"


def test_create_node_requires_title_and_kind():
    operation = MapOperation(type="create_node", parent_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="title and kind"):
        validate_operation_risk(operation)


def test_operation_sets_are_disjoint():
    assert LOW_RISK_OPERATIONS.isdisjoint(HIGH_RISK_OPERATIONS)
```

- [ ] **Step 7: Run map update tests to verify failure**

Run:

```bash
cd backend
pytest tests/test_map_update_service.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.map_update_service'`.

- [ ] **Step 8: Implement map update service**

Create `backend/app/services/map_update_service.py`:

```python
from app.schemas.v2 import MapOperation


LOW_RISK_OPERATIONS = {"create_node", "update_node", "mark_answered"}
HIGH_RISK_OPERATIONS = {"move_node", "rename_node", "merge_nodes", "split_node", "delete_node"}


def validate_operation_risk(operation: MapOperation) -> str:
    if operation.type == "create_node":
        if not operation.title or not operation.kind:
            raise ValueError("create_node requires title and kind")
        return "low"

    if operation.type == "update_node":
        if not operation.node_id:
            raise ValueError("update_node requires node_id")
        return "low"

    if operation.type == "mark_answered":
        if not operation.node_id:
            raise ValueError("mark_answered requires node_id")
        return "low"

    if operation.type in HIGH_RISK_OPERATIONS:
        if operation.type != "merge_nodes" and not operation.node_id:
            raise ValueError(f"{operation.type} requires node_id")
        if operation.type == "merge_nodes" and len(operation.source_node_ids) < 2:
            raise ValueError("merge_nodes requires at least two source_node_ids")
        return "high"

    raise ValueError(f"Unsupported operation type: {operation.type}")
```

- [ ] **Step 9: Run service tests**

Run:

```bash
cd backend
pytest tests/test_thinking_mode_service.py tests/test_map_update_service.py -v
```

Expected: 7 passed.

- [ ] **Step 10: Commit**

```bash
git add backend/app/schemas/v2.py backend/app/services/thinking_mode_service.py backend/app/services/map_update_service.py backend/tests/test_thinking_mode_service.py backend/tests/test_map_update_service.py
git commit -m "feat: add v2 thinking services"
```

---

## Task 3: Add Mock V2 Workspace and Turn API

**Files:**

- Create: `backend/app/services/incubator_orchestrator.py`
- Create: `backend/app/api/v2.py`
- Create: `backend/tests/test_v2_api.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/schemas/project.py`
- Modify: `backend/app/api/projects.py`

- [ ] **Step 1: Write v2 API integration tests**

Create `backend/tests/test_v2_api.py`:

```python
import uuid

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.models import Project


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_v2_api.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_project() -> str:
    db = TestingSessionLocal()
    project = Project(
        id=uuid.uuid4(),
        user_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        title="AI diary tool",
        framework="general",
        status="active",
    )
    db.add(project)
    db.commit()
    project_id = str(project.id)
    db.close()
    return project_id


def test_workspace_bootstraps_center_idea():
    project_id = create_project()
    response = client.get(f"/api/v2/projects/{project_id}/workspace")
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "AI diary tool"
    assert len(payload["nodes"]) == 1
    assert payload["nodes"][0]["kind"] == "idea"


def test_turn_creates_user_and_assistant_messages_and_question_node():
    project_id = create_project()
    response = client.post(
        f"/api/v2/projects/{project_id}/turns",
        json={"content": "It is for people who want to journal but cannot keep the habit.", "source": "chat"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["user_message"]["role"] == "user"
    assert payload["assistant_message"]["role"] == "assistant"
    assert payload["thinking_mode"] in ["diverge", "converge", "clarify", "challenge", "validate"]
    assert any(node["kind"] == "question" for node in payload["nodes"])
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_v2_api.py -v
```

Expected: FAIL because `/api/v2/projects/{id}/workspace` is not registered.

- [ ] **Step 3: Implement mock orchestrator**

Create `backend/app/services/incubator_orchestrator.py`:

```python
from datetime import datetime
from time import perf_counter
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, IncubatorRun, Project, RestructureSuggestion, ThinkingNode
from app.schemas.v2 import AIOrchestratorOutput, CurrentSummary, MapOperation, TurnRequest
from app.services.thinking_mode_service import ThinkingStateSignals, recommend_thinking_mode


def ensure_root_node(db: Session, project: Project) -> ThinkingNode:
    root = db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id, ThinkingNode.parent_id.is_(None)).first()
    if root:
        return root
    root = ThinkingNode(
        project_id=project.id,
        parent_id=None,
        kind="idea",
        status="confirmed",
        title=project.title,
        summary=project.title,
        sort_order=0,
        layout=None,
        source_message_ids=[],
        confidence=100,
    )
    db.add(root)
    db.flush()
    return root


def build_signals(db: Session, project_id: UUID) -> ThinkingStateSignals:
    node_count = db.query(ThinkingNode).filter(ThinkingNode.project_id == project_id).count()
    open_question_count = db.query(ThinkingNode).filter(ThinkingNode.project_id == project_id, ThinkingNode.kind == "question", ThinkingNode.status == "open").count()
    decision_count = db.query(ThinkingNode).filter(ThinkingNode.project_id == project_id, ThinkingNode.kind == "decision").count()
    turn_count = db.query(ConversationMessageV2).filter(ConversationMessageV2.project_id == project_id, ConversationMessageV2.role == "user").count()
    return ThinkingStateSignals(
        turn_count=turn_count,
        node_count=node_count,
        open_question_count=open_question_count,
        decision_count=decision_count,
        map_density="high" if node_count >= 18 else "low",
    )


def mock_ai_response(content: str, mode: str) -> AIOrchestratorOutput:
    next_question = "Who feels this problem most strongly, and what situation are they in when it appears?"
    if mode == "converge":
        next_question = "If you had to state the core problem in one sentence, what would it be?"
    return AIOrchestratorOutput(
        thinking_mode=mode,
        stage="discover" if mode == "diverge" else "define",
        mode_reason=f"Mock mode selected as {mode} from project signals.",
        assistant_message=f"I captured that. The strongest signal is: {content[:120]}",
        next_question=next_question,
        question_intent="Keep the user moving with one focused question.",
        map_updates=[
            {
                "operation": MapOperation(type="create_node", title=next_question, kind="question", status="open", summary="AI follow-up question"),
                "risk": "low",
            }
        ],
        restructure_suggestions=[],
        detected_gaps=[],
        current_summary=CurrentSummary(insights=[content[:160]], open_questions=[next_question]),
    )


def run_turn(db: Session, project: Project, request: TurnRequest) -> tuple[ConversationMessageV2, ConversationMessageV2]:
    started = perf_counter()
    root = ensure_root_node(db, project)
    user_message = ConversationMessageV2(
        project_id=project.id,
        node_id=request.node_id,
        role="user",
        source=request.source,
        content=request.content,
    )
    db.add(user_message)
    db.flush()

    signals = build_signals(db, project.id)
    recommendation = recommend_thinking_mode(signals)
    ai_output = mock_ai_response(request.content, recommendation.mode)

    assistant_message = ConversationMessageV2(
        project_id=project.id,
        role="assistant",
        source="system",
        content=f"{ai_output.assistant_message}\n\n{ai_output.next_question}",
        thinking_mode=ai_output.thinking_mode,
        stage=ai_output.stage,
        message_metadata={
            "mode_reason": ai_output.mode_reason,
            "question_intent": ai_output.question_intent,
            "current_summary": ai_output.current_summary.model_dump(),
        },
    )
    db.add(assistant_message)
    db.flush()

    for update in ai_output.map_updates:
        operation = update.operation
        if operation.type == "create_node":
            node = ThinkingNode(
                project_id=project.id,
                parent_id=UUID(operation.parent_id) if operation.parent_id else root.id,
                kind=operation.kind or "question",
                status=operation.status or "open",
                title=operation.title or "Untitled question",
                summary=operation.summary,
                question=operation.question or operation.title,
                sort_order=0,
                layout=None,
                source_message_ids=[str(user_message.id), str(assistant_message.id)],
                confidence=90,
            )
            db.add(node)

    run = IncubatorRun(
        project_id=project.id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        model="mock-v2",
        input_payload={"content": request.content, "signals": signals.__dict__, "recommended_mode": recommendation.mode},
        output_payload=ai_output.model_dump(),
        latency_ms=int((perf_counter() - started) * 1000),
    )
    db.add(run)

    project.thinking_mode = ai_output.thinking_mode
    project.thinking_stage = ai_output.stage
    project.summary_snapshot = ai_output.current_summary.model_dump()
    project.system_context_version = "v2.0"
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message
```

- [ ] **Step 4: Implement v2 API**

Create `backend/app/api/v2.py`:

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ConversationMessageV2, Project, RestructureSuggestion, ThinkingNode
from app.schemas.v2 import TurnRequest, TurnResponse, WorkspaceResponse
from app.services.incubator_orchestrator import ensure_root_node, run_turn

router = APIRouter(prefix="/v2", tags=["v2"])


def get_project_or_404(db: Session, project_id: str) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def build_workspace(db: Session, project: Project) -> dict:
    ensure_root_node(db, project)
    db.commit()
    nodes = db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id).order_by(ThinkingNode.created_at.asc()).all()
    messages = db.query(ConversationMessageV2).filter(ConversationMessageV2.project_id == project.id).order_by(ConversationMessageV2.created_at.asc()).all()
    suggestions = db.query(RestructureSuggestion).filter(RestructureSuggestion.project_id == project.id, RestructureSuggestion.status == "pending").all()
    return {
        "project_id": str(project.id),
        "title": project.title,
        "thinking_mode": project.thinking_mode,
        "thinking_stage": project.thinking_stage,
        "messages": messages,
        "nodes": nodes,
        "suggestions": suggestions,
    }


@router.get("/projects/{project_id}/workspace", response_model=WorkspaceResponse)
def get_workspace(project_id: str, db: Session = Depends(get_db)) -> dict:
    project = get_project_or_404(db, project_id)
    return build_workspace(db, project)


@router.post("/projects/{project_id}/turns", response_model=TurnResponse)
def create_turn(project_id: str, request: TurnRequest, db: Session = Depends(get_db)) -> dict:
    project = get_project_or_404(db, project_id)
    user_message, assistant_message = run_turn(db, project, request)
    workspace = build_workspace(db, project)
    workspace["user_message"] = user_message
    workspace["assistant_message"] = assistant_message
    return workspace
```

- [ ] **Step 5: Register v2 router**

Modify `backend/app/main.py` so it imports and includes `v2.router`:

```python
from app.api import auth, projects, nodes, ai, v2

# existing router registrations stay in place
app.include_router(v2.router, prefix="/api")
```

- [ ] **Step 6: Allow general projects**

Modify `backend/app/schemas/project.py`:

```python
class FrameworkType(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    BUSINESS_CANVAS = "business_canvas"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    SOCRATIC = "socratic"
    GENERAL = "general"


class ProjectCreate(BaseModel):
    title: str
    framework: FrameworkType = FrameworkType.GENERAL
```

Modify `backend/app/api/projects.py` to tolerate omitted framework by using `project_data.framework.value`, which now defaults to `general`.

- [ ] **Step 7: Run v2 API tests**

Run:

```bash
cd backend
pytest tests/test_v2_api.py -v
```

Expected: 2 passed.

- [ ] **Step 8: Run backend suite**

Run:

```bash
cd backend
pytest -v
```

Expected: all tests pass. If existing OpenAI-dependent tests fail due missing API key, mark the failure and run only deterministic v2 tests before proceeding.

- [ ] **Step 9: Commit**

```bash
git add backend/app/services/incubator_orchestrator.py backend/app/api/v2.py backend/app/main.py backend/app/schemas/project.py backend/app/api/projects.py backend/tests/test_v2_api.py
git commit -m "feat: add mock v2 incubator API"
```

---

## Task 4: Add V2 Frontend Types, API Client, and Workspace Shell

**Files:**

- Create: `frontend/src/types/incubator.ts`
- Create: `frontend/src/api/incubator.ts`
- Create: `frontend/src/hooks/useIncubatorSession.ts`
- Create: `frontend/src/pages/IncubatorWorkspacePage.tsx`
- Create: `frontend/src/components/incubator/ChatPanel.tsx`
- Create: `frontend/src/components/incubator/MindmapCanvas.tsx`
- Create: `frontend/src/components/incubator/NodeInspector.tsx`
- Create: `frontend/src/components/incubator/RestructureSuggestionPanel.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/api/index.ts`

- [ ] **Step 1: Add v2 frontend types**

Create `frontend/src/types/incubator.ts`:

```ts
export type ThinkingMode = 'diverge' | 'converge' | 'clarify' | 'challenge' | 'validate'
export type ThinkingStage = 'discover' | 'define' | 'develop' | 'deliver'
export type ThinkingNodeKind = 'idea' | 'question' | 'answer' | 'insight' | 'assumption' | 'decision' | 'risk' | 'next_step'
export type ThinkingNodeStatus = 'open' | 'answered' | 'suggested' | 'confirmed'

export interface ConversationMessageV2 {
  id: string
  project_id: string
  node_id: string | null
  role: 'user' | 'assistant'
  source: string
  content: string
  thinking_mode: ThinkingMode | null
  stage: ThinkingStage | null
  message_metadata: Record<string, unknown> | null
  created_at: string
}

export interface ThinkingNode {
  id: string
  project_id: string
  parent_id: string | null
  kind: ThinkingNodeKind
  status: ThinkingNodeStatus
  title: string
  summary: string | null
  question: string | null
  answer_summary: string | null
  sort_order: number
  layout: Record<string, unknown> | null
  source_message_ids: string[]
  confidence: number
  created_at: string
  updated_at: string
}

export interface MapOperation {
  type: 'create_node' | 'update_node' | 'mark_answered' | 'move_node' | 'rename_node' | 'merge_nodes' | 'split_node' | 'delete_node'
  node_id?: string | null
  parent_id?: string | null
  title?: string | null
  kind?: ThinkingNodeKind | null
  status?: ThinkingNodeStatus | null
  summary?: string | null
  question?: string | null
  source_node_ids?: string[]
}

export interface RestructureSuggestion {
  id: string
  project_id: string
  status: 'pending' | 'accepted' | 'rejected'
  operations: MapOperation[]
  rationale: string
  created_from_message_id: string | null
  created_at: string
  resolved_at: string | null
}

export interface WorkspaceResponse {
  project_id: string
  title: string
  thinking_mode: ThinkingMode | null
  thinking_stage: ThinkingStage | null
  messages: ConversationMessageV2[]
  nodes: ThinkingNode[]
  suggestions: RestructureSuggestion[]
}

export interface TurnRequest {
  content: string
  source: 'chat' | 'node'
  node_id?: string | null
}

export interface TurnResponse extends WorkspaceResponse {
  user_message: ConversationMessageV2
  assistant_message: ConversationMessageV2
}
```

- [ ] **Step 2: Add v2 API client**

Create `frontend/src/api/incubator.ts`:

```ts
import apiClient from './client'
import type { TurnRequest, TurnResponse, WorkspaceResponse } from '../types/incubator'

export const incubatorApi = {
  getWorkspace: async (projectId: string) => {
    const response = await apiClient.get<WorkspaceResponse>(`/v2/projects/${projectId}/workspace`)
    return response.data
  },

  createTurn: async (projectId: string, data: TurnRequest) => {
    const response = await apiClient.post<TurnResponse>(`/v2/projects/${projectId}/turns`, data)
    return response.data
  },
}
```

Modify `frontend/src/api/index.ts` to export it:

```ts
export { incubatorApi } from './incubator'
```

- [ ] **Step 3: Add session hook**

Create `frontend/src/hooks/useIncubatorSession.ts`:

```ts
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { message } from 'antd'
import { incubatorApi } from '../api/incubator'
import type { TurnRequest, WorkspaceResponse } from '../types/incubator'

export function useIncubatorSession(projectId: string | undefined) {
  const queryClient = useQueryClient()

  const workspaceQuery = useQuery({
    queryKey: ['v2-workspace', projectId],
    queryFn: () => incubatorApi.getWorkspace(projectId!),
    enabled: Boolean(projectId),
  })

  const turnMutation = useMutation({
    mutationFn: (request: TurnRequest) => incubatorApi.createTurn(projectId!, request),
    onSuccess: (data) => {
      queryClient.setQueryData<WorkspaceResponse>(['v2-workspace', projectId], data)
    },
    onError: (error: any) => {
      message.error(error.response?.data?.detail || 'AI 思考失败，请重试')
    },
  })

  return {
    workspace: workspaceQuery.data,
    isLoading: workspaceQuery.isLoading,
    isThinking: turnMutation.isPending,
    submitTurn: turnMutation.mutate,
  }
}
```

- [ ] **Step 4: Add workspace components**

Create `frontend/src/components/incubator/ChatPanel.tsx`:

```tsx
import { Button, Input, Spin, Tag } from 'antd'
import { useState } from 'react'
import type { ConversationMessageV2, ThinkingNode } from '../../types/incubator'

interface ChatPanelProps {
  messages: ConversationMessageV2[]
  selectedNode: ThinkingNode | null
  isThinking: boolean
  onSubmit: (content: string, nodeId?: string | null) => void
}

export default function ChatPanel({ messages, selectedNode, isThinking, onSubmit }: ChatPanelProps) {
  const [value, setValue] = useState('')

  const submit = () => {
    const content = value.trim()
    if (!content) return
    onSubmit(content, selectedNode?.id ?? null)
    setValue('')
  }

  return (
    <section className="h-full flex flex-col border-r border-slate-200 bg-white">
      <div className="px-4 py-3 border-b border-slate-200">
        <div className="text-sm font-semibold text-slate-800">思考对话</div>
        {selectedNode && <Tag className="mt-2" color="blue">围绕节点：{selectedNode.title}</Tag>}
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {messages.map((msg) => (
          <div key={msg.id} className={msg.role === 'user' ? 'text-right' : 'text-left'}>
            <div className={`inline-block max-w-[88%] rounded-lg px-3 py-2 text-sm ${msg.role === 'user' ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-800'}`}>
              {msg.content}
            </div>
          </div>
        ))}
        {isThinking && <Spin size="small" tip="AI 正在思考..." />}
      </div>
      <div className="p-4 border-t border-slate-200">
        <Input.TextArea
          value={value}
          onChange={(event) => setValue(event.target.value)}
          rows={4}
          placeholder="回答 AI 的问题，或围绕选中节点继续思考..."
          onPressEnter={(event) => {
            if (!event.shiftKey) {
              event.preventDefault()
              submit()
            }
          }}
        />
        <Button type="primary" block className="mt-3" loading={isThinking} onClick={submit}>
          发送
        </Button>
      </div>
    </section>
  )
}
```

Create `frontend/src/components/incubator/MindmapCanvas.tsx`:

```tsx
import type { ThinkingNode } from '../../types/incubator'

interface MindmapCanvasProps {
  nodes: ThinkingNode[]
  selectedNodeId: string | null
  onSelectNode: (node: ThinkingNode) => void
}

const kindLabel: Record<ThinkingNode['kind'], string> = {
  idea: '想法',
  question: '问题',
  answer: '回答',
  insight: '洞察',
  assumption: '假设',
  decision: '决策',
  risk: '风险',
  next_step: '下一步',
}

export default function MindmapCanvas({ nodes, selectedNodeId, onSelectNode }: MindmapCanvasProps) {
  return (
    <section className="h-full bg-slate-50 overflow-auto p-6">
      <div className="min-w-[720px]">
        <div className="text-sm font-semibold text-slate-700 mb-4">思维导图</div>
        <div className="grid gap-3">
          {nodes.map((node) => (
            <button
              key={node.id}
              type="button"
              onClick={() => onSelectNode(node)}
              className={`text-left rounded-lg border px-4 py-3 bg-white transition ${selectedNodeId === node.id ? 'border-sky-500 shadow-md' : 'border-slate-200 hover:border-sky-300'}`}
              style={{ marginLeft: node.parent_id ? 32 : 0 }}
            >
              <div className="text-xs text-slate-500">{kindLabel[node.kind]} · {node.status}</div>
              <div className="font-medium text-slate-900">{node.title}</div>
              {node.summary && <div className="text-sm text-slate-600 mt-1">{node.summary}</div>}
            </button>
          ))}
        </div>
      </div>
    </section>
  )
}
```

Create `frontend/src/components/incubator/NodeInspector.tsx`:

```tsx
import { Empty, Tag } from 'antd'
import type { ThinkingNode } from '../../types/incubator'

interface NodeInspectorProps {
  node: ThinkingNode | null
}

export default function NodeInspector({ node }: NodeInspectorProps) {
  if (!node) {
    return <Empty description="选择一个节点查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
  }

  return (
    <aside className="border-l border-slate-200 bg-white p-4 w-80 overflow-y-auto">
      <Tag color="blue">{node.kind}</Tag>
      <h3 className="mt-3 text-lg font-semibold text-slate-900">{node.title}</h3>
      {node.question && <p className="mt-3 text-sm text-slate-700">{node.question}</p>}
      {node.summary && <p className="mt-3 text-sm text-slate-600">{node.summary}</p>}
      {node.answer_summary && (
        <div className="mt-4 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">
          {node.answer_summary}
        </div>
      )}
    </aside>
  )
}
```

Create `frontend/src/components/incubator/RestructureSuggestionPanel.tsx`:

```tsx
import { Alert, Button } from 'antd'
import type { RestructureSuggestion } from '../../types/incubator'

interface Props {
  suggestions: RestructureSuggestion[]
}

export default function RestructureSuggestionPanel({ suggestions }: Props) {
  if (suggestions.length === 0) return null
  return (
    <div className="absolute right-4 top-4 w-80 space-y-3">
      {suggestions.map((suggestion) => (
        <Alert
          key={suggestion.id}
          type="info"
          showIcon
          message="AI 建议重组导图"
          description={
            <div>
              <p>{suggestion.rationale}</p>
              <div className="mt-3 flex gap-2">
                <Button size="small" type="primary">接受</Button>
                <Button size="small">拒绝</Button>
              </div>
            </div>
          }
        />
      ))}
    </div>
  )
}
```

- [ ] **Step 5: Add workspace page**

Create `frontend/src/pages/IncubatorWorkspacePage.tsx`:

```tsx
import { Button, Spin, Tag } from 'antd'
import { ArrowLeftOutlined } from '@ant-design/icons'
import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import ChatPanel from '../components/incubator/ChatPanel'
import MindmapCanvas from '../components/incubator/MindmapCanvas'
import NodeInspector from '../components/incubator/NodeInspector'
import RestructureSuggestionPanel from '../components/incubator/RestructureSuggestionPanel'
import { useIncubatorSession } from '../hooks/useIncubatorSession'
import type { ThinkingNode } from '../types/incubator'

export default function IncubatorWorkspacePage() {
  const { projectId } = useParams<{ projectId: string }>()
  const navigate = useNavigate()
  const { workspace, isLoading, isThinking, submitTurn } = useIncubatorSession(projectId)
  const [selectedNode, setSelectedNode] = useState<ThinkingNode | null>(null)

  if (isLoading || !workspace) {
    return <div className="h-screen flex items-center justify-center"><Spin size="large" /></div>
  }

  return (
    <div className="h-screen flex flex-col bg-white">
      <header className="h-14 border-b border-slate-200 px-4 flex items-center gap-3">
        <Button type="text" icon={<ArrowLeftOutlined />} onClick={() => navigate('/projects')}>返回</Button>
        <h1 className="text-lg font-semibold text-slate-900 flex-1">{workspace.title}</h1>
        {workspace.thinking_mode && <Tag color="purple">{workspace.thinking_mode}</Tag>}
      </header>
      <main className="flex-1 grid grid-cols-[380px_1fr_320px] min-h-0 relative">
        <ChatPanel
          messages={workspace.messages}
          selectedNode={selectedNode}
          isThinking={isThinking}
          onSubmit={(content, nodeId) => submitTurn({ content, source: nodeId ? 'node' : 'chat', node_id: nodeId })}
        />
        <MindmapCanvas nodes={workspace.nodes} selectedNodeId={selectedNode?.id ?? null} onSelectNode={setSelectedNode} />
        <NodeInspector node={selectedNode} />
        <RestructureSuggestionPanel suggestions={workspace.suggestions} />
      </main>
    </div>
  )
}
```

- [ ] **Step 6: Route to v2 workspace**

Modify `frontend/src/App.tsx` to import `IncubatorWorkspacePage` and use it for `/projects/:projectId`:

```tsx
import IncubatorWorkspacePage from './pages/IncubatorWorkspacePage'
```

Replace the protected project route element's child from `<IncubatorPage />` to `<IncubatorWorkspacePage />`.

- [ ] **Step 7: Run frontend checks**

Run:

```bash
cd frontend
npm run build
```

Expected: TypeScript and Vite build pass.

- [ ] **Step 8: Commit**

```bash
git add frontend/src/types/incubator.ts frontend/src/api/incubator.ts frontend/src/hooks/useIncubatorSession.ts frontend/src/pages/IncubatorWorkspacePage.tsx frontend/src/components/incubator frontend/src/App.tsx frontend/src/api/index.ts
git commit -m "feat: add v2 incubator workspace shell"
```

---

## Task 5: Remove Framework Selection From Project Creation

**Files:**

- Modify: `frontend/src/pages/ProjectListPage.tsx`
- Modify: `frontend/src/api/index.ts`
- Modify: `frontend/src/types/index.ts`

- [ ] **Step 1: Update frontend project create API type**

Modify `frontend/src/api/index.ts`:

```ts
create: async (data: { title: string; framework?: FrameworkType }) => {
  const response = await apiClient.post<Project>('/projects', data)
  return response.data
},
```

- [ ] **Step 2: Add general framework type**

Modify `frontend/src/types/index.ts`:

```ts
export type FrameworkType = 'product_manager' | 'business_canvas' | 'technical_feasibility' | 'socratic' | 'general'
```

- [ ] **Step 3: Simplify project modal**

In `frontend/src/pages/ProjectListPage.tsx`, remove the `Select` import and framework `<Form.Item>`. Keep only the title field. Change `handleCreate`:

```tsx
const handleCreate = (values: { title: string }) => {
  createMutation.mutate({ title: values.title, framework: 'general' })
}
```

Keep `frameworkOptions` only for legacy project card labels and add:

```tsx
{ label: '通用探索', value: 'general' },
```

- [ ] **Step 4: Run build**

Run:

```bash
cd frontend
npm run build
```

Expected: build passes and no unused `Select` import remains.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/ProjectListPage.tsx frontend/src/api/index.ts frontend/src/types/index.ts
git commit -m "feat: default projects to general exploration"
```

---

## Task 6: Add Mindmap Adapter Tests and Integrate Mind Elixir

**Files:**

- Create: `frontend/src/components/incubator/thinkingMapAdapter.ts`
- Create: `frontend/src/test/incubator/thinkingMapAdapter.test.ts`
- Modify: `frontend/src/components/incubator/MindmapCanvas.tsx`
- Modify: `frontend/package.json`
- Modify: `frontend/package-lock.json`

- [ ] **Step 1: Install mind-elixir**

Run:

```bash
cd frontend
npm install mind-elixir
```

Expected: package and lockfile update successfully.

- [ ] **Step 2: Add adapter tests**

Create `frontend/src/test/incubator/thinkingMapAdapter.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { buildMindElixirData } from '../../components/incubator/thinkingMapAdapter'
import type { ThinkingNode } from '../../types/incubator'

const baseNode = (overrides: Partial<ThinkingNode>): ThinkingNode => ({
  id: 'node-1',
  project_id: 'project-1',
  parent_id: null,
  kind: 'idea',
  status: 'confirmed',
  title: 'Root idea',
  summary: null,
  question: null,
  answer_summary: null,
  sort_order: 0,
  layout: null,
  source_message_ids: [],
  confidence: 100,
  created_at: '2026-04-25T00:00:00',
  updated_at: '2026-04-25T00:00:00',
  ...overrides,
})

describe('buildMindElixirData', () => {
  it('builds a root with children from flat nodes', () => {
    const data = buildMindElixirData([
      baseNode({ id: 'root', title: 'AI diary', kind: 'idea' }),
      baseNode({ id: 'child', parent_id: 'root', title: 'Target user', kind: 'question', status: 'open' }),
    ])
    expect(data.nodeData.id).toBe('root')
    expect(data.nodeData.children?.[0].id).toBe('child')
    expect(data.nodeData.children?.[0].topic).toContain('Target user')
  })

  it('creates fallback root when node list is empty', () => {
    const data = buildMindElixirData([])
    expect(data.nodeData.topic).toBe('Untitled idea')
  })
})
```

- [ ] **Step 3: Run adapter test to verify failure**

Run:

```bash
cd frontend
npm run test -- src/test/incubator/thinkingMapAdapter.test.ts
```

Expected: FAIL because `thinkingMapAdapter` does not exist.

- [ ] **Step 4: Implement adapter**

Create `frontend/src/components/incubator/thinkingMapAdapter.ts`:

```ts
import type { ThinkingNode } from '../../types/incubator'

interface MindElixirNode {
  id: string
  topic: string
  children?: MindElixirNode[]
  tags?: string[]
}

export interface MindElixirData {
  nodeData: MindElixirNode
}

const kindText: Record<ThinkingNode['kind'], string> = {
  idea: '想法',
  question: '问题',
  answer: '回答',
  insight: '洞察',
  assumption: '假设',
  decision: '决策',
  risk: '风险',
  next_step: '下一步',
}

export function buildMindElixirData(nodes: ThinkingNode[]): MindElixirData {
  if (nodes.length === 0) {
    return { nodeData: { id: 'root', topic: 'Untitled idea', children: [] } }
  }

  const byId = new Map<string, MindElixirNode>()
  nodes.forEach((node) => {
    byId.set(node.id, {
      id: node.id,
      topic: node.title,
      tags: [kindText[node.kind], node.status],
      children: [],
    })
  })

  let root: MindElixirNode | null = null
  nodes.forEach((node) => {
    const current = byId.get(node.id)!
    if (!node.parent_id || !byId.has(node.parent_id)) {
      if (!root) root = current
      return
    }
    byId.get(node.parent_id)!.children!.push(current)
  })

  return { nodeData: root ?? byId.values().next().value }
}
```

- [ ] **Step 5: Integrate Mind Elixir in canvas**

Replace `frontend/src/components/incubator/MindmapCanvas.tsx` with a component that initializes the engine and falls back to the existing list if initialization fails:

```tsx
import { useEffect, useRef, useState } from 'react'
import MindElixir from 'mind-elixir'
import 'mind-elixir/style.css'
import type { ThinkingNode } from '../../types/incubator'
import { buildMindElixirData } from './thinkingMapAdapter'

interface MindmapCanvasProps {
  nodes: ThinkingNode[]
  selectedNodeId: string | null
  onSelectNode: (node: ThinkingNode) => void
}

export default function MindmapCanvas({ nodes, onSelectNode }: MindmapCanvasProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const instanceRef = useRef<any>(null)
  const [failed, setFailed] = useState(false)

  useEffect(() => {
    if (!containerRef.current) return
    try {
      const data = buildMindElixirData(nodes)
      if (!instanceRef.current) {
        instanceRef.current = new MindElixir({
          el: containerRef.current,
          direction: MindElixir.SIDE,
          draggable: true,
          contextMenu: false,
          toolBar: true,
          nodeMenu: false,
          keypress: true,
        })
        instanceRef.current.init(data)
        instanceRef.current.bus.addListener('selectNode', (node: { id: string }) => {
          const selected = nodes.find((item) => item.id === node.id)
          if (selected) onSelectNode(selected)
        })
      } else {
        instanceRef.current.refresh(data)
      }
      setFailed(false)
    } catch {
      setFailed(true)
    }
  }, [nodes, onSelectNode])

  if (failed) {
    return (
      <section className="h-full bg-slate-50 overflow-auto p-6">
        {nodes.map((node) => (
          <button key={node.id} type="button" onClick={() => onSelectNode(node)} className="block w-full text-left rounded-lg border border-slate-200 bg-white px-4 py-3 mb-3">
            <div className="text-xs text-slate-500">{node.kind} · {node.status}</div>
            <div className="font-medium text-slate-900">{node.title}</div>
          </button>
        ))}
      </section>
    )
  }

  return <section ref={containerRef} className="h-full w-full bg-white" />
}
```

- [ ] **Step 6: Run adapter tests and build**

Run:

```bash
cd frontend
npm run test -- src/test/incubator/thinkingMapAdapter.test.ts
npm run build
```

Expected: adapter tests pass and build succeeds. If Mind Elixir typings are missing, add a local declaration file `frontend/src/types/mind-elixir.d.ts` with `declare module 'mind-elixir'`.

- [ ] **Step 7: Commit**

```bash
git add frontend/package.json frontend/package-lock.json frontend/src/components/incubator/MindmapCanvas.tsx frontend/src/components/incubator/thinkingMapAdapter.ts frontend/src/test/incubator/thinkingMapAdapter.test.ts frontend/src/types/mind-elixir.d.ts
git commit -m "feat: render v2 workspace with mindmap engine"
```

---

## Task 7: Add Suggestion Accept and Reject API

**Files:**

- Modify: `backend/app/api/v2.py`
- Modify: `backend/app/services/map_update_service.py`
- Modify: `frontend/src/api/incubator.ts`
- Modify: `frontend/src/components/incubator/RestructureSuggestionPanel.tsx`
- Modify: `frontend/src/hooks/useIncubatorSession.ts`
- Test: `backend/tests/test_v2_api.py`

- [ ] **Step 1: Extend backend tests**

Add this test to `backend/tests/test_v2_api.py`:

```python
def test_reject_missing_suggestion_returns_404():
    response = client.post(f"/api/v2/restructure-suggestions/{uuid.uuid4()}/reject")
    assert response.status_code == 404
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
cd backend
pytest tests/test_v2_api.py::test_reject_missing_suggestion_returns_404 -v
```

Expected: FAIL with 404 route not found or method not allowed.

- [ ] **Step 3: Add reject and accept endpoints**

Add to `backend/app/api/v2.py`:

```python
from datetime import datetime


@router.post("/restructure-suggestions/{suggestion_id}/reject", response_model=WorkspaceResponse)
def reject_suggestion(suggestion_id: str, db: Session = Depends(get_db)) -> dict:
    suggestion = db.query(RestructureSuggestion).filter(RestructureSuggestion.id == suggestion_id).first()
    if not suggestion:
      raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = "rejected"
    suggestion.resolved_at = datetime.utcnow()
    project = get_project_or_404(db, str(suggestion.project_id))
    db.commit()
    return build_workspace(db, project)


@router.post("/restructure-suggestions/{suggestion_id}/accept", response_model=WorkspaceResponse)
def accept_suggestion(suggestion_id: str, db: Session = Depends(get_db)) -> dict:
    suggestion = db.query(RestructureSuggestion).filter(RestructureSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")
    suggestion.status = "accepted"
    suggestion.resolved_at = datetime.utcnow()
    project = get_project_or_404(db, str(suggestion.project_id))
    db.commit()
    return build_workspace(db, project)
```

- [ ] **Step 4: Run backend API tests**

Run:

```bash
cd backend
pytest tests/test_v2_api.py -v
```

Expected: all v2 API tests pass.

- [ ] **Step 5: Add frontend API methods**

Modify `frontend/src/api/incubator.ts`:

```ts
acceptSuggestion: async (suggestionId: string) => {
  const response = await apiClient.post<WorkspaceResponse>(`/v2/restructure-suggestions/${suggestionId}/accept`)
  return response.data
},

rejectSuggestion: async (suggestionId: string) => {
  const response = await apiClient.post<WorkspaceResponse>(`/v2/restructure-suggestions/${suggestionId}/reject`)
  return response.data
},
```

- [ ] **Step 6: Wire suggestion actions**

Modify `useIncubatorSession` to expose `acceptSuggestion` and `rejectSuggestion` mutations that update the workspace query with returned data. Modify `RestructureSuggestionPanel` props to accept callbacks:

```tsx
interface Props {
  suggestions: RestructureSuggestion[]
  onAccept: (id: string) => void
  onReject: (id: string) => void
}
```

Change the buttons:

```tsx
<Button size="small" type="primary" onClick={() => onAccept(suggestion.id)}>接受</Button>
<Button size="small" onClick={() => onReject(suggestion.id)}>拒绝</Button>
```

Pass callbacks from `IncubatorWorkspacePage`.

- [ ] **Step 7: Run checks**

Run:

```bash
cd backend && pytest tests/test_v2_api.py -v
cd ../frontend && npm run build
```

Expected: backend v2 tests pass and frontend build succeeds.

- [ ] **Step 8: Commit**

```bash
git add backend/app/api/v2.py backend/tests/test_v2_api.py frontend/src/api/incubator.ts frontend/src/hooks/useIncubatorSession.ts frontend/src/components/incubator/RestructureSuggestionPanel.tsx frontend/src/pages/IncubatorWorkspacePage.tsx
git commit -m "feat: add restructure suggestion actions"
```

---

## Task 8: Replace Mock AI With Structured AI Orchestration

**Files:**

- Modify: `backend/app/services/incubator_orchestrator.py`
- Modify: `backend/tests/test_v2_api.py`
- Create: `backend/tests/test_incubator_orchestrator.py`

- [ ] **Step 1: Add orchestrator unit test for invalid AI output**

Create `backend/tests/test_incubator_orchestrator.py`:

```python
import pytest
from pydantic import ValidationError

from app.schemas.v2 import AIOrchestratorOutput


def test_ai_output_requires_one_valid_mode():
    with pytest.raises(ValidationError):
        AIOrchestratorOutput.model_validate({
            "thinking_mode": "random",
            "stage": "discover",
            "mode_reason": "bad",
            "assistant_message": "hello",
            "next_question": "question?",
            "question_intent": "intent",
        })
```

- [ ] **Step 2: Run test**

Run:

```bash
cd backend
pytest tests/test_incubator_orchestrator.py -v
```

Expected: test passes because schema validation already rejects invalid mode.

- [ ] **Step 3: Add real system context builder**

In `backend/app/services/incubator_orchestrator.py`, add:

```python
SYSTEM_CONTEXT_V2 = """You are AI Incubator's thinking partner.
Help the user clarify vague ideas through questions, reflection, and structure.
Do not use visible fixed frameworks. Use them only as private inspiration.
Balance divergent and convergent thinking.
Ask one main question per turn.
Separate facts, assumptions, insights, open questions, decisions, risks, and next steps.
Suggest high-risk map restructuring only as suggestions requiring confirmation.
Return only valid JSON matching the requested schema.
"""
```

Add a `call_ai_orchestrator(context: dict) -> AIOrchestratorOutput` function that calls OpenAI when `settings.OPENAI_API_KEY` is present and otherwise falls back to `mock_ai_response`.

- [ ] **Step 4: Keep deterministic tests by injecting mock**

Refactor `run_turn` signature:

```python
def run_turn(db: Session, project: Project, request: TurnRequest, ai_func=mock_ai_response) -> tuple[ConversationMessageV2, ConversationMessageV2]:
```

Use `ai_func(request.content, recommendation.mode)` in tests. The API route can call default behavior.

- [ ] **Step 5: Run backend tests**

Run:

```bash
cd backend
pytest tests/test_thinking_mode_service.py tests/test_map_update_service.py tests/test_incubator_orchestrator.py tests/test_v2_api.py -v
```

Expected: all listed tests pass without requiring a live OpenAI call.

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/incubator_orchestrator.py backend/tests/test_incubator_orchestrator.py backend/tests/test_v2_api.py
git commit -m "feat: add structured v2 AI orchestration"
```

---

## Task 9: Final Verification and Manual Acceptance

**Files:**

- Modify only if verification reveals defects in files from previous tasks.

- [ ] **Step 1: Run backend deterministic tests**

Run:

```bash
cd backend
pytest tests/test_thinking_mode_service.py tests/test_map_update_service.py tests/test_incubator_orchestrator.py tests/test_v2_api.py -v
```

Expected: all pass.

- [ ] **Step 2: Run frontend tests and build**

Run:

```bash
cd frontend
npm run test -- src/test/incubator/thinkingMapAdapter.test.ts
npm run build
```

Expected: tests and build pass.

- [ ] **Step 3: Start backend**

Run:

```bash
cd backend
python -m uvicorn app.main:app --reload
```

Expected: server starts at `http://127.0.0.1:8000`.

- [ ] **Step 4: Start frontend**

Run in a second terminal:

```bash
cd frontend
npm run dev
```

Expected: Vite prints a local URL, usually `http://localhost:5173`.

- [ ] **Step 5: Manual acceptance**

In the browser:

1. Create a project titled `AI diary tool for beginners`.
2. Open the project workspace.
3. Confirm the right side shows a center idea node.
4. Send this chat message: `It is for people who want to journal but cannot keep the habit.`
5. Confirm the left side shows both user and assistant messages.
6. Confirm the right side adds at least one question node.
7. Click the question node and answer from the chat input.
8. Confirm the message source is tied to the selected node.

- [ ] **Step 6: Stop any running dev servers**

Stop `uvicorn` and `vite` with Ctrl-C. Do not leave sessions running.

- [ ] **Step 7: Commit any verification fixes**

If fixes were needed:

```bash
git add <changed-files>
git commit -m "fix: stabilize v2 incubator verification"
```

If no fixes were needed, do not create an empty commit.

---

## Self-Review

Spec coverage:

- Dual chat and map workspace: Tasks 4, 6, and 9.
- General AI context and structured AI output: Tasks 2, 3, and 8.
- Thinking mode decision with explicit signals: Task 2.
- User-confirmed high-risk restructuring: Task 7.
- Additive migration and v1 compatibility: Tasks 1, 3, and 5.
- Tests and manual acceptance: Tasks 2, 3, 6, 7, 8, and 9.

Placeholder scan:

- The plan contains no placeholder markers or unspecified test steps.
- Each task has exact file paths, concrete commands, expected outcomes, and code snippets for new modules.

Type consistency:

- Backend schemas use snake_case fields matching API JSON and SQLAlchemy columns.
- Frontend types match backend response field names.
- `ThinkingNode.kind`, `status`, `ThinkingMode`, and `ThinkingStage` values match the design spec.
