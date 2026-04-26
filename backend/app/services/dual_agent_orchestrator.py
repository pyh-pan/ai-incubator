from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import ConversationMessageV2, IncubatorRun, Project, ThinkingNode
from app.schemas.v2 import CenterContext
from app.services.incubator_orchestrator import ensure_root_node
from app.services.map_agent import build_map_output
from app.services.thinking_agent import run_thinking_agent
from app.services.workspace_context_builder import build_center_context, build_workspace_context


def _save_center_context(project: Project, center_context: CenterContext) -> None:
    snapshot = project.summary_snapshot if isinstance(project.summary_snapshot, dict) else {}
    project.summary_snapshot = {
        **snapshot,
        "center_context": center_context.model_dump(mode="json"),
    }


def _coerce_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (TypeError, ValueError):
        return None


def _merge_center_context(project: Project, patch: dict[str, Any]) -> CenterContext:
    current = build_center_context(project)
    updates = {
        key: value
        for key, value in patch.items()
        if key in CenterContext.model_fields and value is not None
    }
    for preserved_key in ("original_idea", "background_summary"):
        updates.pop(preserved_key, None)
    return current.model_copy(update=updates)


def _rich_bootstrap_hint(project: Project) -> dict[str, Any]:
    if not project.more_info:
        return {}

    has_rich_background = len(project.more_info.strip()) >= 30 and any(
        marker in project.more_info
        for marker in ("目标用户", "用户", "核心体验", "输入", "痛点", "场景", "target user", "user", "input")
    )
    if not has_rich_background:
        return {}

    target_users: list[str] = []
    for marker in ("目标用户是", "目标用户可能是", "用户是"):
        if marker in project.more_info:
            tail = project.more_info.split(marker, 1)[1]
            user_text = tail.split("，", 1)[0].split("。", 1)[0].strip()
            if user_text:
                target_users.append(user_text)
            break

    if not target_users:
        target_users = ["背景信息中描述的目标用户"]

    return {
        "background_summary": project.more_info,
        "known_facts": [project.more_info],
        "target_users": target_users,
    }


def _build_bootstrap_context(db: Session, project: Project) -> dict[str, Any]:
    context = build_workspace_context(db, project)
    project_context = context.setdefault("project", {})
    if isinstance(project_context, dict):
        project_context.update(_rich_bootstrap_hint(project))
    return context


def _apply_node_operations(db: Session, project: Project, operations: list[dict[str, Any]]) -> list[ThinkingNode]:
    created_nodes: list[ThinkingNode] = []
    next_sort_order = db.query(ThinkingNode).filter(ThinkingNode.project_id == project.id).count()

    for operation in operations:
        if operation.get("type") not in {"create_question_node", "create_followup_node"}:
            continue

        parent_id = _coerce_uuid(operation.get("parent_id"))
        if parent_id is None:
            continue

        parent_exists = (
            db.query(ThinkingNode.id)
            .filter(
                ThinkingNode.project_id == project.id,
                ThinkingNode.id == parent_id,
            )
            .first()
        )
        if not parent_exists:
            continue

        node_kind = "followup" if operation.get("type") == "create_followup_node" else "question"
        node = ThinkingNode(
            project_id=project.id,
            parent_id=parent_id,
            kind=node_kind,
            status=operation.get("status") or "open",
            title=operation.get("title") or "Untitled question",
            summary=operation.get("rationale"),
            question=operation.get("detail_question"),
            sort_order=next_sort_order,
            layout={
                "rationale": operation.get("rationale"),
                "expected_answer_type": operation.get("expected_answer_type"),
            },
            source_message_ids=[],
            confidence=85,
        )
        next_sort_order += 1
        db.add(node)
        created_nodes.append(node)

    return created_nodes


def _summarize_answer(content: str, limit: int = 280) -> str:
    normalized = " ".join(content.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[: limit - 1].rstrip()}..."


def _append_background_context(project: Project, content: str) -> None:
    current = build_center_context(project)
    normalized = " ".join(content.split())
    if not normalized:
        return

    known_facts = [fact for fact in current.known_facts if fact != normalized]
    known_facts.append(normalized)
    background_parts = [part for part in [current.background_summary, normalized] if part]
    target_users = list(current.target_users)
    if not target_users and ("用户" in normalized or "目标" in normalized or "user" in normalized.lower()):
        target_users.append("补充背景中描述的目标用户")

    _save_center_context(
        project,
        current.model_copy(
            update={
                "background_summary": "\n".join(dict.fromkeys(background_parts)),
                "known_facts": known_facts[-8:],
                "target_users": target_users,
            }
        ),
    )


