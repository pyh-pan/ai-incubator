import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, IncubatorRun, Project, ThinkingNode
from app.schemas.v2 import AIMapUpdate, AIOrchestratorOutput, CurrentSummary, MapOperation, TurnRequest
from app.services.ai_service import get_ai_client, get_model
from app.services.map_update_service import validate_operation_risk
from app.services.thinking_mode_service import ThinkingStateSignals, recommend_thinking_mode


SYSTEM_CONTEXT_V2 = """You are AI Incubator's thinking partner.
Help the user clarify vague ideas through questions, reflection, and structure.
Do not use visible fixed frameworks. Use them only as private inspiration.
Balance divergent and convergent thinking.
Ask one main question per turn.
Separate facts, assumptions, insights, open questions, decisions, risks, and next steps.
Suggest high-risk map restructuring only as suggestions requiring confirmation.
Return only valid JSON matching the requested schema.
"""


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


def mock_ai_response(content: str, mode, context: dict | None = None) -> AIOrchestratorOutput:
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


def build_ai_context(
    project: Project,
    request: TurnRequest,
    signals: ThinkingStateSignals,
    recommended_mode: str,
    root_node: ThinkingNode,
) -> dict:
    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            "more_info": project.more_info,
            "thinking_stage": project.thinking_stage,
            "thinking_mode": project.thinking_mode,
            "summary_snapshot": project.summary_snapshot,
        },
        "root_node": {
            "id": str(root_node.id),
            "title": root_node.title,
            "summary": root_node.summary,
        },
        "user_message": {
            "content": request.content,
            "source": request.source,
            "node_id": str(request.node_id) if request.node_id else None,
        },
        "recommended_mode": recommended_mode,
        "signals": signals.__dict__,
        "output_schema": AIOrchestratorOutput.model_json_schema(),
    }


def call_ai_orchestrator(content: str, mode: str, context: dict | None = None) -> AIOrchestratorOutput:
    client = get_ai_client()
    if client is None:
        return mock_ai_response(content, mode)

    response = client.chat.completions.create(
        model=get_model(),
        messages=[
            {"role": "system", "content": SYSTEM_CONTEXT_V2},
            {
                "role": "user",
                "content": json.dumps(context or {"content": content, "recommended_mode": mode}, ensure_ascii=False),
            },
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    response_content = response.choices[0].message.content or "{}"
    return AIOrchestratorOutput.model_validate_json(response_content)


def run_turn(
    db: Session,
    project: Project,
    request: TurnRequest,
    ai_func=call_ai_orchestrator,
) -> tuple[ConversationMessageV2, ConversationMessageV2]:
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

    ai_context = build_ai_context(project, request, signals, recommendation.mode, root_node)
    ai_output = ai_func(request.content, recommendation.mode, ai_context)

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

    configured_client = get_ai_client()
    db.add(
        IncubatorRun(
            project_id=project.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            model=get_model() if configured_client else "mock-v2",
            input_payload={
                "content": request.content,
                "source": request.source,
                "node_id": str(request.node_id) if request.node_id else None,
                "signals": signals.__dict__,
                "context": ai_context,
            },
            output_payload=ai_output.model_dump(mode="json"),
            latency_ms=0,
        )
    )
    db.commit()
    db.refresh(user_message)
    db.refresh(assistant_message)
    return user_message, assistant_message
