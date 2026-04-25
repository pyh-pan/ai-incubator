from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ThinkingNode
from app.schemas.v2 import MapOperation


LOW_RISK_OPERATIONS = {"create_node", "update_node", "mark_answered"}
HIGH_RISK_OPERATIONS = {"move_node", "rename_node", "merge_nodes", "split_node", "delete_node"}


def validate_operation_risk(operation: MapOperation) -> str:
    if operation.type == "create_node":
        if not operation.title or not operation.kind:
            raise ValueError("create_node requires title and kind")
        return "low"

    if operation.type == "update_node":
        if not operation.node_id:
            raise ValueError("update_node requires node_id")
        if operation.title:
            raise ValueError("update_node cannot rename nodes; use rename_node")
        if operation.parent_id:
            raise ValueError("update_node cannot move nodes; use move_node")
        update_fields = (
            operation.summary,
            operation.question,
            operation.status,
            operation.kind,
        )
        if not any(update_fields):
            raise ValueError("update_node requires at least one update payload")
        return "low"

    if operation.type == "mark_answered":
        if not operation.node_id:
            raise ValueError("mark_answered requires node_id")
        return "low"

    if operation.type == "move_node":
        if not operation.node_id:
            raise ValueError("move_node requires node_id")
        if not operation.parent_id:
            raise ValueError("move_node requires parent_id")
        return "high"

    if operation.type == "rename_node":
        if not operation.node_id:
            raise ValueError("rename_node requires node_id")
        if not operation.title:
            raise ValueError("rename_node requires title")
        return "high"

    if operation.type == "merge_nodes":
        if len(operation.source_node_ids) < 2:
            raise ValueError("merge_nodes requires at least two source_node_ids")
        return "high"

    if operation.type == "split_node":
        if not operation.node_id:
            raise ValueError("split_node requires node_id")
        if not operation.source_node_ids:
            raise ValueError("split_node requires source_node_ids")
        return "high"

    if operation.type == "delete_node":
        if not operation.node_id:
            raise ValueError("delete_node requires node_id")
        return "high"

    raise ValueError(f"Unsupported operation type: {operation.type}")


def apply_map_operation(db: Session, project_id: UUID, operation: MapOperation) -> None:
    validate_operation_risk(operation)

    if operation.type == "create_node":
        sort_order = db.query(func.count(ThinkingNode.id)).filter(ThinkingNode.project_id == project_id).scalar() or 0
        db.add(
            ThinkingNode(
                project_id=project_id,
                parent_id=operation.parent_id,
                kind=operation.kind,
                status=operation.status or "suggested",
                title=operation.title,
                summary=operation.summary,
                question=operation.question,
                sort_order=sort_order,
                layout=None,
                source_message_ids=[],
                confidence=75,
            )
        )
        return

    if not operation.node_id:
        raise ValueError(f"{operation.type} requires node_id")

    node = (
        db.query(ThinkingNode)
        .filter(
            ThinkingNode.id == operation.node_id,
            ThinkingNode.project_id == project_id,
        )
        .first()
    )
    if not node:
        raise ValueError("Target node not found")

    if operation.type == "update_node":
        if operation.summary is not None:
            node.summary = operation.summary
        if operation.question is not None:
            node.question = operation.question
        if operation.status is not None:
            node.status = operation.status
        if operation.kind is not None:
            node.kind = operation.kind
        return

    if operation.type == "mark_answered":
        node.status = "answered"
        if operation.summary is not None:
            node.answer_summary = operation.summary
        return

    if operation.type == "move_node":
        node.parent_id = operation.parent_id
        return

    if operation.type == "rename_node":
        node.title = operation.title
        return

    if operation.type == "delete_node":
        db.delete(node)
        return

    raise ValueError(f"{operation.type} is not implemented")


def apply_map_operations(db: Session, project_id: UUID, operations: list[dict]) -> None:
    for raw_operation in operations:
        operation = MapOperation.model_validate(raw_operation)
        apply_map_operation(db, project_id, operation)
