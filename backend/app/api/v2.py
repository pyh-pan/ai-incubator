from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import ConversationMessageV2, Project, RestructureSuggestion, ThinkingNode
from app.schemas.v2 import TurnRequest, TurnResponse, WorkspaceResponse
from app.services.incubator_orchestrator import ensure_root_node, run_turn

router = APIRouter(prefix="/v2", tags=["v2"])


def get_project_or_404(db: Session, project_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def build_workspace(db: Session, project: Project) -> dict:
    ensure_root_node(db, project)
    db.commit()
    db.refresh(project)

    messages = (
        db.query(ConversationMessageV2)
        .filter(ConversationMessageV2.project_id == project.id)
        .order_by(ConversationMessageV2.created_at.asc())
        .all()
    )
    nodes = (
        db.query(ThinkingNode)
        .filter(ThinkingNode.project_id == project.id)
        .order_by(ThinkingNode.parent_id.isnot(None), ThinkingNode.sort_order.asc(), ThinkingNode.created_at.asc())
        .all()
    )
    suggestions = (
        db.query(RestructureSuggestion)
        .filter(RestructureSuggestion.project_id == project.id)
        .order_by(RestructureSuggestion.created_at.asc())
        .all()
    )

    return {
        "project_id": project.id,
        "title": project.title,
        "thinking_mode": project.thinking_mode,
        "thinking_stage": project.thinking_stage,
        "messages": messages,
        "nodes": nodes,
        "suggestions": suggestions,
    }


@router.get("/projects/{project_id}/workspace", response_model=WorkspaceResponse)
def get_workspace(project_id: UUID, db: Session = Depends(get_db)) -> dict:
    project = get_project_or_404(db, project_id)
    return build_workspace(db, project)


@router.post("/projects/{project_id}/turns", response_model=TurnResponse)
def create_turn(project_id: UUID, request: TurnRequest, db: Session = Depends(get_db)) -> dict:
    project = get_project_or_404(db, project_id)
    user_message, assistant_message = run_turn(db, project, request)
    workspace = build_workspace(db, project)
    return {
        **workspace,
        "user_message": user_message,
        "assistant_message": assistant_message,
    }
