"""
AI Service Interfaces and Dependency Injection

This module defines abstract interfaces for AI services to reduce tight coupling
and enable easier testing, mocking, and service provider switching.
"""
from abc import ABC, abstractmethod
from typing import Dict, Optional, Protocol
import asyncio


class ActionPlanService(Protocol):
    """Protocol for generating action plans (WhatsApp messages, emails) for civic issues."""

    async def generate_action_plan(
        self,
        issue_description: str,
        category: str,
        language: str = 'en',
        image_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Generate action plan with WhatsApp message and email draft.

        Args:
            issue_description: Description of the civic issue
            category: Category of the issue (pothole, garbage, etc.)
            image_path: Optional path to image evidence

        Returns:
            Dict with keys: 'whatsapp', 'email_subject', 'email_body'
        """
        ...


class ChatService(Protocol):
    """Protocol for conversational AI chat functionality."""

    async def chat(self, query: str) -> str:
        """
        Process a user query and return a response.

        Args:
            query: User's question or message

        Returns:
            AI-generated response
        """
        ...


class MLASummaryService(Protocol):
    """Protocol for generating MLA information summaries."""

    async def generate_mla_summary(
        self,
        district: str,
        assembly_constituency: str,
        mla_name: str,
        issue_category: Optional[str] = None
    ) -> str:
        """
        Generate a human-readable summary about an MLA.

        Args:
            district: District name
            assembly_constituency: Assembly constituency name
            mla_name: Name of the MLA
            issue_category: Optional issue category for context

        Returns:
            Human-readable summary text
        """
        ...


class AIServiceContainer:
    """Container for AI service dependencies using dependency injection."""

    def __init__(
        self,
        action_plan_service: ActionPlanService,
        chat_service: ChatService,
        mla_summary_service: MLASummaryService
    ):
        self.action_plan_service = action_plan_service
        self.chat_service = chat_service
        self.mla_summary_service = mla_summary_service


# Global service container instance
_ai_services: Optional[AIServiceContainer] = None


def get_ai_services() -> AIServiceContainer:
    """Get the global AI services container."""
    if _ai_services is None:
        raise RuntimeError("AI services not initialized. Call initialize_ai_services() first.")
    return _ai_services


def initialize_ai_services(
    action_plan_service: ActionPlanService,
    chat_service: ChatService,
    mla_summary_service: MLASummaryService
) -> None:
    """Initialize the global AI services container."""
    global _ai_services
    _ai_services = AIServiceContainer(
        action_plan_service=action_plan_service,
        chat_service=chat_service,
        mla_summary_service=mla_summary_service
    )
