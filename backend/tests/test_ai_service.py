import pytest

from app.services.ai_service import AIService


class TestFrameworkRecommendation:
    """Test framework recommendation."""

    def test_recommend_framework_product_idea(self):
        """Test recommending framework for product idea."""
        result = AIService.recommend_framework("I want to build a AI diary app")
        assert "framework" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1

    def test_recommend_framework_generic_idea(self):
        """Test recommending framework for generic idea."""
        result = AIService.recommend_framework("I have a new idea")
        assert "framework" in result
        assert result["framework"] == "general"


class TestQuestionGeneration:
    """Test question generation."""

    def test_generate_question_uses_generic_fallback(self):
        """Test generating a generic question without framework templates."""
        result = AIService.generate_question(
            framework="general",
            context="AI diary app",
            label="目标用户"
        )
        assert "question" in result
        assert "context" in result
        assert "目标用户" in result["question"]

    def test_generate_question_fallback(self):
        """Test fallback question generation."""
        result = AIService.generate_question(
            framework="unknown_framework",
            context="test",
            label="测试"
        )
        assert "question" in result
        assert "测试" in result["question"]


class TestPointExtraction:
    """Test key point extraction."""

    def test_extract_points_simple_answer(self):
        """Test extracting points from simple answer."""
        result = AIService.extract_points(
            "My target users are people who want to start journaling but find it difficult to maintain the habit."
        )
        assert "points" in result
        assert isinstance(result["points"], list)
        assert len(result["points"]) > 0

    def test_extract_points_short_answer(self):
        """Test extracting points from short answer."""
        result = AIService.extract_points("Yes")
        assert "points" in result
        assert isinstance(result["points"], list)


class TestFollowUpGeneration:
    """Test follow-up question generation."""

    def test_generate_followup(self):
        """Test generating follow-up question."""
        result = AIService.generate_followup(
            parent_answer="Users want emotional insights",
            label="情感分析"
        )
        assert "question" in result
        assert "context" in result
