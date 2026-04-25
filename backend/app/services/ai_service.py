from typing import Any

from openai import OpenAI

from app.core.config import settings


def _configured_api_key(provider: str) -> str:
    if provider == "glm":
        return settings.GLM_API_KEY
    return settings.OPENAI_API_KEY


def get_ai_client(provider: str | None = None) -> OpenAI | None:
    """Create an AI client only when the selected provider has credentials."""
    selected_provider = provider or settings.AI_PROVIDER
    api_key = _configured_api_key(selected_provider)
    if not api_key or api_key.startswith("your-"):
        return None

    if selected_provider == "glm":
        return OpenAI(
            api_key=api_key,
            base_url=settings.GLM_API_BASE,
            timeout=6.0,
            max_retries=0,
        )

    return OpenAI(api_key=api_key, timeout=6.0, max_retries=0)


def get_model(provider: str | None = None) -> str:
    """Return the configured model name for the selected provider."""
    selected_provider = provider or settings.AI_PROVIDER
    if selected_provider == "glm":
        return settings.GLM_MODEL
    return settings.OPENAI_MODEL


def get_client() -> OpenAI:
    """Compatibility wrapper for older call sites that expect a configured client."""
    client = get_ai_client()
    if client is None:
        raise RuntimeError("AI provider is not configured")
    return client


class AIService:
    """Legacy AI endpoints backed by the current general thinking direction."""

    @staticmethod
    def recommend_framework(idea: str) -> dict[str, Any]:
        """Return the single active framework for compatibility with old clients."""
        return {
            "framework": "general",
            "confidence": 1.0,
            "reason": "当前版本使用一个通用思考框架，优先保持项目简洁并围绕用户想法持续追问。",
        }

    @staticmethod
    def generate_question(framework: str, context: str, label: str = "") -> dict[str, Any]:
        """Generate a focused question with deterministic fallback."""
        topic = label.strip() or "这个想法"
        client = get_ai_client()
        if client is None:
            return {
                "question": f"关于{topic}，现在最需要澄清的一点是什么？",
                "context": "先明确一个关键不确定点，再继续扩展思路。",
                "examples": [],
            }

        try:
            response = client.chat.completions.create(
                model=get_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "你是 AI Incubator 的通用思考伙伴。只生成一个具体、可回答的问题，并给出简短背景。",
                    },
                    {
                        "role": "user",
                        "content": f"想法：{context}\n关注点：{topic}\n请生成一个追问。",
                    },
                ],
                temperature=0.4,
                max_tokens=300,
            )
            question = (response.choices[0].message.content or "").strip()
            return {
                "question": question or f"关于{topic}，现在最需要澄清的一点是什么？",
                "context": "这个问题用于帮助用户推进当前想法。",
                "examples": [],
            }
        except Exception:
            return {
                "question": f"关于{topic}，现在最需要澄清的一点是什么？",
                "context": "AI 服务暂不可用，已使用本地 fallback。",
                "examples": [],
            }

    @staticmethod
    def extract_points(answer: str) -> dict[str, Any]:
        """Extract key points from a user answer."""
        client = get_ai_client()
        if client is None:
            cleaned = answer.strip()
            point = cleaned[:60] if cleaned else "需要补充更多信息"
            return {"points": [point], "summary": cleaned[:100] if cleaned else point}

        try:
            response = client.chat.completions.create(
                model=get_model(),
                messages=[
                    {
                        "role": "system",
                        "content": "提取用户回答的核心要点，最多 3 条，每条不超过 20 字。",
                    },
                    {"role": "user", "content": answer},
                ],
                temperature=0.3,
                max_tokens=200,
            )
            content = response.choices[0].message.content or ""
            points = [line.strip("-*•123456789. ").strip() for line in content.split("\n") if line.strip()]
            return {"points": points[:3] or [answer[:60]], "summary": content[:100] or answer[:100]}
        except Exception:
            cleaned = answer.strip()
            point = cleaned[:60] if cleaned else "需要补充更多信息"
            return {"points": [point], "summary": cleaned[:100] if cleaned else point}

    @staticmethod
    def generate_followup(parent_answer: str, label: str = "") -> dict[str, Any]:
        """Generate a follow-up question using the generic question path."""
        return AIService.generate_question("general", parent_answer, label or "这个回答")
