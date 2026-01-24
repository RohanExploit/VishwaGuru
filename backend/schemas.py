from pydantic import BaseModel, Field, ConfigDict, validator, field_validator
from typing import List, Optional, Any, Dict, Union
from datetime import datetime
from enum import Enum

class IssueCategory(str, Enum):
    ROAD = "Road"
    WATER = "Water"
    STREETLIGHT = "Streetlight"
    GARBAGE = "Garbage"
    COLLEGE_INFRA = "College Infra"
    WOMEN_SAFETY = "Women Safety"

class IssueStatus(str, Enum):
    OPEN = "open"
    VERIFIED = "verified"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class ActionPlan(BaseModel):
    whatsapp: Optional[str] = Field(None, description="WhatsApp message template")
    email_subject: Optional[str] = Field(None, description="Email subject line")
    email_body: Optional[str] = Field(None, description="Email body content")
    x_post: Optional[str] = Field(None, description="X (Twitter) post content")

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="User's chat query")

    @field_validator('query')
    @classmethod
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty or whitespace only')
        return v.strip()

class ChatResponse(BaseModel):
    response: str = Field(..., description="AI assistant's response")

class IssueSummaryResponse(BaseModel):
    id: int = Field(..., description="Unique issue identifier")
    category: str = Field(..., description="Issue category")
    description: str = Field(..., description="Issue description")
    created_at: datetime = Field(..., description="Issue creation timestamp")
    image_path: Optional[str] = Field(None, description="Path to uploaded image")
    status: str = Field(..., description="Issue status")
    upvotes: int = Field(0, description="Number of upvotes")
    location: Optional[str] = Field(None, description="Location description")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    # action_plan excluded to optimize payload size

    model_config = ConfigDict(from_attributes=True)

class IssueResponse(IssueSummaryResponse):
    action_plan: Optional[Dict[str, Any]] = Field(None, description="Generated action plan")

class IssueCreateRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=1000, description="Issue description")
    category: IssueCategory = Field(..., description="Issue category")
    user_email: Optional[str] = Field(None, description="User's email address")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    location: Optional[str] = Field(None, max_length=200, description="Location description")

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty or whitespace only')
        return v.strip()

class IssueCreateResponse(BaseModel):
    id: int = Field(..., description="Created issue ID")
    message: str = Field(..., description="Success message")
    action_plan: Optional[ActionPlan] = Field(None, description="Generated action plan")

class VoteRequest(BaseModel):
    vote_type: str = Field(..., pattern="^(up|down)$", description="Vote type: 'up' or 'down'")

class VoteResponse(BaseModel):
    id: int = Field(..., description="Issue ID")
    upvotes: int = Field(..., description="Updated upvote count")
    message: str = Field(..., description="Vote confirmation message")

class IssueStatusUpdateRequest(BaseModel):
    reference_id: str = Field(..., description="Secure reference ID for the issue")
    status: IssueStatus = Field(..., description="New status for the issue")
    assigned_to: Optional[str] = Field(None, description="Government official/department assigned")
    notes: Optional[str] = Field(None, description="Additional notes from government")

class IssueStatusUpdateResponse(BaseModel):
    id: int = Field(..., description="Issue ID")
    reference_id: str = Field(..., description="Reference ID")
    status: IssueStatus = Field(..., description="Updated status")
    message: str = Field(..., description="Update confirmation message")

class PushSubscriptionRequest(BaseModel):
    user_email: Optional[str] = Field(None, description="User email for notifications")
    endpoint: str = Field(..., description="Push service endpoint")
    p256dh: str = Field(..., description="P-256 DH key")
    auth: str = Field(..., description="Authentication secret")
    issue_id: Optional[int] = Field(None, description="Specific issue to subscribe to")

class PushSubscriptionResponse(BaseModel):
    id: int = Field(..., description="Subscription ID")
    message: str = Field(..., description="Subscription confirmation")

class DetectionResponse(BaseModel):
    detections: List[Dict[str, Any]] = Field(..., description="List of detected objects/items")

class UrgencyAnalysisRequest(BaseModel):
    description: str = Field(..., min_length=10, max_length=1000, description="Issue description")
    category: IssueCategory = Field(..., description="Issue category")

class UrgencyAnalysisResponse(BaseModel):
    urgency_level: str = Field(..., pattern="^(low|medium|high|critical)$", description="Urgency level")
    reasoning: str = Field(..., description="Explanation for urgency assessment")
    recommended_actions: List[str] = Field(..., description="Recommended immediate actions")

class HealthResponse(BaseModel):
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$", description="Service health status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: Optional[str] = Field(None, description="API version")
    services: Optional[Dict[str, str]] = Field(None, description="Service status details")

class MLStatusResponse(BaseModel):
    status: str = Field(..., description="ML service status")
    models_loaded: List[str] = Field(..., description="List of loaded models")
    memory_usage: Optional[Dict[str, Any]] = Field(None, description="Memory usage statistics")

class ResponsibilityMapResponse(BaseModel):
    data: Dict[str, Any] = Field(..., description="Responsibility mapping data")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for client handling")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class SuccessResponse(BaseModel):
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
