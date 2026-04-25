from datetime import datetime

import uuid
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base

JSONBType = JSON().with_variant(JSONB, "postgresql")


class MindmapNode(Base):
    """Mindmap node model."""

    __tablename__ = "mindmap_nodes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("mindmap_nodes.id"), nullable=True)
    label = Column(String, nullable=False)
    question = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    answer = Column(Text, nullable=True)
    extracted_points = Column(JSONBType, nullable=True)  # List[str]
    status = Column(
        SQLEnum("unanswered", "in_progress", "answered"),
        nullable=False,
        default="unanswered"
    )
    depth = Column(Integer, nullable=False, default=0)
    position = Column(JSONBType, nullable=True)  # {x: number, y: number}
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    project = relationship("Project", back_populates="nodes")
    parent = relationship("MindmapNode", remote_side=[id], backref="children")


class ConversationHistory(Base):
    """Conversation history model."""

    __tablename__ = "conversation_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)
    node_id = Column(UUID(as_uuid=True), ForeignKey("mindmap_nodes.id"), nullable=True)
    role = Column(SQLEnum("user", "assistant"), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSONBType, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())


class EvolutionHistory(Base):
    """Evolution history model."""

    __tablename__ = "evolution_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    node_id = Column(UUID(as_uuid=True), ForeignKey("mindmap_nodes.id"), nullable=False)
    old_answer = Column(Text, nullable=True)
    new_answer = Column(Text, nullable=True)
    change_summary = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
