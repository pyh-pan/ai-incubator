import re
from typing import Any, Literal, TypedDict, cast


ThinkingMode = Literal["diverge", "converge", "clarify", "challenge", "validate"]


class FallbackTurn(TypedDict):
    title: str
    kind: str
    question: str
    summary: str
    intent: str


GENERIC_QUESTION_PATTERNS = (
    "还有什么需要补充",
    "还有哪些需要补充",
    "还有哪些信息可以补充",
    "还有哪些细节需要补充",
    "你有什么想法",
    "请详细描述",
)


MODE_TEMPLATES: dict[ThinkingMode, tuple[str, str, str, str]] = {
    "clarify": (
        "Clarify focus",
        "question",
        "围绕「{anchor}」，这里最需要先定义清楚的对象、场景或成功标准是什么？",
        "Clarify the most ambiguous part before adding more structure.",
    ),
    "challenge": (
        "Stress test",
        "risk",
        "如果「{anchor}」这个方向不成立，最可能是哪一个关键假设错了？你会看到什么反证？",
        "Challenge the weakest assumption instead of repeating the same line of thought.",
    ),
    "validate": (
        "Validation signal",
        "question",
        "围绕「{anchor}」，哪个最小证据能证明这件事值得继续？你准备如何在一周内验证？",
        "Turn the idea into an observable validation signal.",
    ),
    "diverge": (
        "New angle",
        "question",
        "除了「{anchor}」这个切入点，还有哪两个完全不同的用户场景也可能有同样强的需求？",
        "Open adjacent possibilities while the map is still sparse.",
    ),
    "converge": (
        "Next step",
        "next_step",
        "基于「{anchor}」，现在最小、最可执行的下一步是什么？完成后你会用什么结果判断方向？",
        "Convert open thinking into a concrete next action.",
    ),
}


def normalize_question(question: str) -> str:
    """Normalize a question for duplicate and generic-question checks."""
    return re.sub(r"[\s，,。\.！？!?；;:：、\"'“”‘’（）()\[\]【】\-]+", "", question or "").strip().lower()


def is_generic_question(question: str) -> bool:
    normalized = normalize_question(question)
    return any(pattern in normalized for pattern in GENERIC_QUESTION_PATTERNS)


def has_duplicate_questions(questions: list[str]) -> bool:
    seen: set[str] = set()
    for question in questions:
        normalized = normalize_question(question)
        if not normalized:
            continue
        if normalized in seen:
            return True
        seen.add(normalized)
    return False


def _anchor_text(content: str) -> str:
    cleaned = re.sub(r"\s+", " ", (content or "").strip())
    if not cleaned:
        return "当前想法"
    return cleaned[:28] + ("..." if len(cleaned) > 28 else "")


def _coerce_mode(mode: str) -> ThinkingMode:
    if mode in MODE_TEMPLATES:
        return cast(ThinkingMode, mode)
    return "clarify"


def build_fallback_turn(content: str, mode: str, context: dict[str, Any] | None = None) -> FallbackTurn:
    """Build a concrete v2 fallback question without exposing fixed thinking frameworks."""
    selected_mode = _coerce_mode(mode)
    title, kind, question_template, summary = MODE_TEMPLATES[selected_mode]
    anchor = _anchor_text(content)
    question = question_template.format(anchor=anchor)

    if is_generic_question(question):
        question = f"围绕「{anchor}」，哪一个具体事实最能改变你对这个方向的判断？"

    return {
        "title": title,
        "kind": kind,
        "question": question,
        "summary": summary,
        "intent": summary,
    }
