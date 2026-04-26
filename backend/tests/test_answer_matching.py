from app.services.dual_agent_orchestrator import match_answers_to_nodes


def test_batch_answer_matches_multiple_nodes_by_title_and_question():
    nodes = [
        {"id": "node-user", "title": "目标用户", "question": "第一批用户是谁？"},
        {"id": "node-experience", "title": "核心体验", "question": "核心体验是什么？"},
    ]
    content = "目标用户是推理小说作者。核心体验应该是破案推理，不是剧情分支。"

    matches = match_answers_to_nodes(content, nodes)

    assert [match["node_id"] for match in matches] == ["node-user", "node-experience"]
    assert all(match["confidence"] in {"high", "medium"} for match in matches)
