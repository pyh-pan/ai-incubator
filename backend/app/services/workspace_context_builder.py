from typing import Any

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, Project, ThinkingNode
from app.schemas.v2 import CenterContext


def build_center_context(project: Project) -> CenterContext:
    snapshot = project.summary_snapshot or {}
    existing = snapshot.get("center_context") if isinstance(snapshot, dict) else None
    if isinstance(existing, dict):
        try:
            return CenterContext.model_validate(existing)
        except ValidationError:
            pass

    if isinstance(snapshot, dict) and any(
        key in snapshot for key in ("facts", "assumptions", "risks", "decisions", "open_questions")
    ):
        return CenterContext(
            original_idea=project.title,
            idea_summary=project.title,
            background_summary=project.more_info,
            known_facts=snapshot.get("facts") or ([project.more_info] if project.more_info else []),
            assumptions=snapshot.get("assumptions") or [],
            unresolved_context_gaps=snapshot.get("open_questions") or [],
            context_sufficiency="unknown",
        )

    return CenterContext(
        original_idea=project.title,
        idea_summary=project.title,
        background_summary=project.more_info,
        known_facts=[project.more_info] if project.more_info else [],
        context_sufficiency="unknown",
    )


def _node_context(node: ThinkingNode) -> dict[str, Any]:
    return {
        "id": str(node.id),
        "parent_id": str(node.parent_id) if node.parent_id else None,
        "title": node.title,
        "kind": node.kind,
        "status": node.status,
        "question": node.question,
        "summary": node.summary,
        "answer_summary": node.answer_summary,
        "metadata": node.layout or {},
    }


def _message_context(message: ConversationMessageV2) -> dict[str, Any]:
    return {
        "id": str(message.id),
        "role": message.role,
        "source": message.source,
        "node_id": str(message.node_id) if message.node_id else None,
        "content": message.content,
        "metadata": message.message_metadata or {},
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def build_workspace_context(
    db: Session,
    project: Project,
    user_input: dict[str, Any] | None = None,
    focused_node: ThinkingNode | None = None,
) -> dict[str, Any]:
    center_context = build_center_context(project)
    focused_node_context = None
    if focused_node and focused_node.project_id == project.id:
        focused_node_context = _node_context(focused_node)

    nodes = (
        db.query(ThinkingNode)
        .filter(ThinkingNode.project_id == project.id)
        .order_by(
            ThinkingNode.parent_id.isnot(None),
            ThinkingNode.sort_order.asc(),
            ThinkingNode.created_at.asc(),
        )
        .all()
    )
    messages = (
        db.query(ConversationMessageV2)
        .filter(ConversationMessageV2.project_id == project.id)
        .order_by(ConversationMessageV2.created_at.desc(), ConversationMessageV2.id.desc())
        .limit(12)
        .all()
    )

    return {
        "project": {
            "id": str(project.id),
            "title": project.title,
            **center_context.model_dump(mode="json"),
        },
        "map_state": {
            "center_node": next((_node_context(node) for node in nodes if node.parent_id is None), None),
            "open_question_nodes": [
                _node_context(node)
                for node in nodes
                if node.kind in {"question", "followup"} and node.status == "open"
            ],
            "answered_nodes": [_node_context(node) for node in nodes if node.status == "answered"],
            "focused_node": focused_node_context,
        },
        "recent_conversation": [_message_context(message) for message in reversed(messages)],
        "user_input": user_input or {"source": "chat", "content": "", "answered_node_ids": []},
    }
