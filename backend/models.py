import json
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Enum, Index, Boolean
from sqlalchemy.types import TypeDecorator
from backend.database import Base
from sqlalchemy.orm import relationship

import datetime
import enum

class JSONEncodedDict(TypeDecorator):
    """Represents an immutable structure as a json-encoded string."""
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value

class JurisdictionLevel(enum.Enum):
    LOCAL = "local"
    DISTRICT = "district"
    STATE = "state"
    NATIONAL = "national"

class SeverityLevel(enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class GrievanceStatus(enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"

class EscalationReason(enum.Enum):
    SLA_BREACH = "sla_breach"
    SEVERITY_UPGRADE = "severity_upgrade"
    MANUAL = "manual"

class UserRole(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    OFFICIAL = "official"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))


class Jurisdiction(Base):
    __tablename__ = "jurisdictions"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(Enum(JurisdictionLevel), nullable=False, index=True)
    geographic_coverage = Column(JSONEncodedDict, nullable=False)  # e.g., {"states": ["Maharashtra"], "districts": ["Mumbai"]}
    responsible_authority = Column(String, nullable=False)  # Department or authority name
    default_sla_hours = Column(Integer, nullable=False)  # Default SLA in hours

    # Relationships
    grievances = relationship("Grievance", back_populates="jurisdiction")

class Grievance(Base):
    __tablename__ = "grievances"
    __table_args__ = (
        Index("ix_grievances_status_lat_lon", "status", "latitude", "longitude"),
        Index("ix_grievances_status_jurisdiction", "status", "current_jurisdiction_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    unique_id = Column(String, unique=True, index=True)  # Auto-generated unique identifier
    category = Column(String, nullable=False, index=True)  # Department category
    severity = Column(Enum(SeverityLevel), nullable=False, index=True)
    pincode = Column(String, nullable=True)
    city = Column(String, nullable=True)
    district = Column(String, nullable=True)
    state = Column(String, nullable=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    address = Column(String, nullable=True)
    current_jurisdiction_id = Column(Integer, ForeignKey("jurisdictions.id"), nullable=False)
    assigned_authority = Column(String, nullable=False, index=True)
    sla_deadline = Column(DateTime, nullable=False)
    status = Column(Enum(GrievanceStatus), default=GrievanceStatus.OPEN, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    resolved_at = Column(DateTime, nullable=True)
    
    # Closure confirmation fields
    closure_requested_at = Column(DateTime, nullable=True)
    closure_confirmation_deadline = Column(DateTime, nullable=True)
    closure_approved = Column(Boolean, default=False)
    pending_closure = Column(Boolean, default=False, index=True)
    
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=True, index=True)

    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="grievances")
    audit_logs = relationship("EscalationAudit", back_populates="grievance")
    followers = relationship("GrievanceFollower", back_populates="grievance")
    closure_confirmations = relationship("ClosureConfirmation", back_populates="grievance")
    resolution_evidence = relationship("ResolutionEvidence", back_populates="grievance")
    resolution_tokens = relationship("ResolutionProofToken", back_populates="grievance")

class SLAConfig(Base):
    __tablename__ = "sla_configs"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(Enum(SeverityLevel), nullable=False, index=True)
    jurisdiction_level = Column(Enum(JurisdictionLevel), nullable=False, index=True)
    department = Column(String, nullable=False, index=True)  # Category/department
    sla_hours = Column(Integer, nullable=False)

class EscalationAudit(Base):
    __tablename__ = "escalation_audits"

    id = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"), nullable=False)
    previous_authority = Column(String, nullable=False)
    new_authority = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    reason = Column(Enum(EscalationReason), nullable=False)
    notes = Column(Text, nullable=True)  # Additional context

    # Relationships
    grievance = relationship("Grievance", back_populates="audit_logs")

class Issue(Base):
    __tablename__ = "issues"
    __table_args__ = (
        Index("ix_issues_status_lat_lon", "status", "latitude", "longitude"),
    )

    id = Column(Integer, primary_key=True, index=True)
    reference_id = Column(String, unique=True, index=True)  # Secure reference for government updates
    description = Column(Text)
    category = Column(String, index=True)
    image_path = Column(String)
    source = Column(String)  # 'telegram', 'web', etc.
    status = Column(String, default="open", index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    verified_at = Column(DateTime, nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    user_email = Column(String, nullable=True, index=True)
    assigned_to = Column(String, nullable=True)  # Government official/department
    upvotes = Column(Integer, default=0, index=True)
    latitude = Column(Float, nullable=True, index=True)
    longitude = Column(Float, nullable=True, index=True)
    location = Column(String, nullable=True)
    action_plan = Column(JSONEncodedDict, nullable=True)
    integrity_hash = Column(String, nullable=True)  # Blockchain integrity seal
    
    # Voice and Language Support (Issue #291)
    submission_type = Column(String, default="text")  # 'text', 'voice'
    original_language = Column(String, nullable=True)  # Language code (e.g., 'hi', 'mr', 'en')
    original_text = Column(Text, nullable=True)  # Original text in regional language
    transcription_confidence = Column(Float, nullable=True)  # Confidence score for voice transcriptions
    manual_correction_applied = Column(Boolean, default=False)  # Flag for manual corrections
    audio_file_path = Column(String, nullable=True)  # Path to stored audio file

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=True, index=True)
    endpoint = Column(String, unique=True, index=True)
    p256dh = Column(String)
    auth = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    issue_id = Column(Integer, nullable=True)  # Optional: subscription for specific issue updates

class GrievanceFollower(Base):
    __tablename__ = "grievance_followers"
    __table_args__ = (
        Index("ix_follower_user_grievance", "user_email", "grievance_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"), nullable=False)
    user_email = Column(String, nullable=False, index=True)
    followed_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    grievance = relationship("Grievance", back_populates="followers")


class ClosureConfirmation(Base):
    __tablename__ = "closure_confirmations"

    id = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"), nullable=False)
    user_email = Column(String, nullable=False, index=True)
    confirmation_type = Column(String, nullable=False)  # 'confirmed', 'disputed'
    reason = Column(Text, nullable=True)  # Optional reason for dispute
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    
    # Relationship
    grievance = relationship("Grievance", back_populates="closure_confirmations")


class FieldOfficerVisit(Base):
    """
    Field Officer Check-In System (Issue #288)
    Tracks government officer visits to grievance sites with GPS verification
    """
    __tablename__ = "field_officer_visits"
    __table_args__ = (
        Index("ix_visits_issue_timestamp", "issue_id", "check_in_time"),
        Index("ix_visits_officer_timestamp", "officer_email", "check_in_time"),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Reference to issue/grievance
    issue_id = Column(Integer, ForeignKey("issues.id"), nullable=False, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"), nullable=True, index=True)
    
    # Officer details
    officer_email = Column(String, nullable=False, index=True)
    officer_name = Column(String, nullable=False)
    officer_department = Column(String, nullable=True)
    officer_designation = Column(String, nullable=True)
    
    # Check-in location data
    check_in_latitude = Column(Float, nullable=False)
    check_in_longitude = Column(Float, nullable=False)
    check_in_time = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False, index=True)
    
    # Geo-fencing verification
    distance_from_site = Column(Float, nullable=True)  # Distance in meters from reported issue location
    within_geofence = Column(Boolean, default=False, nullable=False)  # True if within acceptable radius
    geofence_radius_meters = Column(Float, default=100.0)  # Acceptable radius in meters
    
    # Visit details
    visit_notes = Column(Text, nullable=True)  # Officer's notes about the visit
    visit_images = Column(JSONEncodedDict, nullable=True)  # Paths to uploaded images
    visit_duration_minutes = Column(Integer, nullable=True)  # Estimated duration of visit
    
    # Check-out (optional)
    check_out_time = Column(DateTime, nullable=True)
    check_out_latitude = Column(Float, nullable=True)
    check_out_longitude = Column(Float, nullable=True)
    
    # Status and verification
    status = Column(String, default="checked_in", nullable=False)  # 'checked_in', 'checked_out', 'verified', 'disputed'
    verified_by = Column(String, nullable=True)  # Admin/supervisor who verified
    verified_at = Column(DateTime, nullable=True)
    
    # Immutability hash (blockchain-like integrity)
    visit_hash = Column(String, nullable=True)  # Hash of visit data for integrity verification
    
    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    is_public = Column(Boolean, default=True)  # Public visibility for transparency

class ResolutionEvidence(Base):
    __tablename__ = "resolution_evidence"
    id = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"), nullable=False)
    file_path = Column(String, nullable=False)
    media_type = Column(String, default="image")
    description = Column(Text, nullable=True)
    uploaded_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))

    # Relationship
    grievance = relationship("Grievance", back_populates="resolution_evidence")

class ResolutionProofToken(Base):
    __tablename__ = "resolution_proof_tokens"
    id = Column(Integer, primary_key=True, index=True)
    grievance_id = Column(Integer, ForeignKey("grievances.id"), nullable=False)
    token = Column(String, unique=True, index=True)
    generated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)

    # Relationship
    grievance = relationship("Grievance", back_populates="resolution_tokens")
