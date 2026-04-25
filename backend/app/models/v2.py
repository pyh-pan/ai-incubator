from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

JSONBType = JSON().with_variant(JSONB, "postgresql")


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
    message_metadata = Column(JSONBType, nullable=True)
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
    layout = Column(JSONBType, nullable=True)
    source_message_ids = Column(JSONBType, nullable=False, default=list)
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
    operations = Column(JSONBType, nullable=False)
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
    input_payload = Column(JSONBType, nullable=False)
    output_payload = Column(JSONBType, nullable=True)
    error = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=utcnow)
