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
        return "low"

    if operation.type == "mark_answered":
        if not operation.node_id:
            raise ValueError("mark_answered requires node_id")
        return "low"

    if operation.type in HIGH_RISK_OPERATIONS:
        if operation.type != "merge_nodes" and not operation.node_id:
            raise ValueError(f"{operation.type} requires node_id")
        if operation.type == "merge_nodes" and len(operation.source_node_ids) < 2:
            raise ValueError("merge_nodes requires at least two source_node_ids")
        return "high"

    raise ValueError(f"Unsupported operation type: {operation.type}")
