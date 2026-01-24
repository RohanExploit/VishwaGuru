"""
Concrete implementations of AI service interfaces using Gemini AI.
"""
from typing import Dict, Optional
import asyncio
from backend.ai_interfaces import ActionPlanService, ChatService, MLASummaryService
from backend.ai_service import (
    generate_action_plan as _generate_action_plan,
    chat_with_civic_assistant as _chat_with_civic_assistant
)
from backend.gemini_summary import generate_mla_summary as _generate_mla_summary


class GeminiActionPlanService(ActionPlanService):
    """Gemini-based implementation of action plan generation."""

    async def generate_action_plan(
        self,
        issue_description: str,
        category: str,
        language: str = 'en',
        image_path: Optional[str] = None
    ) -> Dict[str, str]:
        return await _generate_action_plan(issue_description, category, language, image_path)


class GeminiChatService(ChatService):
    """Gemini-based implementation of chat functionality."""

    async def chat(self, query: str) -> str:
        return await _chat_with_civic_assistant(query)


class GeminiMLASummaryService(MLASummaryService):
    """Gemini-based implementation of MLA summary generation."""

    async def generate_mla_summary(
        self,
        district: str,
        assembly_constituency: str,
        mla_name: str,
        issue_category: Optional[str] = None
    ) -> str:
        return await _generate_mla_summary(district, assembly_constituency, mla_name, issue_category)


# Factory functions for easy service creation
def create_gemini_action_plan_service() -> GeminiActionPlanService:
    """Create a Gemini-based action plan service."""
    return GeminiActionPlanService()


def create_gemini_chat_service() -> GeminiChatService:
    """Create a Gemini-based chat service."""
    return GeminiChatService()


def create_gemini_mla_summary_service() -> GeminiMLASummaryService:
    """Create a Gemini-based MLA summary service."""
    return GeminiMLASummaryService()

# Global service instance
_ai_services = None

class AIServices:
    def __init__(self, action_plan_service, chat_service, mla_summary_service):
        self.action_plan_service = action_plan_service
        self.chat_service = chat_service
        self.mla_summary_service = mla_summary_service

def initialize_ai_services(action_plan_service, chat_service, mla_summary_service):
    global _ai_services
    _ai_services = AIServices(action_plan_service, chat_service, mla_summary_service)

def get_ai_services():
    return _ai_services
