from app.services.thinking_mode_service import ThinkingStateSignals, recommend_thinking_mode


def test_sparse_initial_state_recommends_diverge():
    signals = ThinkingStateSignals(turn_count=1, node_count=1, open_question_count=0)
    result = recommend_thinking_mode(signals)
    assert result.mode == "diverge"
    assert "early" in result.reason.lower() or "sparse" in result.reason.lower()


def test_dense_map_with_many_open_questions_recommends_converge():
    signals = ThinkingStateSignals(turn_count=8, node_count=24, open_question_count=7, decision_count=1, map_density="high")
    result = recommend_thinking_mode(signals)
    assert result.mode == "converge"
    assert "open questions" in result.reason.lower()


def test_user_requested_action_plan_recommends_converge():
    signals = ThinkingStateSignals(turn_count=4, node_count=6, user_requested_action_plan=True)
    result = recommend_thinking_mode(signals)
    assert result.mode == "converge"
    assert "action" in result.reason.lower()
