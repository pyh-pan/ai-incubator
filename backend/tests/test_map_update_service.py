import uuid

import pytest

from app.schemas.v2 import MapOperation
from app.services.map_update_service import HIGH_RISK_OPERATIONS, LOW_RISK_OPERATIONS, validate_operation_risk


def test_create_node_is_low_risk_when_required_fields_exist():
    operation = MapOperation(type="create_node", parent_id=str(uuid.uuid4()), title="Target user", kind="question")
    assert validate_operation_risk(operation) == "low"


def test_move_node_is_high_risk():
    operation = MapOperation(type="move_node", node_id=str(uuid.uuid4()), parent_id=str(uuid.uuid4()))
    assert validate_operation_risk(operation) == "high"


def test_update_node_requires_update_payload():
    operation = MapOperation(type="update_node", node_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="at least one update"):
        validate_operation_risk(operation)


def test_update_node_with_summary_remains_low_risk():
    operation = MapOperation(type="update_node", node_id=str(uuid.uuid4()), summary="Updated summary")
    assert validate_operation_risk(operation) == "low"


def test_update_node_rejects_title_payload():
    operation = MapOperation(type="update_node", node_id=str(uuid.uuid4()), title="Renamed node")
    with pytest.raises(ValueError, match="rename_node"):
        validate_operation_risk(operation)


def test_update_node_rejects_parent_id_payload():
    operation = MapOperation(type="update_node", node_id=str(uuid.uuid4()), parent_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="move_node"):
        validate_operation_risk(operation)


def test_mark_answered_requires_node_id():
    operation = MapOperation(type="mark_answered")
    with pytest.raises(ValueError, match="node_id"):
        validate_operation_risk(operation)


def test_move_node_requires_parent_id():
    operation = MapOperation(type="move_node", node_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="parent_id"):
        validate_operation_risk(operation)


def test_rename_node_requires_title():
    operation = MapOperation(type="rename_node", node_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="title"):
        validate_operation_risk(operation)


def test_merge_nodes_requires_two_source_node_ids():
    operation = MapOperation(type="merge_nodes", source_node_ids=[str(uuid.uuid4())])
    with pytest.raises(ValueError, match="at least two source_node_ids"):
        validate_operation_risk(operation)


def test_split_node_requires_source_node_ids():
    operation = MapOperation(type="split_node", node_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="source_node_ids"):
        validate_operation_risk(operation)


def test_delete_node_requires_node_id():
    operation = MapOperation(type="delete_node")
    with pytest.raises(ValueError, match="node_id"):
        validate_operation_risk(operation)


def test_create_node_requires_title_and_kind():
    operation = MapOperation(type="create_node", parent_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="title and kind"):
        validate_operation_risk(operation)


def test_operation_sets_are_disjoint():
    assert LOW_RISK_OPERATIONS.isdisjoint(HIGH_RISK_OPERATIONS)