def match_answers_to_nodes(content: str, nodes: list[dict[str, Any]]) -> list[dict[str, str]]:
    matches: list[dict[str, str]] = []
    normalized_content = content.replace("：", ":")
    for node in nodes:
        title = node.get("title") or ""
        question = node.get("question") or ""
        node_id = str(node.get("id") or "")
        if not node_id:
            continue
        if title and title in normalized_content:
            matches.append({"node_id": node_id, "extracted_answer": content, "confidence": "high"})
            continue
        if title and any(part for part in title.split() if part and part in normalized_content):
            matches.append({"node_id": node_id, "extracted_answer": content, "confidence": "medium"})
            continue
        if "用户" in question and "用户" in normalized_content:
            matches.append({"node_id": node_id, "extracted_answer": content, "confidence": "medium"})
            continue
        if "体验" in question and "体验" in normalized_content:
            matches.append({"node_id": node_id, "extracted_answer": content, "confidence": "medium"})
    return matches


def answer_node(
    db: Session,
    project: Project,
    node: ThinkingNode,
    content: str,
    *,
    record_user_message: bool = True,
    source_message_id: UUID | None = None,
    input_source: str = "node",
) -> None:
    node.status = "answered"
    node.answer_summary = _summarize_answer(content)

    user_message_id = source_message_id
    if record_user_message:
        user_message = ConversationMessageV2(
            project_id=project.id,
            node_id=node.id,
            role="user",
            source="node",
            content=content,
            message_metadata={
                "message_type": "user_answer",
                "linked_node_ids": [str(node.id)],
            },
        )
        db.add(user_message)
        db.flush()
        user_message_id = user_message.id

    context = build_workspace_context(
        db,
        project,
        user_input={
            "source": input_source,
            "content": content,
            "answered_node_ids": [str(node.id)],
        },
        focused_node=node,
    )
    thinking_output = run_thinking_agent(context)
    map_output = build_map_output(context, thinking_output)

    center_context = _merge_center_context(project, map_output.get("center_node_patch") or {})
    _save_center_context(project, center_context)

    assistant_message_ids: list[str] = []
    for event in map_output.get("conversation_events") or []:
        message = ConversationMessageV2(project_id=project.id, **event)
        db.add(message)
        db.flush()
        assistant_message_ids.append(str(message.id))

    created_nodes = _apply_node_operations(db, project, map_output.get("node_operations") or [])
    for created_node in created_nodes:
        created_node.source_message_ids = assistant_message_ids

    db.add(
        IncubatorRun(
            project_id=project.id,
            user_message_id=user_message_id,
            input_payload={"context": context, "node_answer": True, "user_message_id": str(user_message_id) if user_message_id else None},
            output_payload={
                "thinking": thinking_output.model_dump(mode="json"),
                "map": map_output,
            },
            model="dual-agent",
            latency_ms=0,
        )
    )


def _open_question_nodes(db: Session, project: Project) -> list[ThinkingNode]:
    return (
        db.query(ThinkingNode)
        .filter(
            ThinkingNode.project_id == project.id,
            ThinkingNode.kind.in_(["question", "followup"]),
            ThinkingNode.status == "open",
        )
        .order_by(ThinkingNode.sort_order.asc(), ThinkingNode.created_at.asc())
        .all()
    )


