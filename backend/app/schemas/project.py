from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class FrameworkType(str, Enum):
    PRODUCT_MANAGER = "product_manager"
    BUSINESS_CANVAS = "business_canvas"
    TECHNICAL_FEASIBILITY = "technical_feasibility"
    SOCRATIC = "socratic"


class ProjectCreate(BaseModel):
    title: str
    framework: FrameworkType


class ProjectUpdate(BaseModel):
    title: str | None = None
    framework: FrameworkType | None = None
    status: str | None = None


class ProjectResponse(BaseModel):
    id: str
    user_id: str
    title: str
    framework: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
