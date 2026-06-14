import json
from sqlalchemy import Column, Integer, String, DateTime, Float, Text, ForeignKey, Enum, Index
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
    assigned_authority = Column(String, nullable=False)
    sla_deadline = Column(DateTime, nullable=False)
    status = Column(Enum(GrievanceStatus), default=GrievanceStatus.OPEN, index=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True)
    updated_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), onupdate=lambda: datetime.datetime.now(datetime.timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    jurisdiction = relationship("Jurisdiction", back_populates="grievances")
    audit_logs = relationship("EscalationAudit", back_populates="grievance")

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
    description = Column(String)
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

class PushSubscription(Base):
    __tablename__ = "push_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=True, index=True)
    endpoint = Column(String, unique=True, index=True)
    p256dh = Column(String)
    auth = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    issue_id = Column(Integer, nullable=True)  # Optional: subscription for specific issue updates