def submit_chat_turn(db: Session, project: Project, content: str) -> tuple[ConversationMessageV2, ConversationMessageV2]:
    user_message = ConversationMessageV2(
        project_id=project.id,
        role="user",
        source="chat",
        content=content,
        message_metadata={"message_type": "chat_background"},
    )
    db.add(user_message)
    db.flush()

    open_nodes = _open_question_nodes(db, project)
    matches = match_answers_to_nodes(content, [node_context for node_context in (_node_match_context(node) for node in open_nodes)])
    high_matches = [match for match in matches if match["confidence"] == "high"]

    if high_matches:
        nodes_by_id = {str(node.id): node for node in open_nodes}
        user_message.message_metadata = {
            "message_type": "batch_answer",
            "linked_node_ids": [match["node_id"] for match in high_matches],
            "answer_matches": high_matches,
        }
        for match in high_matches:
            node = nodes_by_id.get(match["node_id"])
            if node:
                answer_node(
                    db,
                    project,
                    node,
                    match["extracted_answer"],
                    record_user_message=False,
                    source_message_id=user_message.id,
                    input_source="chat",
                )

        assistant_message = _latest_assistant_message(db, project)
        if assistant_message:
            return user_message, assistant_message

    medium_matches = [match for match in matches if match["confidence"] == "medium"]
    if len(medium_matches) > 1:
        user_message.message_metadata = {
            "message_type": "batch_answer_candidate",
            "linked_node_ids": [match["node_id"] for match in medium_matches],
            "answer_matches": medium_matches,
        }
        assistant_message = ConversationMessageV2(
            project_id=project.id,
            role="assistant",
            source="system",
            content="我识别到这段回答可能对应多个问题，请在右侧节点中分别确认或补充。",
            message_metadata={
                "message_type": "match_confirmation",
                "linked_node_ids": [match["node_id"] for match in medium_matches],
                "answer_matches": medium_matches,
            },
        )
        db.add(assistant_message)
        db.flush()
        return user_message, assistant_message

    _append_background_context(project, content)
    context = build_workspace_context(
        db,
        project,
        user_input={"source": "chat", "content": content, "answered_node_ids": []},
    )
    thinking_output = run_thinking_agent(context)
    map_output = build_map_output(context, thinking_output)

    center_context = _merge_center_context(project, map_output.get("center_node_patch") or {})
    _save_center_context(project, center_context)

    assistant_message: ConversationMessageV2 | None = None
    assistant_message_ids: list[str] = []
    for event in map_output.get("conversation_events") or []:
        assistant_message = ConversationMessageV2(project_id=project.id, **event)
        db.add(assistant_message)
        db.flush()
        assistant_message_ids.append(str(assistant_message.id))

    created_nodes = _apply_node_operations(db, project, map_output.get("node_operations") or [])
    for created_node in created_nodes:
        created_node.source_message_ids = assistant_message_ids

    if assistant_message is None:
        assistant_message = ConversationMessageV2(
            project_id=project.id,
            role="assistant",
            source="system",
            content="我已经记录这部分背景，会继续围绕它完善问题。",
            message_metadata={"message_type": "question_batch"},
        )
        db.add(assistant_message)
        db.flush()

    db.add(
        IncubatorRun(
            project_id=project.id,
            user_message_id=user_message.id,
            assistant_message_id=assistant_message.id,
            input_payload={"context": context, "chat_turn": True},
            output_payload={
                "thinking": thinking_output.model_dump(mode="json"),
                "map": map_output,
            },
            model="dual-agent",
            latency_ms=0,
        )
    )
    return user_message, assistant_message


def _node_match_context(node: ThinkingNode) -> dict[str, Any]:
    return {
        "id": str(node.id),
        "title": node.title,
        "question": node.question,
    }


def _latest_assistant_message(db: Session, project: Project) -> ConversationMessageV2 | None:
    return (
        db.query(ConversationMessageV2)
        .filter(ConversationMessageV2.project_id == project.id, ConversationMessageV2.role == "assistant")
        .order_by(ConversationMessageV2.created_at.desc(), ConversationMessageV2.id.desc())
        .first()
    )


def bootstrap_workspace_if_needed(db: Session, project: Project) -> bool:
    existing_message = (
        db.query(ConversationMessageV2.id)
        .filter(ConversationMessageV2.project_id == project.id)
        .first()
    )
    if existing_message:
        return False

    ensure_root_node(db, project)
    context = _build_bootstrap_context(db, project)
    thinking_output = run_thinking_agent(context)
    map_output = build_map_output(context, thinking_output)

    center_context = _merge_center_context(project, map_output.get("center_node_patch") or {})
    _save_center_context(project, center_context)

    assistant_message_ids: list[str] = []
    for event in map_output.get("conversation_events") or []:
        message = ConversationMessageV2(project_id=project.id, **event)
        db.add(message)
        db.flush()
        assistant_message_ids.append(str(message.id))

    created_nodes = _apply_node_operations(db, project, map_output.get("node_operations") or [])
    for node in created_nodes:
        node.source_message_ids = assistant_message_ids

    db.add(
        IncubatorRun(
            project_id=project.id,
            input_payload={"context": context, "bootstrap": True},
            output_payload={
                "thinking": thinking_output.model_dump(mode="json"),
                "map": map_output,
            },
            model="dual-agent",
            latency_ms=0,
        )
    )
    return True
