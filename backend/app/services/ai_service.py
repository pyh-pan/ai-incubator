from typing import Any

from openai import OpenAI

from app.core.config import settings

client: OpenAI | None = None


def get_client() -> OpenAI:
    """Create OpenAI client lazily so imports and tests do not require network config."""
    global client
    if client is None:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return client


# Framework templates
FRAMEWORK_TEMPLATES = {
    "product_manager": {
        "name": "产品经理框架",
        "branches": [
            {"id": "target_users", "label": "目标用户", "question": "谁是你的目标用户？"},
            {"id": "core_value", "label": "核心价值", "question": "这个工具的核心价值是什么？"},
            {"id": "pain_points", "label": "痛点问题", "question": "要解决的核心痛点是什么？"},
            {"id": "competitors", "label": "竞品分析", "question": "现有的竞品有哪些？"},
            {"id": "differentiation", "label": "差异化", "question": "你的差异化是什么？"},
            {"id": "feasibility", "label": "可行性", "question": "实现的可行性如何？"},
        ]
    },
    "business_canvas": {
        "name": "商业模式画布",
        "branches": [
            {"id": "value_proposition", "label": "价值主张", "question": "你的价值主张是什么？"},
            {"id": "customers", "label": "客户细分", "question": "目标客户群体有哪些？"},
            {"id": "channels", "label": "渠道通路", "question": "如何触达客户？"},
            {"id": "revenue", "label": "收入来源", "question": "如何赚钱？"},
            {"id": "resources", "label": "核心资源", "question": "需要哪些核心资源？"},
        ]
    },
    "technical_feasibility": {
        "name": "技术可行性分析",
        "branches": [
            {"id": "problem", "label": "问题定义", "question": "要解决的核心问题是什么？"},
            {"id": "solution", "label": "技术方案", "question": "技术实现方案是什么？"},
            {"id": "resources", "label": "资源需求", "question": "需要哪些技术资源？"},
            {"id": "risks", "label": "风险评估", "question": "技术风险有哪些？"},
            {"id": "roadmap", "label": "实施路径", "question": "实施的技术路线是什么？"},
        ]
    },
    "socratic": {
        "name": "苏格拉底式追问",
        "branches": []  # Dynamic generation
    }
}


class AIService:
    """AI service for question generation and text extraction."""

    @staticmethod
    def recommend_framework(idea: str) -> dict[str, Any]:
        """Recommend a framework based on the user's idea."""
        try:
            response = get_client().chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是AI Incubator的框架推荐助手。基于用户的想法，推荐最合适的思维框架。"
                    },
                    {
                        "role": "user",
                        "content": f"想法：{idea}\n\n请推荐一个框架（product_manager/business_canvas/technical_feasibility/socratic），并说明理由。"
                    }
                ],
                temperature=0.3,
                max_tokens=200,
            )
            content = response.choices[0].message.content.lower()

            # Parse response
            for framework in FRAMEWORK_TEMPLATES:
                if framework in content:
                    return {
                        "framework": framework,
                        "confidence": 0.8,
                        "reason": f"基于想法内容分析，推荐使用{FRAMEWORK_TEMPLATES[framework]['name']}"
                    }

            # Default fallback
            return {
                "framework": "product_manager",
                "confidence": 0.5,
                "reason": "默认推荐产品经理框架，适合大多数产品想法"
            }
        except Exception as e:
            # Fallback on error
            return {
                "framework": "product_manager",
                "confidence": 0.5,
                "reason": "AI服务暂不可用，使用默认框架"
            }

    @staticmethod
    def generate_question(framework: str, context: str, label: str = "") -> dict[str, Any]:
        """Generate a question based on framework and context."""
        # Use template-based generation for MVP
        if framework in FRAMEWORK_TEMPLATES and FRAMEWORK_TEMPLATES[framework].get("branches"):
            for branch in FRAMEWORK_TEMPLATES[framework]["branches"]:
                if branch["label"] == label:
                    return {
                        "question": branch["question"],
                        "context": f"这是{FRAMEWORK_TEMPLATES[framework]['name']}中的{label}维度。",
                        "examples": []
                    }

        # Fallback question
        return {
            "question": f"关于{label}，你有什么想法？",
            "context": "请详细描述你的想法。",
            "examples": []
        }

    @staticmethod
    def extract_points(answer: str) -> dict[str, Any]:
        """Extract key points from user's answer."""
        try:
            response = get_client().chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是AI Incubator的观点提炼助手。请提取用户回答中的核心观点，以要点列表形式组织。"
                    },
                    {
                        "role": "user",
                        "content": f"用户回答：{answer}\n\n请提炼核心观点（最多3-5个要点，每个不超过15字）："
                    }
                ],
                temperature=0.3,
                max_tokens=300,
            )
            content = response.choices[0].message.content

            # Parse bullet points
            points = [line.strip("-*•123456789. ").strip() for line in content.split("\n") if line.strip()]
            points = [p for p in points if len(p) > 0]

            return {
                "points": points[:5] if points else ["观点提取中..."],
                "summary": content[:100]
            }
        except Exception as e:
            return {
                "points": ["观点提取中..."],
                "summary": "AI服务暂不可用"
            }

    @staticmethod
    def generate_followup(parent_answer: str, label: str = "") -> dict[str, Any]:
        """Generate a follow-up question based on parent answer."""
        try:
            response = get_client().chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是AI Incubator的追问助手。基于用户的回答，生成一个帮助用户深入思考的追问。"
                    },
                    {
                        "role": "user",
                        "content": f"用户回答：{parent_answer}\n\n当前话题：{label}\n\n请生成一个追问（一个问题，让想法更清晰）："
                    }
                ],
                temperature=0.5,
                max_tokens=150,
            )
            content = response.choices[0].message.content

            return {
                "question": content,
                "context": "基于你的回答，我想深入了解...",
                "examples": []
            }
        except Exception as e:
            return {
                "question": f"关于{label}，还有哪些细节需要补充？",
                "context": "请继续深入思考。",
                "examples": []
            }
