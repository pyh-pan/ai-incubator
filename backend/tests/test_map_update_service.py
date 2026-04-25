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


def test_create_node_requires_title_and_kind():
    operation = MapOperation(type="create_node", parent_id=str(uuid.uuid4()))
    with pytest.raises(ValueError, match="title and kind"):
        validate_operation_risk(operation)


def test_operation_sets_are_disjoint():
    assert LOW_RISK_OPERATIONS.isdisjoint(HIGH_RISK_OPERATIONS)
