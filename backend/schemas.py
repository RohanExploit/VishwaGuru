from pydantic import BaseModel, Field, ConfigDict, validator, field_validator
from typing import List, Optional, Any, Dict, Union
from datetime import datetime, timezone
from enum import Enum

class IssueCategory(str, Enum):
    ROAD = "Road"
    WATER = "Water"
    STREETLIGHT = "Streetlight"
    GARBAGE = "Garbage"
    COLLEGE_INFRA = "College Infra"
    WOMEN_SAFETY = "Women Safety"

class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"
    OFFICIAL = "official"

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
    relevant_government_rule: Optional[str] = Field(None, description="Relevant government policy or rule")

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Chat query text")

class ChatResponse(BaseModel):
    response: str

class GrievanceRequest(BaseModel):
    text: str

class IssueSummaryResponse(BaseModel):
    id: int
    category: str
    description: str
    created_at: datetime
    image_path: Optional[str] = None
    status: str
    upvotes: int
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

class IssueResponse(IssueSummaryResponse):
    action_plan: Optional[Union[Dict[str, Any], Any]] = Field(None, description="Generated action plan")

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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Error timestamp")

class SuccessResponse(BaseModel):
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Response timestamp")


class StatsResponse(BaseModel):
    total_issues: int = Field(..., description="Total number of issues reported")
    resolved_issues: int = Field(..., description="Number of resolved/verified issues")
    pending_issues: int = Field(..., description="Number of open/assigned/in_progress issues")
    issues_by_category: Dict[str, int] = Field(..., description="Count of issues by category")


class NearbyIssueResponse(BaseModel):
    id: int = Field(..., description="Issue ID")
    description: str = Field(..., description="Issue description")
    category: str = Field(..., description="Issue category")
    latitude: float = Field(..., description="Issue latitude")
    longitude: float = Field(..., description="Issue longitude")
    distance_meters: float = Field(..., description="Distance from new issue location")
    upvotes: int = Field(..., description="Number of upvotes")
    created_at: datetime = Field(..., description="Issue creation timestamp")
    status: str = Field(..., description="Issue status")


class DeduplicationCheckResponse(BaseModel):
    has_nearby_issues: bool = Field(..., description="Whether nearby issues were found")
    nearby_issues: List[NearbyIssueResponse] = Field(default_factory=list, description="List of nearby issues")
    recommended_action: str = Field(..., description="Recommended action: 'create_new', 'upvote_existing', 'verify_existing'")


class IssueCreateWithDeduplicationResponse(BaseModel):
    id: Optional[int] = Field(None, description="Created issue ID (None if deduplication occurred)")
    message: str = Field(..., description="Response message")
    action_plan: Optional[ActionPlan] = Field(None, description="Generated action plan")
    deduplication_info: DeduplicationCheckResponse = Field(..., description="Deduplication check results")
    linked_issue_id: Optional[int] = Field(None, description="ID of existing issue that was upvoted (if applicable)")


class LeaderboardEntry(BaseModel):
    user_email: str = Field(..., description="User email (masked)")
    reports_count: int = Field(..., description="Number of issues reported")
    total_upvotes: int = Field(..., description="Total upvotes received on reports")
    rank: int = Field(..., description="Rank on the leaderboard")

class LeaderboardResponse(BaseModel):
    leaderboard: List[LeaderboardEntry] = Field(..., description="List of top reporters")


# Escalation-related schemas
class EscalationAuditResponse(BaseModel):
    id: int = Field(..., description="Escalation audit record ID")
    grievance_id: int = Field(..., description="Associated grievance ID")
    previous_authority: str = Field(..., description="Previous authority handling the grievance")
    new_authority: str = Field(..., description="New authority after escalation")
    timestamp: datetime = Field(..., description="When the escalation occurred")
    reason: str = Field(..., description="Reason for escalation (SLA_BREACH, SEVERITY_UPGRADE, MANUAL)")

