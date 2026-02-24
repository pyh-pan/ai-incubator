from datetime import datetime

import uuid
from sqlalchemy import Column, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    framework = Column(String, nullable=False)  # product_manager, business_canvas, etc.
    status = Column(SQLEnum("active", "archived"), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow(), onupdate=lambda: datetime.utcnow())

    # Relationships
    user = relationship("User", back_populates="projects")
    nodes = relationship("MindmapNode", back_populates="project", cascade="all, delete-orphan")
