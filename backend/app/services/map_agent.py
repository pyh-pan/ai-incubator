from typing import Any

from app.schemas.v2 import ThinkingAgentOutput


def _build_center_node_patch(
    context: dict[str, Any],
    context_sufficiency: str,
    unresolved_context_gaps: list[str] | None = None,
) -> dict[str, Any]:
    patch: dict[str, Any] = {"context_sufficiency": context_sufficiency}
    project_title = (context.get("project") or {}).get("title")
    if project_title:
        patch["title"] = project_title
        patch["idea_summary"] = project_title
    if unresolved_context_gaps is not None:
        patch["unresolved_context_gaps"] = unresolved_context_gaps
    return patch


def build_map_output(context: dict[str, Any], thinking_output: ThinkingAgentOutput) -> dict[str, Any]:
    center_node = (context.get("map_state") or {}).get("center_node") or {}
    center_id = center_node.get("id")

    node_operations: list[dict[str, Any]] = []
    conversation_events: list[dict[str, Any]] = []

    if thinking_output.background_questions:
        questions = [question.model_dump(mode="json") for question in thinking_output.background_questions]
        conversation_events.append(
            {
                "role": "assistant",
                "source": "system",
                "content": "\n".join(f"{index + 1}. {item['question']}" for index, item in enumerate(questions)),
                "message_metadata": {
                    "message_type": "background_question_batch",
                    "background_questions": questions,
                    "visible_reasoning_summary": thinking_output.reasoning_trace.visible_summary,
                    "collapsed_by_default": True,
                },
            }
        )
        return {
            "center_node_patch": _build_center_node_patch(
                context,
                "insufficient",
                [question.expected_signal for question in thinking_output.background_questions],
            ),
            "node_operations": node_operations,
            "conversation_events": conversation_events,
        }

    if thinking_output.follow_up_questions:
        questions = [question.model_dump(mode="json") for question in thinking_output.follow_up_questions]
        linked_node_ids = [item["parent_question_id"] for item in questions]
        for question in thinking_output.follow_up_questions:
            node_operations.append(
                {
                    "type": "create_followup_node",
                    "parent_id": str(question.parent_question_id),
                    "title": question.short_title,
                    "detail_question": question.question,
                    "rationale": question.why_this_matters,
                    "expected_answer_type": question.expected_answer_type,
                    "status": "open",
                }
            )
        conversation_events.append(
            {
                "role": "assistant",
                "source": "system",
                "content": "\n".join(f"{index + 1}. {item['question']}" for index, item in enumerate(questions)),
                "message_metadata": {
                    "message_type": "assistant_followup",
                    "linked_node_ids": linked_node_ids,
                    "question_batch": questions,
                    "follow_up_questions": questions,
                    "visible_reasoning_summary": thinking_output.reasoning_trace.visible_summary,
                    "collapsed_by_default": True,
                },
            }
        )

    if thinking_output.thinking_questions:
        questions = [question.model_dump(mode="json") for question in thinking_output.thinking_questions]
        if center_id:
            for question in thinking_output.thinking_questions:
                node_operations.append(
                    {
                        "type": "create_question_node",
                        "parent_id": center_id,
                        "title": question.short_title,
                        "detail_question": question.question,
                        "rationale": question.why_this_matters,
                        "expected_answer_type": question.expected_answer_type,
                        "status": "open",
                    }
                )
        conversation_events.append(
            {
                "role": "assistant",
                "source": "system",
                "content": "\n".join(f"{index + 1}. {item['question']}" for index, item in enumerate(questions)),
                "message_metadata": {
                    "message_type": "question_batch",
                    "question_batch": questions,
                    "visible_reasoning_summary": thinking_output.reasoning_trace.visible_summary,
                    "collapsed_by_default": True,
                },
            }
        )

    return {
        "center_node_patch": _build_center_node_patch(context, thinking_output.context_sufficiency),
        "node_operations": node_operations,
        "conversation_events": conversation_events,
    }
