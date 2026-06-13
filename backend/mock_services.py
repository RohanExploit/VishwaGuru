"""
Mock implementations of AI service interfaces for testing and development.
"""
from typing import Dict, Optional
import asyncio

from backend.ai_interfaces import ActionPlanService, ChatService, MLASummaryService
from backend.ai_service import build_x_post

class MockActionPlanService(ActionPlanService):
    """Mock implementation that returns predefined responses."""

    async def generate_action_plan(
        self,
        issue_description: str,
        category: str,
        language: str = 'en',
        image_path: Optional[str] = None
    ) -> Dict[str, str]:
        # Simulate async operation
        await asyncio.sleep(0.1)
        return {
            "whatsapp": f"Mock: Report {category} issue - {issue_description[:50]}...",
            "email_subject": f"Mock: Complaint regarding {category}",
            "email_body": f"Mock: Respected Authority,\n\nI am writing to bring to your attention a {category} issue: {issue_description}.\n\nPlease take necessary action.\n\nSincerely,\nCitizen",
            "x_post": build_x_post(issue_description, category),
        }


class MockChatService(ChatService):
    """Mock implementation that returns predefined chat responses."""

    async def chat(self, query: str) -> str:
        # Simulate async operation
        await asyncio.sleep(0.1)
        return f"Mock response to: {query[:50]}... (This is a mock response for testing purposes)"


class MockMLASummaryService(MLASummaryService):
    """Mock implementation that returns predefined MLA summaries."""

    async def generate_mla_summary(
        self,
        district: str,
        assembly_constituency: str,
        mla_name: str,
        issue_category: Optional[str] = None
    ) -> str:
        # Simulate async operation
        await asyncio.sleep(0.1)
        category_text = f" specializing in {issue_category}" if issue_category else ""
        return (
            f"Mock: {mla_name} represents the {assembly_constituency} assembly constituency "
            f"in {district} district, Maharashtra{category_text}. MLAs handle local issues such as "
            f"infrastructure, public services, and constituent welfare."
        )


# Factory functions for easy service creation
def create_mock_action_plan_service() -> MockActionPlanService:
    """Create a mock action plan service for testing."""
    return MockActionPlanService()


def create_mock_chat_service() -> MockChatService:
    """Create a mock chat service for testing."""
    return MockChatService()


def create_mock_mla_summary_service() -> MockMLASummaryService:
    """Create a mock MLA summary service for testing."""
    return MockMLASummaryService()
