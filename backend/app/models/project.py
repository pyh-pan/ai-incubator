from datetime import datetime

import uuid
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base

JSONBType = JSON().with_variant(JSONB, "postgresql")


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    more_info = Column(Text, nullable=True)
    framework = Column(String, nullable=False)  # product_manager, business_canvas, etc.
    status = Column(SQLEnum("active", "archived"), nullable=False, default="active")
    system_context_version = Column(String, nullable=False, default="v2.0")
    thinking_stage = Column(String, nullable=True)
    thinking_mode = Column(String, nullable=True)
    summary_snapshot = Column(JSONBType, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    user = relationship("User", back_populates="projects")
    nodes = relationship("MindmapNode", back_populates="project", cascade="all, delete-orphan")
