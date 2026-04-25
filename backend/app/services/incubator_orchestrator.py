from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, IncubatorRun, Project, ThinkingNode
from app.schemas.v2 import AIMapUpdate, AIOrchestratorOutput, CurrentSummary, MapOperation, TurnRequest
from app.services.map_update_service import validate_operation_risk
from app.services.thinking_mode_service import ThinkingStateSignals, recommend_thinking_mode


def ensure_root_node(db: Session, project: Project) -> tuple[ThinkingNode, bool]:
    root_node = (
        db.query(ThinkingNode)
        .filter(
            ThinkingNode.project_id == project.id,
            ThinkingNode.parent_id.is_(None),
        )
        .order_by(ThinkingNode.created_at.asc())
        .first()
    )
    if root_node:
        return root_node, False

    root_node = ThinkingNode(
        project_id=project.id,
        parent_id=None,
        kind="idea",
        status="open",
        title=project.title,
        summary=project.summary_snapshot.get("overview") if project.summary_snapshot else None,
        sort_order=0,
        layout={"x": 0, "y": 0, "role": "center"},
        source_message_ids=[],
        confidence=100,
    )
    db.add(root_node)
    db.flush()
    return root_node, True


def build_signals(db: Session, project_id) -> ThinkingStateSignals:
    turn_count = (
        db.query(func.count(ConversationMessageV2.id))
        .filter(
            ConversationMessageV2.project_id == project_id,
            ConversationMessageV2.role == "user",
        )
        .scalar()
        or 0
    )
    node_count = db.query(func.count(ThinkingNode.id)).filter(ThinkingNode.project_id == project_id).scalar() or 0
    answered_node_count = (
        db.query(func.count(ThinkingNode.id))
        .filter(
            ThinkingNode.project_id == project_id,
            ThinkingNode.status == "answered",
        )
        .scalar()
        or 0
    )
    open_question_count = (
        db.query(func.count(ThinkingNode.id))
        .filter(
            ThinkingNode.project_id == project_id,
            ThinkingNode.kind == "question",
            ThinkingNode.status == "open",
        )
        .scalar()
        or 0
    )
    decision_count = (
        db.query(func.count(ThinkingNode.id))
        .filter(
            ThinkingNode.project_id == project_id,
            ThinkingNode.kind == "decision",
        )
        .scalar()
        or 0
    )
    assumption_count = (
        db.query(func.count(ThinkingNode.id))
        .filter(
            ThinkingNode.project_id == project_id,
            ThinkingNode.kind == "assumption",
        )
        .scalar()
        or 0
    )
    risk_count = (
        db.query(func.count(ThinkingNode.id))
        .filter(
            ThinkingNode.project_id == project_id,
            ThinkingNode.kind == "risk",
        )
        .scalar()
        or 0
    )

    return ThinkingStateSignals(
        turn_count=turn_count,
        node_count=node_count,
        answered_node_count=answered_node_count,
        open_question_count=open_question_count,
        decision_count=decision_count,
        assumption_count=assumption_count,
        risk_count=risk_count,
        map_density="high" if node_count >= 12 else "low",
    )


def mock_ai_response(content: str, mode) -> AIOrchestratorOutput:
    trimmed_content = content.strip()
    question = "Who is the first specific user who would need this badly enough to try an early version?"
    if "?" in trimmed_content:
        question = "What evidence would make the answer to that question clearer?"

    operation = MapOperation(
        type="create_node",
        title="Target user",
        kind="question",
        status="open",
        question=question,
        summary="Clarify the initial audience and urgency.",
    )
    risk = validate_operation_risk(operation)

    return AIOrchestratorOutput(
        thinking_mode=mode,
        stage="discover",
        mode_reason=f"Mock orchestration selected {mode} for the current workspace state.",
        assistant_message=(
            "Let's anchor this idea in one concrete user and the problem they already feel. "
            f"{question}"
        ),
        next_question=question,
        question_intent="Identify a narrow initial user and concrete demand signal.",
        map_updates=[AIMapUpdate(operation=operation, risk=risk)],
        detected_gaps=["Initial target user is not yet specific enough."],
        current_summary=CurrentSummary(
            facts=[trimmed_content],
            open_questions=[question],
        ),
    )


def run_turn(db: Session, project: Project, request: TurnRequest) -> tuple[ConversationMessageV2, ConversationMessageV2]:
    root_node, _ = ensure_root_node(db, project)
    signals = build_signals(db, project.id)
    signals.user_requested_action_plan = "plan" in request.content.lower() or "next step" in request.content.lower()
    signals.user_expressed_confusion = "confused" in request.content.lower() or "unclear" in request.content.lower()
    recommendation = recommend_thinking_mode(signals)

    user_message = ConversationMessageV2(
        project_id=project.id,
        node_id=request.node_id,
        role="user",
        source=request.source,
        content=request.content,
    )
    db.add(user_message)
    db.flush()

    ai_output = mock_ai_response(request.content, recommendation.mode)

    assistant_message = ConversationMessageV2(
        project_id=project.id,
        role="assistant",
        source="chat",
        content=ai_output.assistant_message,
        thinking_mode=ai_output.thinking_mode,
        stage=ai_output.stage,
        message_metadata={
            "mode_reason": ai_output.mode_reason,
            "next_question": ai_output.next_question,
            "question_intent": ai_output.question_intent,
            "detected_gaps": ai_output.detected_gaps,
        },
    )
    db.add(assistant_message)
    db.flush()

    next_sort_order = db.query(func.count(ThinkingNode.id)).filter(ThinkingNode.project_id == project.id).scalar() or 0
    for update in ai_output.map_updates:
        operation = update.operation
        if operation.type != "create_node":
            continue
        node = ThinkingNode(
            project_id=project.id,
            parent_id=operation.parent_id or root_node.id,
            kind=operation.kind,
            status=operation.status or "open",
            title=operation.title,
            summary=operation.summary,
            question=operation.question,
            sort_order=next_sort_order,
            layout={"x": 240, "y": 120 + (next_sort_order * 80)},
            source_message_ids=[str(user_message.id), str(assistant_message.id)],
            confidence=80,
        )
        next_sort_order += 1
        db.add(node)

    project.thinking_mode = ai_output.thinking_mode
    project.thinking_stage = ai_output.stage
    project.summary_snapshot = ai_output.current_summary.model_dump(mode="json")

    db.add(
        IncubatorRun(
            project_id=project.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            model="mock-v2",
            input_payload={
                "content": request.content,
                "source": request.source,
                "node_id": str(request.node_id) if request.node_id else None,
                "signals": signals.__dict__,
            },
            output_payload=ai_output.model_dump(mode="json"),
            latency_ms=0,
        )
    )
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message
