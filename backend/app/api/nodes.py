from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import MindmapNode
from app.schemas.node import NodeCreate, NodeResponse, NodeUpdate

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.post("", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(
    node_data: NodeCreate,
    db: Session = Depends(get_db)
) -> MindmapNode:
    """Create a new mindmap node."""
    new_node = MindmapNode(
        project_id=node_data.project_id,
        parent_id=node_data.parent_id,
        label=node_data.label,
        question=node_data.question,
        context=node_data.context,
        answer=node_data.answer,
        extracted_points=node_data.extracted_points,
        status=node_data.status.value,
        depth=node_data.depth,
        position=node_data.position
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)

    return new_node


@router.get("/{node_id}", response_model=NodeResponse)
def get_node(node_id: str, db: Session = Depends(get_db)) -> MindmapNode:
    """Get a node by ID."""
    node = db.query(MindmapNode).filter(MindmapNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.put("/{node_id}", response_model=NodeResponse)
def update_node(
    node_id: str,
    node_data: NodeUpdate,
    db: Session = Depends(get_db)
) -> MindmapNode:
    """Update a node."""
    node = db.query(MindmapNode).filter(MindmapNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    for key, value in node_data.model_dump(exclude_unset=True).items():
        if hasattr(node, key) and value is not None:
            setattr(node, key, value)

    db.commit()
    db.refresh(node)
    return node


@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: str, db: Session = Depends(get_db)) -> None:
    """Delete a node."""
    node = db.query(MindmapNode).filter(MindmapNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    db.delete(node)
    db.commit()
    return None


@router.get("/{node_id}/children", response_model=list[NodeResponse])
def get_node_children(node_id: str, db: Session = Depends(get_db)) -> list[MindmapNode]:
    """Get all children of a node."""
    children = db.query(MindmapNode).filter(
        MindmapNode.parent_id == node_id
    ).all()
    return children
