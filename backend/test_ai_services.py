"""
Test script to verify AI service dependency injection works correctly.
"""
import asyncio
import pytest
import os
import sys
from pathlib import Path

# Ensure repository root on sys.path so backend package resolves
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.ai_interfaces import initialize_ai_services, get_ai_services
from backend.mock_services import (
    create_mock_action_plan_service,
    create_mock_chat_service,
    create_mock_mla_summary_service
)


@pytest.mark.asyncio
async def test_ai_services():
    """Test that AI services can be initialized and used."""
    print("Testing AI service dependency injection...")

    # Test with mock services (safer for testing)
    print("\n1. Testing with mock services...")

    action_plan_service = create_mock_action_plan_service()
    chat_service = create_mock_chat_service()
    mla_summary_service = create_mock_mla_summary_service()

    initialize_ai_services(action_plan_service, chat_service, mla_summary_service)

    services = get_ai_services()

    # Test action plan generation
    action_plan = await services.action_plan_service.generate_action_plan(
        "Pothole on main road", "pothole"
    )
    print(f"Action plan keys: {list(action_plan.keys())}")
    assert "whatsapp" in action_plan
    assert "email_subject" in action_plan
    assert "email_body" in action_plan
    print("✓ Action plan service works")

    # Test chat service
    response = await services.chat_service.chat("Hello, how are you?")
    print(f"Chat response: {response[:50]}...")
    assert isinstance(response, str)
    assert len(response) > 0
    print("✓ Chat service works")

    # Test MLA summary service
    summary = await services.mla_summary_service.generate_mla_summary(
        "Mumbai", "Dadar", "John Doe"
    )
    print(f"MLA summary: {summary[:50]}...")
    assert isinstance(summary, str)
    assert len(summary) > 0
    print("✓ MLA summary service works")

    print("\n✅ All AI service dependency injection tests passed!")


if __name__ == "__main__":
    asyncio.run(test_ai_services())
