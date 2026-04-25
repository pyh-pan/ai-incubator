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
