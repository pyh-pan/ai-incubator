from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class FrameworkType(str, Enum):
    GENERAL = "general"
    PRODUCT_MANAGER = "product_manager"
    BUSINESS_CANVAS = "business_canvas"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    SOCRATIC = "socratic"


class ProjectCreate(BaseModel):
    title: str
    more_info: str | None = None
    framework: FrameworkType = FrameworkType.GENERAL


class ProjectUpdate(BaseModel):
    title: str | None = None
    more_info: str | None = None
    framework: FrameworkType | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    more_info: str | None = None
    framework: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
