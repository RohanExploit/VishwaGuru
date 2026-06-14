"""
Grievance Service - Main Interface
Provides the main interface for grievance management and escalation.
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone, timedelta

from backend.models import Grievance, Jurisdiction, GrievanceStatus, SeverityLevel, Issue
from backend.database import SessionLocal
from backend.routing_service import RoutingService
from backend.sla_config_service import SLAConfigService
from backend.escalation_engine import EscalationEngine

class GrievanceService:
    """
    Main service for managing grievances, routing, and escalations.
    """

    def __init__(self, rules_config_path: str = "backend/grievance_rules.json"):
        """
        Initialize the grievance service.

        Args:
            rules_config_path: Path to the rules configuration file
        """
        with open(rules_config_path, 'r') as f:
            self.rules_config = json.load(f)

        self.routing_service = RoutingService(self.rules_config)
        self.sla_service = SLAConfigService(
            default_sla_hours=self.rules_config.get('sla_defaults', {}).get('default_hours', 48)
        )
        self.escalation_engine = EscalationEngine(
            self.routing_service,
            self.sla_service,
            self.rules_config
        )

    def create_grievance(self, grievance_data: Dict[str, Any], db: Session = None) -> Optional[Grievance]:
        """
        Create a new grievance with automatic routing and SLA assignment.

        Args:
            grievance_data: Dictionary containing grievance details
            db: Database session

        Returns:
            Created Grievance object or None if creation failed
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # Determine initial jurisdiction
            jurisdiction = self.routing_service.determine_initial_jurisdiction(grievance_data, db)
            if not jurisdiction:
                print("No suitable jurisdiction found for grievance")
                return None

            # Assign authority
            assigned_authority = self.routing_service.assign_authority(
                jurisdiction,
                grievance_data.get('category', 'general')
            )

            # Calculate SLA
            severity = SeverityLevel(grievance_data.get('severity', 'medium'))
            sla_hours = self.sla_service.get_sla_hours(
                severity=severity,
                jurisdiction_level=jurisdiction.level,
                department=grievance_data.get('category', 'general'),
                db=db
            )

            now = datetime.now(timezone.utc)
            sla_deadline = now + timedelta(hours=sla_hours)

            # Generate unique ID
            unique_id = str(uuid.uuid4())[:8].upper()

            # Extract location data
            location_data = grievance_data.get('location', {})
            latitude = location_data.get('latitude') if isinstance(location_data, dict) else None
            longitude = location_data.get('longitude') if isinstance(location_data, dict) else None
            address = location_data.get('address') if isinstance(location_data, dict) else None

            # Create grievance
            grievance = Grievance(
                unique_id=unique_id,
                category=grievance_data.get('category', 'general'),
                severity=severity,
                pincode=grievance_data.get('pincode'),
                city=grievance_data.get('city'),
                district=grievance_data.get('district'),
                state=grievance_data.get('state'),
                latitude=latitude,
                longitude=longitude,
                address=address,
                current_jurisdiction_id=jurisdiction.id,
                assigned_authority=assigned_authority,
                sla_deadline=sla_deadline,
                status=GrievanceStatus.OPEN,
                issue_id=grievance_data.get('issue_id')
            )

            db.add(grievance)
            db.commit()
            db.refresh(grievance)

            return grievance

        except Exception as e:
            db.rollback()
            print(f"Error creating grievance: {e}")
            return None
        finally:
            if should_close:
                db.close()

    def get_grievance(self, grievance_id: int, db: Session = None) -> Optional[Grievance]:
        """
        Get a grievance by ID.

        Args:
            grievance_id: Grievance ID
            db: Database session

        Returns:
            Grievance object or None
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            return db.query(Grievance).options(
                joinedload(Grievance.jurisdiction),
                joinedload(Grievance.audit_logs)
            ).filter(Grievance.id == grievance_id).first()

        finally:
            if should_close:
                db.close()

    def update_grievance_status(self, grievance_id: int, status: GrievanceStatus,
                               db: Session = None) -> bool:
        """
        Update the status of a grievance.

        Args:
            grievance_id: Grievance ID
            status: New status
            db: Database session

        Returns:
            True if update successful
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
            if not grievance:
                return False

            grievance.status = status
            grievance.updated_at = datetime.now(timezone.utc)

            if status == GrievanceStatus.RESOLVED:
                grievance.resolved_at = datetime.now(timezone.utc)

            # Sync with Issue if linked
            if grievance.issue_id:
                issue = db.query(Issue).filter(Issue.id == grievance.issue_id).first()
                if issue:
                    # Map GrievanceStatus to Issue status
                    status_map = {
                        GrievanceStatus.RESOLVED: "resolved",
                        GrievanceStatus.IN_PROGRESS: "in_progress",
                        GrievanceStatus.ESCALATED: "in_progress", # Escalated is internal, for user it's still in progress
                        GrievanceStatus.OPEN: "open"
                    }
                    new_issue_status = status_map.get(status)

                    if new_issue_status:
                        issue.status = new_issue_status
                        if new_issue_status == "resolved":
                            issue.resolved_at = datetime.now(timezone.utc)
                        elif new_issue_status == "in_progress":
                            # Maybe set assigned_at if not set?
                            if not issue.assigned_at:
                                issue.assigned_at = datetime.now(timezone.utc)
                                issue.assigned_to = grievance.assigned_authority

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"Error updating grievance status: {e}")
            return False
        finally:
            if should_close:
                db.close()

    def escalate_grievance_severity(self, grievance_id: int, new_severity: SeverityLevel,
                                   reason: str = "") -> bool:
        """
        Escalate grievance severity.

        Args:
            grievance_id: Grievance ID
            new_severity: New severity level
            reason: Reason for escalation

        Returns:
            True if escalation successful
        """
        return self.escalation_engine.escalate_grievance_severity(grievance_id, new_severity, reason)

    def manual_escalate(self, grievance_id: int, reason: str = "") -> bool:
        """
        Manually escalate a grievance.

        Args:
            grievance_id: Grievance ID
            reason: Reason for escalation

        Returns:
            True if escalation successful
        """
        return self.escalation_engine.manual_escalate(grievance_id, reason)

    def run_escalation_check(self) -> Dict[str, int]:
        """
        Run periodic escalation evaluation for all grievances.

        Returns:
            Dictionary with escalation statistics
        """
        return self.escalation_engine.evaluate_and_escalate_grievances()

    def get_grievance_audit_trail(self, grievance_id: int, db: Session = None) -> List[Dict[str, Any]]:
        """
        Get the complete audit trail for a grievance.

        Args:
            grievance_id: Grievance ID
            db: Database session

        Returns:
            List of audit entries
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
            if not grievance:
                return []

            audit_trail = []
            for audit in grievance.audit_logs:
                audit_trail.append({
                    "timestamp": audit.timestamp.isoformat(),
                    "previous_authority": audit.previous_authority,
                    "new_authority": audit.new_authority,
                    "reason": audit.reason.value,
                    "notes": audit.notes
                })

            return audit_trail

        finally:
            if should_close:
                db.close()

    def get_active_grievances_by_jurisdiction(self, jurisdiction_id: int, db: Session = None) -> List[Grievance]:
        """
        Get active grievances for a specific jurisdiction.

        Args:
            jurisdiction_id: Jurisdiction ID
            db: Database session

        Returns:
            List of active grievances
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            return db.query(Grievance).filter(
                and_(
                    Grievance.current_jurisdiction_id == jurisdiction_id,
                    Grievance.status.in_([GrievanceStatus.OPEN, GrievanceStatus.IN_PROGRESS, GrievanceStatus.ESCALATED])
                )
            ).all()

        finally:
            if should_close:
                db.close()