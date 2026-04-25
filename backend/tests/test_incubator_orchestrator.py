import pytest
from pydantic import ValidationError

from app.schemas.v2 import AIOrchestratorOutput
from app.services import incubator_orchestrator
from app.services.incubator_orchestrator import call_ai_orchestrator
from app.services.question_strategy import is_generic_question


def test_ai_output_requires_one_valid_mode():
    with pytest.raises(ValidationError):
        AIOrchestratorOutput.model_validate(
            {
                "thinking_mode": "random",
                "stage": "discover",
                "mode_reason": "bad",
                "assistant_message": "hello",
                "next_question": "question?",
                "question_intent": "intent",
            }
        )


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, content: str):
        self._content = content

    def create(self, **kwargs):
        return _FakeResponse(self._content)


class _FakeChat:
    def __init__(self, content: str):
        self.completions = _FakeCompletions(content)


class _FakeClient:
    def __init__(self, content: str):
        self.chat = _FakeChat(content)


def test_call_ai_orchestrator_uses_concrete_fallback_without_client(monkeypatch):
    monkeypatch.setattr(incubator_orchestrator, "get_ai_client", lambda: None)

    result = call_ai_orchestrator("我想帮助独立开发者验证 SaaS 想法", "validate", {})

    assert result.thinking_mode == "validate"
    assert not is_generic_question(result.next_question)
    assert "独立开发者" in result.next_question or "验证" in result.next_question
    assert result.map_updates[0].operation.question == result.next_question


def test_call_ai_orchestrator_falls_back_on_invalid_ai_json(monkeypatch):
    monkeypatch.setattr(incubator_orchestrator, "get_ai_client", lambda: _FakeClient("not json"))
    monkeypatch.setattr(incubator_orchestrator, "get_model", lambda: "test-model")

    result = call_ai_orchestrator("用户想做 AI 日记", "clarify", {})

    assert result.thinking_mode == "clarify"
    assert not is_generic_question(result.next_question)
    assert result.map_updates[0].operation.title


def test_call_ai_orchestrator_rejects_generic_ai_question(monkeypatch):
    generic_payload = """
    {
      "thinking_mode": "clarify",
      "stage": "discover",
      "mode_reason": "test",
      "assistant_message": "还有什么需要补充？",
      "next_question": "还有什么需要补充？",
      "question_intent": "generic",
      "map_updates": [],
      "detected_gaps": [],
      "current_summary": {"facts": [], "open_questions": ["还有什么需要补充？"]}
    }
    """
    monkeypatch.setattr(incubator_orchestrator, "get_ai_client", lambda: _FakeClient(generic_payload))
    monkeypatch.setattr(incubator_orchestrator, "get_model", lambda: "test-model")

    result = call_ai_orchestrator("目标用户是独立开发者", "challenge", {})

    assert result.thinking_mode == "challenge"
    assert not is_generic_question(result.next_question)
    assert result.next_question != "还有什么需要补充？"


def test_call_ai_orchestrator_rejects_duplicate_map_questions(monkeypatch):
    duplicate_payload = """
    {
      "thinking_mode": "validate",
      "stage": "discover",
      "mode_reason": "test",
      "assistant_message": "先验证需求。",
      "next_question": "如何验证需求？",
      "question_intent": "validation",
      "map_updates": [
        {"operation": {"type": "create_node", "title": "验证", "kind": "question", "question": "目标用户是谁？"}, "risk": "low"},
        {"operation": {"type": "create_node", "title": "用户", "kind": "question", "question": "目标 用户 是 谁"}, "risk": "low"}
      ],
      "detected_gaps": [],
      "current_summary": {"facts": [], "open_questions": ["如何验证需求？"]}
    }
    """
    monkeypatch.setattr(incubator_orchestrator, "get_ai_client", lambda: _FakeClient(duplicate_payload))
    monkeypatch.setattr(incubator_orchestrator, "get_model", lambda: "test-model")

    result = call_ai_orchestrator("目标用户是独立开发者", "validate", {})

    assert result.thinking_mode == "validate"
    assert result.map_updates[0].operation.question == result.next_question
    assert "独立开发者" in result.next_question or "验证" in result.next_question
