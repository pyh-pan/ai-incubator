from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


ThinkingMode = Literal["diverge", "converge", "clarify", "challenge", "validate"]
ThinkingStage = Literal["discover", "define", "develop", "deliver"]
NodeKind = Literal["idea", "question", "answer", "insight", "assumption", "decision", "risk", "next_step"]
NodeStatus = Literal["open", "answered", "suggested", "confirmed"]
MessageRole = Literal["user", "assistant"]
MessageSource = Literal["chat", "node"]
OperationType = Literal["create_node", "update_node", "mark_answered", "move_node", "rename_node", "merge_nodes", "split_node", "delete_node"]


class ThinkingNodeResponse(BaseModel):
    id: UUID
    project_id: UUID
    parent_id: UUID | None
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
    id: UUID
    project_id: UUID
    node_id: UUID | None
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
    id: UUID
    project_id: UUID
    status: str
    operations: list[MapOperation]
    rationale: str
    created_from_message_id: UUID | None
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
