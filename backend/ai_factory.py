"""
AI Service Factory for configuring different service implementations.

This module provides a factory pattern to easily switch between different
AI service implementations (Gemini, Mock, etc.) based on configuration.
"""
import os
from typing import Literal, Tuple
from ai_interfaces import (
    ActionPlanService, 
    ChatService, 
    MLASummaryService,
    DetectionService
)
from gemini_services import (
    create_gemini_action_plan_service,
    create_gemini_chat_service,
    create_gemini_mla_summary_service
)
from mock_services import (
    create_mock_action_plan_service,
    create_mock_chat_service,
    create_mock_mla_summary_service
)
from hf_detection_services import (
    create_hf_vandalism_detection_service,
    create_hf_infrastructure_detection_service,
    create_hf_flooding_detection_service,
    create_local_pothole_detection_service,
    create_local_garbage_detection_service
)
from mock_detection_services import (
    create_mock_vandalism_detection_service,
    create_mock_infrastructure_detection_service,
    create_mock_flooding_detection_service,
    create_mock_pothole_detection_service,
    create_mock_garbage_detection_service
)


ServiceType = Literal["gemini", "mock"]


def get_service_type() -> ServiceType:
    """
    Determine which service implementation to use based on environment variables.

    Returns:
        Service type: "gemini" for production, "mock" for testing
    """
    # Check for explicit service type override
    service_type = os.environ.get("AI_SERVICE_TYPE", "").lower()

    if service_type == "mock":
        return "mock"
    elif service_type == "gemini":
        return "gemini"
    else:
        # Default to Gemini for production, but allow mock for testing
        # You can set AI_SERVICE_TYPE=mock in environment for testing
        return "gemini"


def create_action_plan_service(service_type: ServiceType = None) -> ActionPlanService:
    """Create an action plan service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_action_plan_service()
    elif service_type == "gemini":
        return create_gemini_action_plan_service()
    else:
        raise ValueError(f"Unknown service type: {service_type}")


def create_chat_service(service_type: ServiceType = None) -> ChatService:
    """Create a chat service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_chat_service()
    elif service_type == "gemini":
        return create_gemini_chat_service()
    else:
        raise ValueError(f"Unknown service type: {service_type}")


def create_mla_summary_service(service_type: ServiceType = None) -> MLASummaryService:
    """Create an MLA summary service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_mla_summary_service()
    elif service_type == "gemini":
        return create_gemini_mla_summary_service()
    else:
        raise ValueError(f"Unknown service type: {service_type}")


def create_all_ai_services(service_type: ServiceType = None) -> Tuple[
    ActionPlanService, 
    ChatService, 
    MLASummaryService,
    DetectionService,
    DetectionService,
    DetectionService,
    DetectionService,
    DetectionService
]:
    """
    Create all AI services with the specified type.

    Returns:
        Tuple of all AI services: (action_plan, chat, mla_summary, 
                                   vandalism_detection, infrastructure_detection,
                                   flooding_detection, pothole_detection, garbage_detection)
    """
    if service_type is None:
        service_type = get_service_type()

    return (
        create_action_plan_service(service_type),
        create_chat_service(service_type),
        create_mla_summary_service(service_type),
        create_vandalism_detection_service(service_type),
        create_infrastructure_detection_service(service_type),
        create_flooding_detection_service(service_type),
        create_pothole_detection_service(service_type),
        create_garbage_detection_service(service_type)
    )


def create_vandalism_detection_service(service_type: ServiceType = None) -> DetectionService:
    """Create a vandalism detection service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_vandalism_detection_service()
    else:
        return create_hf_vandalism_detection_service()


def create_infrastructure_detection_service(service_type: ServiceType = None) -> DetectionService:
    """Create an infrastructure detection service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_infrastructure_detection_service()
    else:
        return create_hf_infrastructure_detection_service()


def create_flooding_detection_service(service_type: ServiceType = None) -> DetectionService:
    """Create a flooding detection service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_flooding_detection_service()
    else:
        return create_hf_flooding_detection_service()


def create_pothole_detection_service(service_type: ServiceType = None) -> DetectionService:
    """Create a pothole detection service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_pothole_detection_service()
    else:
        return create_local_pothole_detection_service()


def create_garbage_detection_service(service_type: ServiceType = None) -> DetectionService:
    """Create a garbage detection service based on the specified type."""
    if service_type is None:
        service_type = get_service_type()

    if service_type == "mock":
        return create_mock_garbage_detection_service()
    else:
        return create_local_garbage_detection_service()