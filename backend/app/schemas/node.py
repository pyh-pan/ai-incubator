from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeStatus(str, Enum):
    UNANSWERED = "unanswered"
    IN_PROGRESS = "in_progress"
    ANSWERED = "answered"


class NodeBase(BaseModel):
    label: str
    question: str | None = None
    context: str | None = None


class NodeCreate(NodeBase):
    project_id: str
    parent_id: str | None = None
    answer: str | None = None
    extracted_points: list[str] | None = None
    status: NodeStatus = NodeStatus.UNANSWERED
    depth: int = 0
    position: dict[str, int] | None = None


class NodeUpdate(BaseModel):
    label: str | None = None
    question: str | None = None
    context: str | None = None
    answer: str | None = None
    extracted_points: list[str] | None = None
    status: NodeStatus | None = None
    position: dict[str, int] | None = None


class NodeResponse(NodeBase):
    id: str
    project_id: str
    parent_id: str | None
    answer: str | None
    extracted_points: list[str] | None
    status: str
    depth: int
    position: dict[str, int] | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AIRequest(BaseModel):
    idea: str


class AIExtractRequest(BaseModel):
    answer: str


class AIQuestionResponse(BaseModel):
    question: str
    context: str
    examples: list[str]


class AIExtractResponse(BaseModel):
    points: list[str]
    summary: str


class AIFrameworkRecommendation(BaseModel):
    framework: str
    confidence: float
    reason: str
