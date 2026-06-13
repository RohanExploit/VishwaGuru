"""
AI Service Factory for configuring different service implementations.

This module provides a factory pattern to easily switch between different
AI service implementations (Gemini, Hugging Face, Mock) based on configuration.

Fallback chain:  gemini → huggingface → mock
"""
import os
from typing import Literal

from backend.ai_interfaces import ActionPlanService, ChatService, MLASummaryService
from backend.gemini_services import (
    create_gemini_action_plan_service,
    create_gemini_chat_service,
    create_gemini_mla_summary_service,
)
from backend.hf_text_services import (
    create_hf_action_plan_service,
    create_hf_chat_service,
    create_hf_mla_summary_service,
)
from backend.mock_services import (
    create_mock_action_plan_service,
    create_mock_chat_service,
    create_mock_mla_summary_service,
)

ServiceType = Literal["gemini", "huggingface", "mock"]


def get_service_type() -> ServiceType:
    """
    Determine which service implementation to use.

    Priority when AI_SERVICE_TYPE is not explicitly set:
        1. Gemini   – if GEMINI_API_KEY is present
        2. HuggingFace – if HF_TOKEN is present
        3. Mock     – always available
    """
    explicit = os.environ.get("AI_SERVICE_TYPE", "").lower()

    if explicit == "mock":
        return "mock"
    elif explicit == "huggingface":
        if not os.environ.get("HF_TOKEN"):
            print("⚠️ HF_TOKEN not found. Falling back to MOCK services.")
            return "mock"
        return "huggingface"
    elif explicit == "gemini":
        if not os.environ.get("GEMINI_API_KEY"):
            print("⚠️ GEMINI_API_KEY not found. Falling back to HUGGINGFACE services.")
            if os.environ.get("HF_TOKEN"):
                return "huggingface"
            print("⚠️ HF_TOKEN not found either. Falling back to MOCK services.")
            return "mock"
        return "gemini"
    else:
        # Auto-detect: gemini → huggingface → mock
        if os.environ.get("GEMINI_API_KEY"):
            return "gemini"
        if os.environ.get("HF_TOKEN"):
            print("ℹ️ GEMINI_API_KEY not found. Using HUGGINGFACE services.")
            return "huggingface"
        print("⚠️ No AI API keys found. Defaulting to MOCK services.")
        return "mock"


# ── Factory functions ────────────────────────────────────────────────────────

_FACTORIES = {
    "gemini": (
        create_gemini_action_plan_service,
        create_gemini_chat_service,
        create_gemini_mla_summary_service,
    ),
    "huggingface": (
        create_hf_action_plan_service,
        create_hf_chat_service,
        create_hf_mla_summary_service,
    ),
    "mock": (
        create_mock_action_plan_service,
        create_mock_chat_service,
        create_mock_mla_summary_service,
    ),
}


def create_action_plan_service(service_type: ServiceType = None) -> ActionPlanService:
    if service_type is None:
        service_type = get_service_type()
    return _FACTORIES[service_type][0]()


def create_chat_service(service_type: ServiceType = None) -> ChatService:
    if service_type is None:
        service_type = get_service_type()
    return _FACTORIES[service_type][1]()


def create_mla_summary_service(service_type: ServiceType = None) -> MLASummaryService:
    if service_type is None:
        service_type = get_service_type()
    return _FACTORIES[service_type][2]()


def create_all_ai_services(service_type: ServiceType = None):
    if service_type is None:
        service_type = get_service_type()
    print(f"🤖 AI Service Type: {service_type.upper()}")

    return (
        create_action_plan_service(service_type),
        create_chat_service(service_type),
        create_mla_summary_service(service_type),
    )
