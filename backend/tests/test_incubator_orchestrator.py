import pytest
from pydantic import ValidationError

from app.schemas.v2 import AIOrchestratorOutput


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
