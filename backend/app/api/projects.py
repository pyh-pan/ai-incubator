from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user_id
from app.models import (
    ConversationHistory,
    ConversationMessageV2,
    EvolutionHistory,
    IncubatorRun,
    MindmapNode,
    Project,
    RestructureSuggestion,
    ThinkingNode,
)
from app.schemas.node import NodeResponse
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_data: ProjectCreate,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Project:
    """Create a new project."""
    new_project = Project(
        user_id=user_id,
        title=project_data.title,
        more_info=project_data.more_info,
        framework=project_data.framework.value,
        status="active"
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    return new_project


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[Project]:
    """List all projects for current user."""
    projects = db.query(Project).filter(Project.user_id == user_id).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Project:
    """Get a project by ID."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: UUID,
    project_data: dict[str, Any],
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> Project:
    """Update a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    for key, value in project_data.items():
        if hasattr(project, key) and value is not None:
            setattr(project, key, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> None:
    """Delete a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    mindmap_node_ids = [
        node_id
        for (node_id,) in db.query(MindmapNode.id)
        .filter(MindmapNode.project_id == project.id)
        .all()
    ]
    if mindmap_node_ids:
        db.query(EvolutionHistory).filter(EvolutionHistory.node_id.in_(mindmap_node_ids)).delete(synchronize_session=False)
    db.query(ConversationHistory).filter(ConversationHistory.project_id == project.id).delete(synchronize_session=False)

    db.query(IncubatorRun).filter(IncubatorRun.project_id == project.id).delete(synchronize_session=False)
    db.query(RestructureSuggestion).filter(RestructureSuggestion.project_id == project.id).delete(synchronize_session=False)
    db.query(ConversationMessageV2).filter(ConversationMessageV2.project_id == project.id).delete(synchronize_session=False)
    db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id).delete(synchronize_session=False)

    db.delete(project)
    db.commit()
    return None


@router.get("/{project_id}/mindmap", response_model=list[NodeResponse])
def get_project_mindmap(
    project_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    db: Session = Depends(get_db),
) -> list[MindmapNode]:
    """Get all nodes for a project's mindmap."""
    project = db.query(Project).filter(Project.id == project_id, Project.user_id == user_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    nodes = db.query(MindmapNode).filter(
        MindmapNode.project_id == project_id,
        MindmapNode.parent_id.is_(None)
    ).all()

    # Load children recursively (simplified)
    def load_children(parent_node):
        children = db.query(MindmapNode).filter(
            MindmapNode.parent_id == parent_node.id
        ).all()
        for child in children:
            load_children(child)
        parent_node.children = children

    for node in nodes:
        load_children(node)

    return nodes
