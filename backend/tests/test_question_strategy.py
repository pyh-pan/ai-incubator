from app.services.question_strategy import build_fallback_turn, has_duplicate_questions, is_generic_question, normalize_question


def test_normalize_question_removes_punctuation_and_spacing():
    first = normalize_question("  目标用户是谁？ ")
    second = normalize_question("目标 用户 是 谁")

    assert first == second


def test_generic_question_detector_rejects_low_value_followups():
    assert is_generic_question("还有什么需要补充？")
    assert is_generic_question("你还有哪些信息可以补充")
    assert not is_generic_question("第一个强需求用户是谁？他们现在如何解决这个问题？")


def test_duplicate_question_detector_uses_normalized_text():
    questions = ["目标用户是谁？", "目标 用户 是 谁", "如何验证需求？"]

    assert has_duplicate_questions(questions)
    assert not has_duplicate_questions(["目标用户是谁？", "如何验证需求？"])


def test_fallback_turn_anchors_question_to_user_content():
    fallback = build_fallback_turn(
        content="我想做一个帮助独立开发者验证 SaaS 想法的 AI 工具",
        mode="validate",
        context={},
    )

    assert fallback["title"]
    assert "question" in fallback
    assert "独立开发者" in fallback["question"] or "验证" in fallback["question"]
    assert not is_generic_question(fallback["question"])


def test_fallback_turn_uses_mode_without_exposing_fixed_frameworks():
    fallback = build_fallback_turn(
        content="用户说他们想用 AI 日记改善情绪复盘",
        mode="challenge",
        context={},
    )

    rendered = " ".join(str(value) for value in fallback.values())
    assert "critical_thinking" not in rendered
    assert "批判性思维框架" not in rendered
    assert "framework" not in rendered.lower()
    assert fallback["kind"] in {"question", "assumption", "risk", "next_step"}