class GrievanceSummaryResponse(BaseModel):
    id: int = Field(..., description="Grievance ID")
    unique_id: str = Field(..., description="Unique grievance identifier")
    category: str = Field(..., description="Issue category")
    severity: str = Field(..., description="Severity level (LOW, MEDIUM, HIGH, CRITICAL)")
    pincode: Optional[str] = Field(None, description="Pincode")
    city: Optional[str] = Field(None, description="City")
    district: Optional[str] = Field(None, description="District")
    state: Optional[str] = Field(None, description="State")
    current_jurisdiction_id: int = Field(..., description="Current jurisdiction ID")
    assigned_authority: str = Field(..., description="Currently assigned authority")
    sla_deadline: datetime = Field(..., description="SLA deadline")
    status: str = Field(..., description="Current status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    escalation_history: List[EscalationAuditResponse] = Field(default_factory=list, description="Escalation history")

class EscalationStatsResponse(BaseModel):
    total_grievances: int = Field(..., description="Total number of grievances")
    escalated_grievances: int = Field(..., description="Number of escalated grievances")
    active_grievances: int = Field(..., description="Number of active grievances")
    resolved_grievances: int = Field(..., description="Number of resolved grievances")
    escalation_rate: float = Field(..., description="Percentage of grievances that were escalated")

# Community Confirmation Schemas (Issue #289)

class FollowGrievanceRequest(BaseModel):
    user_email: str = Field(..., description="Email of the user following the grievance")


class FollowGrievanceResponse(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID")
    user_email: str = Field(..., description="User email")
    message: str = Field(..., description="Success message")
    total_followers: int = Field(..., description="Total number of followers")


class RequestClosureRequest(BaseModel):
    admin_notes: Optional[str] = Field(None, description="Optional notes from admin")


class RequestClosureResponse(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID")
    message: str = Field(..., description="Status message")
    confirmation_deadline: datetime = Field(..., description="Deadline for community confirmation")
    total_followers: int = Field(..., description="Number of followers who will be notified")
    required_confirmations: int = Field(..., description="Number of confirmations needed")


class ConfirmClosureRequest(BaseModel):
    user_email: str = Field(..., description="Email of the user confirming")
    confirmation_type: str = Field(..., pattern="^(confirmed|disputed)$", description="Type: 'confirmed' or 'disputed'")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for dispute (optional)")


class ConfirmClosureResponse(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID")
    message: str = Field(..., description="Confirmation message")
    current_confirmations: int = Field(..., description="Current number of confirmations")
    required_confirmations: int = Field(..., description="Required confirmations")
    current_disputes: int = Field(..., description="Current number of disputes")
    closure_approved: bool = Field(..., description="Whether closure has been approved")


class ClosureStatusResponse(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID")
    pending_closure: bool = Field(..., description="Whether closure is pending confirmation")
    closure_approved: bool = Field(..., description="Whether closure has been approved")
    total_followers: int = Field(..., description="Total number of followers")
    confirmations_count: int = Field(..., description="Number of confirmations received")
    disputes_count: int = Field(..., description="Number of disputes received")
    required_confirmations: int = Field(..., description="Number of confirmations needed")
    confirmation_deadline: Optional[datetime] = Field(None, description="Deadline for confirmations")
    days_remaining: Optional[int] = Field(None, description="Days until deadline")

class BlockchainVerificationResponse(BaseModel):
    is_valid: bool = Field(..., description="Whether the issue integrity is intact")
    current_hash: Optional[str] = Field(None, description="Current integrity hash stored in DB")
    computed_hash: str = Field(..., description="Hash computed from current issue data and previous issue's hash")
    message: str = Field(..., description="Verification result message")


# Resolution Proof Schemas (Issue #292)

class GenerateRPTRequest(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID to generate token for")
    authority_email: str = Field(..., description="Email of the authority resolving the grievance")
    geofence_radius_meters: Optional[float] = Field(200.0, ge=50, le=1000, description="Geofence radius in meters")


class RPTResponse(BaseModel):
    token_id: str = Field(..., description="Unique token identifier")
    grievance_id: int = Field(..., description="Associated grievance ID")
    geofence_latitude: float = Field(..., description="Geofence center latitude")
    geofence_longitude: float = Field(..., description="Geofence center longitude")
    geofence_radius_meters: float = Field(..., description="Geofence radius in meters")
    valid_from: datetime = Field(..., description="Token validity start time")
    valid_until: datetime = Field(..., description="Token expiry time")
    token_signature: str = Field(..., description="Cryptographic signature of the token")
    message: str = Field(..., description="Status message")


class SubmitEvidenceRequest(BaseModel):
    token_id: str = Field(..., description="Resolution proof token ID")
    evidence_hash: str = Field(..., min_length=64, max_length=64, description="SHA-256 hash of the evidence media file")
    gps_latitude: float = Field(..., ge=-90, le=90, description="GPS latitude of capture location")
    gps_longitude: float = Field(..., ge=-180, le=180, description="GPS longitude of capture location")
    capture_timestamp: datetime = Field(..., description="Timestamp when evidence was captured")
    device_fingerprint_hash: Optional[str] = Field(None, description="Hash of device fingerprint")


class EvidenceResponse(BaseModel):
    id: int = Field(..., description="Evidence record ID")
    grievance_id: int = Field(..., description="Associated grievance ID")
    evidence_hash: str = Field(..., description="SHA-256 hash of the evidence")
    gps_latitude: float = Field(..., description="Capture GPS latitude")
    gps_longitude: float = Field(..., description="Capture GPS longitude")
    capture_timestamp: datetime = Field(..., description="When evidence was captured")
    verification_status: str = Field(..., description="Verification status: pending, verified, flagged, fraud_detected")
    server_signature: str = Field(..., description="Server cryptographic signature")
    created_at: datetime = Field(..., description="Record creation timestamp")
    message: str = Field(..., description="Status message")


class VerificationResponse(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID")
    is_verified: bool = Field(..., description="Whether the resolution is cryptographically verified")
    verification_status: str = Field(..., description="Status: pending, verified, flagged, fraud_detected")
    resolution_timestamp: Optional[datetime] = Field(None, description="When the grievance was resolved")
    location_match: bool = Field(..., description="Whether evidence GPS matches grievance geofence")
    evidence_integrity: bool = Field(..., description="Whether evidence hash is intact")
    evidence_hash: Optional[str] = Field(None, description="SHA-256 hash fingerprint for transparency")
    evidence_count: int = Field(0, description="Number of evidence records")
    message: str = Field(..., description="Human-readable verification summary")


class EvidenceAuditLogResponse(BaseModel):
    id: int = Field(..., description="Audit log entry ID")
    evidence_id: int = Field(..., description="Associated evidence ID")
    action: str = Field(..., description="Action: created, verified, flagged, fraud_detected")
    details: Optional[str] = Field(None, description="Additional details")
    actor_email: Optional[str] = Field(None, description="Actor who triggered the action")
    timestamp: datetime = Field(..., description="When the action occurred")


class AuditTrailResponse(BaseModel):
    grievance_id: int = Field(..., description="Grievance ID")
    audit_entries: List[EvidenceAuditLogResponse] = Field(default_factory=list, description="Audit trail entries")
    total_entries: int = Field(0, description="Total number of audit entries")


class DuplicateCheckResponse(BaseModel):
    is_duplicate: bool = Field(..., description="Whether the evidence hash is a duplicate")
    duplicate_grievance_ids: List[int] = Field(default_factory=list, description="Grievance IDs with matching hash")
    message: str = Field(..., description="Duplicate check result message")

# Auth Schemas
class UserBase(BaseModel):
    email: str = Field(..., description="User email")
    full_name: Optional[str] = Field(None, description="User full name")

class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="User password")

class UserLogin(BaseModel):
    email: str = Field(..., description="User email")
    password: str = Field(..., description="User password")

class UserResponse(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None

# Voice and Language Support Schemas (Issue #291)

class VoiceTranscriptionRequest(BaseModel):
    """Request model for voice transcription"""
    preferred_language: Optional[str] = Field(
        'auto', 
        description="Preferred language code for transcription (e.g., 'hi', 'mr', 'auto')"
    )

class VoiceTranscriptionResponse(BaseModel):
    """Response model for voice transcription"""
    original_text: Optional[str] = Field(None, description="Transcribed text in original language")
    translated_text: Optional[str] = Field(None, description="Translated text (English)")
    source_language: Optional[str] = Field(None, description="Detected language code")
    source_language_name: Optional[str] = Field(None, description="Detected language name")
    confidence: float = Field(..., description="Transcription confidence score (0-1)")
    manual_correction_needed: bool = Field(..., description="Flag indicating if manual correction is needed")
    error: Optional[str] = Field(None, description="Error message if transcription failed")

class TextTranslationRequest(BaseModel):
    """Request model for text translation"""
    text: str = Field(..., min_length=1, max_length=2000, description="Text to translate")
    source_language: str = Field('auto', description="Source language code ('auto' for detection)")
    target_language: str = Field('en', description="Target language code")

class TextTranslationResponse(BaseModel):
    """Response model for text translation"""
    translated_text: Optional[str] = Field(None, description="Translated text")
    source_language: Optional[str] = Field(None, description="Detected source language")
    source_language_name: Optional[str] = Field(None, description="Source language name")
    target_language: Optional[str] = Field(None, description="Target language")
    target_language_name: Optional[str] = Field(None, description="Target language name")
    original_text: str = Field(..., description="Original text")
    error: Optional[str] = Field(None, description="Error message if translation failed")

class VoiceIssueCreateRequest(BaseModel):
    """Extended issue creation request with voice/language support"""
    description: Optional[str] = Field(None, description="Issue description (for manual corrections)")
    category: IssueCategory = Field(..., description="Issue category")
    user_email: Optional[str] = Field(None, description="User's email address")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude coordinate")
    location: Optional[str] = Field(None, max_length=200, description="Location description")
    
    # Voice/Language specific fields
    submission_type: str = Field('text', pattern="^(text|voice)$", description="Submission type")
    original_language: Optional[str] = Field(None, description="Original language code")
    original_text: Optional[str] = Field(None, description="Original text in regional language")
    transcription_confidence: Optional[float] = Field(None, ge=0, le=1, description="Confidence score")

class SupportedLanguagesResponse(BaseModel):
    """Response model for supported languages"""
    languages: Dict[str, str] = Field(..., description="Dictionary of language code to language name")
    total_count: int = Field(..., description="Total number of supported languages")

# Field Officer Check-In System Schemas (Issue #288)

class OfficerCheckInRequest(BaseModel):
    """Request model for field officer check-in"""
    issue_id: int = Field(..., description="ID of the issue being visited")
    grievance_id: Optional[int] = Field(None, description="Optional grievance ID if linked")
    officer_email: str = Field(..., description="Officer's email address")
    officer_name: str = Field(..., min_length=2, max_length=100, description="Officer's full name")
    officer_department: Optional[str] = Field(None, max_length=100, description="Department name")
    officer_designation: Optional[str] = Field(None, max_length=100, description="Officer's designation")
    check_in_latitude: float = Field(..., ge=-90, le=90, description="Check-in GPS latitude")
    check_in_longitude: float = Field(..., ge=-180, le=180, description="Check-in GPS longitude")
    visit_notes: Optional[str] = Field(None, max_length=1000, description="Visit notes/observations")
    geofence_radius_meters: Optional[float] = Field(100.0, ge=10, le=1000, description="Acceptable distance from site (meters)")

class OfficerCheckOutRequest(BaseModel):
    """Request model for field officer check-out"""
    visit_id: int = Field(..., description="ID of the visit to check out from")
    check_out_latitude: float = Field(..., ge=-90, le=90, description="Check-out GPS latitude")
    check_out_longitude: float = Field(..., ge=-180, le=180, description="Check-out GPS longitude")
    visit_duration_minutes: Optional[int] = Field(None, ge=0, le=1440, description="Visit duration in minutes")
    additional_notes: Optional[str] = Field(None, max_length=1000, description="Additional notes at check-out")

class VisitImageUploadResponse(BaseModel):
    """Response for visit image upload"""
    visit_id: int = Field(..., description="Visit ID")
    image_paths: List[str] = Field(..., description="Paths to uploaded images")
    message: str = Field(..., description="Success message")

class FieldOfficerVisitResponse(BaseModel):
    """Response model for field officer visit (authenticated users)"""
    id: int = Field(..., description="Visit ID")
    issue_id: int = Field(..., description="Issue ID")
    grievance_id: Optional[int] = Field(None, description="Grievance ID")
    officer_email: str = Field(..., description="Officer email")
    officer_name: str = Field(..., description="Officer name")
    officer_department: Optional[str] = Field(None, description="Department")
    officer_designation: Optional[str] = Field(None, description="Designation")
    check_in_latitude: float = Field(..., description="Check-in latitude")
    check_in_longitude: float = Field(..., description="Check-in longitude")
    check_in_time: datetime = Field(..., description="Check-in timestamp")
    check_out_time: Optional[datetime] = Field(None, description="Check-out timestamp")
    distance_from_site: Optional[float] = Field(None, description="Distance from site in meters")
    within_geofence: bool = Field(..., description="Whether check-in was within geofence")
    visit_notes: Optional[str] = Field(None, description="Visit notes")
    visit_images: Optional[List[str]] = Field(None, description="Visit image paths")
    visit_duration_minutes: Optional[int] = Field(None, description="Visit duration")
    status: str = Field(..., description="Visit status")
    verified_by: Optional[str] = Field(None, description="Verified by")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    is_public: bool = Field(..., description="Public visibility")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class PublicFieldOfficerVisitResponse(BaseModel):
    """Public response model for field officer visit (PII removed - no officer_email)"""
    id: int = Field(..., description="Visit ID")
    issue_id: int = Field(..., description="Issue ID")
    grievance_id: Optional[int] = Field(None, description="Grievance ID")
    officer_name: str = Field(..., description="Officer name")
    officer_department: Optional[str] = Field(None, description="Department")
    officer_designation: Optional[str] = Field(None, description="Designation")
    check_in_latitude: float = Field(..., description="Check-in latitude")
    check_in_longitude: float = Field(..., description="Check-in longitude")
    check_in_time: datetime = Field(..., description="Check-in timestamp")
    check_out_time: Optional[datetime] = Field(None, description="Check-out timestamp")
    distance_from_site: Optional[float] = Field(None, description="Distance from site in meters")
    within_geofence: bool = Field(..., description="Whether check-in was within geofence")
    visit_notes: Optional[str] = Field(None, description="Visit notes")
    visit_images: Optional[List[str]] = Field(None, description="Visit image paths")
    visit_duration_minutes: Optional[int] = Field(None, description="Visit duration")
    status: str = Field(..., description="Visit status")
    verified_by: Optional[str] = Field(None, description="Verified by")
    verified_at: Optional[datetime] = Field(None, description="Verification timestamp")
    is_public: bool = Field(..., description="Public visibility")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class VisitHistoryResponse(BaseModel):
    """Response for visit history of an issue"""
    issue_id: int = Field(..., description="Issue ID")
    total_visits: int = Field(..., description="Total number of visits")
    visits: List[PublicFieldOfficerVisitResponse] = Field(..., description="List of visits (PII removed for public access)")


class VisitStatsResponse(BaseModel):
    """Response for visit statistics"""
    total_visits: int = Field(..., description="Total visits")
    verified_visits: int = Field(..., description="Verified visits")
    within_geofence_count: int = Field(..., description="Visits within geofence")
    outside_geofence_count: int = Field(..., description="Visits outside geofence")
    unique_officers: int = Field(..., description="Number of unique officers")
    average_distance_from_site: Optional[float] = Field(None, description="Average distance in meters")
