from fastapi import APIRouter

from app.schemas.node import (
    AIExtractRequest,
    AIExtractResponse,
    AIQuestionResponse,
    AIFrameworkRecommendation,
)
from app.services.ai_service import AIService

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/recommend-framework", response_model=AIFrameworkRecommendation)
def recommend_framework(data: dict[str, str]) -> dict:
    """Recommend a framework based on user's idea."""
    idea = data.get("idea", "")
    result = AIService.recommend_framework(idea)
    return result


@router.post("/generate-question", response_model=AIQuestionResponse)
def generate_question(data: dict[str, str]) -> dict:
    """Generate a question based on framework and context."""
    framework = data.get("framework", "product_manager")
    context = data.get("context", "")
    label = data.get("label", "")

    result = AIService.generate_question(framework, context, label)
    return result


@router.post("/extract-points", response_model=AIExtractResponse)
def extract_points(data: dict[str, str]) -> dict:
    """Extract key points from user's answer."""
    answer = data.get("answer", "")
    result = AIService.extract_points(answer)
    return result


@router.post("/followup/{node_id}", response_model=AIQuestionResponse)
def generate_followup(node_id: str, data: dict[str, str]) -> dict:
    """Generate a follow-up question."""
    parent_answer = data.get("parent_answer", "")
    label = data.get("label", "")

    result = AIService.generate_followup(parent_answer, label)
    return result
