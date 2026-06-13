"""
Concrete implementations of AI service interfaces using Hugging Face Text Generation.
Drop-in replacement for GeminiServices — uses Featherless AI via HF Router.
"""
from typing import Dict, Optional
from backend.ai_interfaces import ActionPlanService, ChatService, MLASummaryService
from backend.hf_text_service import (
    generate_civic_response,
    chat_with_hf_assistant,
    generate_mla_summary_hf,
)


class HFActionPlanService(ActionPlanService):
    """Hugging Face LLM-based implementation of action plan generation."""

    async def generate_action_plan(
        self,
        issue_description: str,
        category: str,
        language: str = "en",
        image_path: Optional[str] = None,
    ) -> Dict[str, str]:
        return await generate_civic_response(issue_description, category, language)


class HFChatService(ChatService):
    """Hugging Face LLM-based implementation of chat functionality."""

    async def chat(self, query: str) -> str:
        return await chat_with_hf_assistant(query)


class HFMLASummaryService(MLASummaryService):
    """Hugging Face LLM-based implementation of MLA summary generation."""

    async def generate_mla_summary(
        self,
        district: str,
        assembly_constituency: str,
        mla_name: str,
        issue_category: Optional[str] = None,
    ) -> str:
        return await generate_mla_summary_hf(
            district, assembly_constituency, mla_name, issue_category
        )


# Factory functions
def create_hf_action_plan_service() -> HFActionPlanService:
    return HFActionPlanService()


def create_hf_chat_service() -> HFChatService:
    return HFChatService()


def create_hf_mla_summary_service() -> HFMLASummaryService:
    return HFMLASummaryService()
