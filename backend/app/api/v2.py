from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.core.time import utc_now
from app.models import ConversationMessageV2, Project, RestructureSuggestion, ThinkingNode
from app.schemas.v2 import NodeAnswerRequest, TurnRequest, TurnResponse, WorkspaceResponse
from app.services.dual_agent_orchestrator import answer_node, bootstrap_workspace_if_needed, submit_chat_turn
from app.services.incubator_orchestrator import ensure_root_node, run_turn
from app.services.map_update_service import apply_map_operations
from app.services.workspace_context_builder import build_center_context

router = APIRouter(prefix="/v2", tags=["v2"])


def get_project_or_404(db: Session, project_id: UUID, user_id: UUID) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def build_workspace(db: Session, project: Project) -> dict:
    _, root_created = ensure_root_node(db, project)
    bootstrapped = bootstrap_workspace_if_needed(db, project)
    if root_created or bootstrapped:
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
        .filter(
            RestructureSuggestion.project_id == project.id,
            RestructureSuggestion.status == "pending",
        )
        .order_by(RestructureSuggestion.created_at.asc())
        .all()
    )

    return {
        "project_id": project.id,
        "title": project.title,
        "thinking_mode": project.thinking_mode,
        "thinking_stage": project.thinking_stage,
        "center_context": build_center_context(project),
        "messages": messages,
        "nodes": nodes,
        "suggestions": suggestions,
        "answer_matches": [],
    }


@router.get("/projects/{project_id}/workspace", response_model=WorkspaceResponse)
def get_workspace(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    project = get_project_or_404(db, project_id, user_id)
    return build_workspace(db, project)


@router.post("/projects/{project_id}/turns", response_model=TurnResponse)
def create_turn(
    project_id: UUID,
    request: TurnRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    project = get_project_or_404(db, project_id, user_id)
    if request.source == "chat":
        user_message, assistant_message = submit_chat_turn(db, project, request.content)
        db.commit()
        db.refresh(project)
    else:
        user_message, assistant_message = run_turn(db, project, request)
    workspace = build_workspace(db, project)
    return {
        **workspace,
        "user_message": user_message,
        "assistant_message": assistant_message,
    }


@router.post("/projects/{project_id}/nodes/{node_id}/answer", response_model=WorkspaceResponse)
def answer_project_node(
    project_id: UUID,
    node_id: UUID,
    request: NodeAnswerRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    project = get_project_or_404(db, project_id, user_id)
    node = (
        db.query(ThinkingNode)
        .filter(
            ThinkingNode.id == node_id,
            ThinkingNode.project_id == project.id,
        )
        .first()
    )
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    if node.kind not in {"question", "followup"}:
        raise HTTPException(status_code=400, detail="Only question nodes can be answered")

    answer_node(db, project, node, request.content)
    db.commit()
    db.refresh(project)
    return build_workspace(db, project)


@router.post("/restructure-suggestions/{suggestion_id}/reject", response_model=WorkspaceResponse)
def reject_suggestion(
    suggestion_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    suggestion = db.query(RestructureSuggestion).filter(RestructureSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    project = get_project_or_404(db, suggestion.project_id, user_id)
    suggestion.status = "rejected"
    suggestion.resolved_at = utc_now()
    db.commit()
    return build_workspace(db, project)


@router.post("/restructure-suggestions/{suggestion_id}/accept", response_model=WorkspaceResponse)
def accept_suggestion(
    suggestion_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> dict:
    suggestion = db.query(RestructureSuggestion).filter(RestructureSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="Suggestion not found")

    project = get_project_or_404(db, suggestion.project_id, user_id)
    try:
        apply_map_operations(db, suggestion.project_id, suggestion.operations)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    suggestion.status = "accepted"
    suggestion.resolved_at = utc_now()
    db.commit()
    return build_workspace(db, project)
