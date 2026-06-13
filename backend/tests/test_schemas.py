import pytest
import warnings
from pydantic import ValidationError
from datetime import datetime

# Suppress warnings for clean test output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
from backend.schemas import (
    IssueCategory, IssueStatus, ActionPlan, ChatRequest, ChatResponse,
    IssueResponse, IssueCreateRequest, IssueCreateResponse, VoteRequest,
    VoteResponse, IssueStatusUpdateRequest, IssueStatusUpdateResponse,
    PushSubscriptionRequest, PushSubscriptionResponse, DetectionResponse,
    UrgencyAnalysisRequest, UrgencyAnalysisResponse, HealthResponse,
    MLStatusResponse, ResponsibilityMapResponse, ErrorResponse, SuccessResponse
)

def test_issue_category_enum():
    assert IssueCategory.ROAD == "Road"
    assert IssueCategory.WATER == "Water"
    assert IssueCategory.STREETLIGHT == "Streetlight"
    assert IssueCategory.GARBAGE == "Garbage"
    assert IssueCategory.COLLEGE_INFRA == "College Infra"
    assert IssueCategory.WOMEN_SAFETY == "Women Safety"

def test_issue_status_enum():
    assert IssueStatus.OPEN == "open"
    assert IssueStatus.VERIFIED == "verified"
    assert IssueStatus.ASSIGNED == "assigned"
    assert IssueStatus.IN_PROGRESS == "in_progress"
    assert IssueStatus.RESOLVED == "resolved"

def test_action_plan():
    plan = ActionPlan(whatsapp="Test message", email_subject="Subject", email_body="Body", x_post="Post")
    assert plan.whatsapp == "Test message"
    assert plan.email_subject == "Subject"
    assert plan.email_body == "Body"
    assert plan.x_post == "Post"

def test_chat_request():
    request = ChatRequest(query="Hello")
    assert request.query == "Hello"

    with pytest.raises(ValidationError):
        ChatRequest(query="")

    with pytest.raises(ValidationError):
        ChatRequest(query="   ")

def test_chat_response():
    response = ChatResponse(response="Hi there")
    assert response.response == "Hi there"

def test_issue_response():
    issue = IssueResponse(
        id=1, category="Road", description="Pothole", created_at=datetime.now(),
        status="open", upvotes=0
    )
    assert issue.id == 1
    assert issue.category == "Road"

def test_issue_create_request():
    request = IssueCreateRequest(
        description="Test issue", category=IssueCategory.ROAD,
        latitude=12.34, longitude=56.78
    )
    assert request.description == "Test issue"
    assert request.category == IssueCategory.ROAD

    with pytest.raises(ValidationError):
        IssueCreateRequest(description="", category=IssueCategory.ROAD)

def test_issue_create_response():
    response = IssueCreateResponse(id=1, message="Created")
    assert response.id == 1
    assert response.message == "Created"

def test_vote_request():
    request = VoteRequest(vote_type="up")
    assert request.vote_type == "up"

    with pytest.raises(ValidationError):
        VoteRequest(vote_type="invalid")

def test_vote_response():
    response = VoteResponse(id=1, upvotes=5, message="Voted")
    assert response.id == 1
    assert response.upvotes == 5

def test_issue_status_update_request():
    request = IssueStatusUpdateRequest(
        reference_id="ref123", status=IssueStatus.RESOLVED
    )
    assert request.reference_id == "ref123"
    assert request.status == IssueStatus.RESOLVED

def test_issue_status_update_response():
    response = IssueStatusUpdateResponse(
        id=1, reference_id="ref123", status=IssueStatus.RESOLVED, message="Updated"
    )
    assert response.id == 1
    assert response.status == IssueStatus.RESOLVED

def test_push_subscription_request():
    request = PushSubscriptionRequest(
        endpoint="https://example.com", p256dh="key", auth="secret"
    )
    assert request.endpoint == "https://example.com"

def test_push_subscription_response():
    response = PushSubscriptionResponse(id=1, message="Subscribed")
    assert response.id == 1

def test_detection_response():
    response = DetectionResponse(detections=[{"object": "car", "confidence": 0.9}])
    assert len(response.detections) == 1
    assert response.detections[0]["object"] == "car"

def test_urgency_analysis_request():
    request = UrgencyAnalysisRequest(
        description="Urgent issue", category=IssueCategory.ROAD
    )
    assert request.description == "Urgent issue"

def test_urgency_analysis_response():
    response = UrgencyAnalysisResponse(
        urgency_level="high", reasoning="Critical", recommended_actions=["Act now"]
    )
    assert response.urgency_level == "high"

def test_health_response():
    response = HealthResponse(status="healthy", timestamp=datetime.now())
    assert response.status == "healthy"

def test_ml_status_response():
    response = MLStatusResponse(status="loaded", models_loaded=["model1"])
    assert response.status == "loaded"

def test_responsibility_map_response():
    response = ResponsibilityMapResponse(data={"key": "value"})
    assert response.data["key"] == "value"

def test_error_response():
    response = ErrorResponse(error="Error", error_code="E001")
    assert response.error == "Error"

def test_success_response():
    response = SuccessResponse(message="Success")
    assert response.message == "Success"
