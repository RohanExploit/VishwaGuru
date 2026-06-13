"""
Grievance Escalation Engine
Core engine for evaluating and performing grievance escalations based on SLA and rules.
"""

import datetime
import hashlib
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from backend.models import Grievance, Jurisdiction, EscalationAudit, GrievanceStatus, JurisdictionLevel, EscalationReason, SeverityLevel
from backend.database import SessionLocal
from backend.cache import audit_last_hash_cache
from backend.config import get_config
from backend.routing_service import RoutingService
from backend.sla_config_service import SLAConfigService
from backend.cache import audit_last_hash_cache

class EscalationEngine:
    """
    Engine for handling grievance escalations based on SLA breaches and severity changes.
    """

    def __init__(self, routing_service: RoutingService, sla_service: SLAConfigService,
                 rules_config: Dict[str, Any]):
        """
        Initialize the escalation engine.

        Args:
            routing_service: RoutingService instance
            sla_service: SLAConfigService instance
            rules_config: Configuration dictionary for escalation rules
        """
        self.routing_service = routing_service
        self.sla_service = sla_service
        self.rules_config = rules_config

    def evaluate_and_escalate_grievances(self, db: Session = None) -> Dict[str, int]:
        """
        Evaluate all active grievances for escalation needs and perform escalations.

        Args:
            db: Database session

        Returns:
            Dictionary with escalation statistics
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            # Get grievances that need evaluation
            grievances_to_evaluate = self._get_grievances_for_evaluation(db)

            escalated_count = 0
            evaluated_count = len(grievances_to_evaluate)

            for grievance in grievances_to_evaluate:
                if self._should_escalate(grievance, db):
                    success = self._escalate_grievance(grievance, EscalationReason.SLA_BREACH, db)
                    if success:
                        escalated_count += 1

            return {
                "evaluated": evaluated_count,
                "escalated": escalated_count
            }

        finally:
            if should_close:
                db.close()

    def escalate_grievance_severity(self, grievance_id: int, new_severity: SeverityLevel,
                                   reason: str = "", db: Session = None) -> bool:
        """
        Escalate a grievance due to severity upgrade.

        Args:
            grievance_id: Grievance ID
            new_severity: New severity level
            reason: Reason for escalation
            db: Database session

        Returns:
            True if escalation successful
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
            if not grievance:
                return False

            # Update severity
            old_severity = grievance.severity
            grievance.severity = new_severity
            grievance.updated_at = datetime.datetime.now(datetime.timezone.utc)

            # Recalculate SLA
            self._recalculate_sla(grievance, db)

            # Check if escalation to higher jurisdiction is needed
            if self._should_escalate_due_to_severity(grievance, old_severity, db):
                return self._escalate_grievance(grievance, EscalationReason.SEVERITY_UPGRADE, db, reason)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"Error escalating grievance severity: {e}")
            return False
        finally:
            if should_close:
                db.close()

    def manual_escalate(self, grievance_id: int, reason: str = "", db: Session = None) -> bool:
        """
        Manually escalate a grievance.

        Args:
            grievance_id: Grievance ID
            reason: Reason for manual escalation
            db: Database session

        Returns:
            True if escalation successful
        """
        should_close = False
        if db is None:
            db = SessionLocal()
            should_close = True

        try:
            grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
            if not grievance:
                return False

            return self._escalate_grievance(grievance, EscalationReason.MANUAL, db, reason)

        finally:
            if should_close:
                db.close()

    def _get_grievances_for_evaluation(self, db: Session) -> List[Grievance]:
        """
        Get grievances that should be evaluated for escalation.

        Args:
            db: Database session

        Returns:
            List of grievances to evaluate
        """
        now = datetime.datetime.now(datetime.timezone.utc)

        # Get grievances that are active and past SLA deadline
        return db.query(Grievance).filter(
            and_(
                Grievance.status.in_([GrievanceStatus.OPEN, GrievanceStatus.IN_PROGRESS, GrievanceStatus.ESCALATED]),
                Grievance.sla_deadline < now
            )
        ).all()

    def _should_escalate(self, grievance: Grievance, db: Session) -> bool:
        """
        Determine if a grievance should be escalated.

        Args:
            grievance: Grievance object
            db: Database session

        Returns:
            True if escalation is needed
        """
        # Check if SLA is breached
        now = datetime.datetime.now(datetime.timezone.utc)

        # Handle naive datetimes from SQLite
        deadline = grievance.sla_deadline
        if deadline and deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=datetime.timezone.utc)

        if deadline >= now:
            return False

        # Check if escalation is possible
        return self.routing_service.can_escalate(grievance.jurisdiction.level)

    def _should_escalate_due_to_severity(self, grievance: Grievance, old_severity: SeverityLevel, db: Session) -> bool:
        """
        Check if severity change requires jurisdiction escalation.

        Args:
            grievance: Grievance object
            old_severity: Previous severity level
            db: Database session

        Returns:
            True if jurisdiction escalation needed
        """
        severity_hierarchy = {
            SeverityLevel.LOW: 1,
            SeverityLevel.MEDIUM: 2,
            SeverityLevel.HIGH: 3,
            SeverityLevel.CRITICAL: 4
        }

        old_level = severity_hierarchy.get(old_severity, 1)
        new_level = severity_hierarchy.get(grievance.severity, 1)

        # If severity increased significantly, consider escalation
        if new_level - old_level >= 2:  # e.g., LOW to CRITICAL
            return self.routing_service.can_escalate(grievance.jurisdiction.level)

        return False

    def _escalate_grievance(self, grievance: Grievance, reason: EscalationReason,
                           db: Session, notes: str = "") -> bool:
        """
        Perform the actual escalation of a grievance.

        Args:
            grievance: Grievance object
            reason: Reason for escalation
            db: Database session
            notes: Additional notes

        Returns:
            True if escalation successful
        """
        try:
            # Get next jurisdiction level
            next_level = self.routing_service.get_next_jurisdiction_level(grievance.jurisdiction.level)
            if not next_level:
                return False  # Cannot escalate beyond national level

            # Find new jurisdiction
            new_jurisdiction = self.routing_service._find_jurisdiction(
                jurisdiction_level=next_level,
                state=grievance.state,
                district=grievance.district,
                city=grievance.city,
                db=db
            )

            if not new_jurisdiction:
                return False  # No jurisdiction found for next level

            # Record previous authority
            previous_authority = grievance.assigned_authority

            # Update grievance
            grievance.current_jurisdiction_id = new_jurisdiction.id
            grievance.assigned_authority = self.routing_service.assign_authority(new_jurisdiction, grievance.category)
            grievance.status = GrievanceStatus.ESCALATED
            grievance.updated_at = datetime.datetime.now(datetime.timezone.utc)

            # Recalculate SLA
            self._recalculate_sla(grievance, db)

            # Blockchain integrity logic for escalation history
            from backend.cache import audit_last_hash_cache
            prev_hash = audit_last_hash_cache.get("last_hash")

            if prev_hash is None:
                # Cache miss: Fetch only the last hash from DB
                last_audit = db.query(EscalationAudit.integrity_hash).order_by(EscalationAudit.id.desc()).first()
                prev_hash = last_audit[0] if last_audit and last_audit[0] else ""
                audit_last_hash_cache.set(data=prev_hash, key="last_hash")

            # Chaining: hash(grievance_id|prev_auth|new_auth|reason|prev_hash)
            hash_content = f"{grievance.id}|{previous_authority}|{grievance.assigned_authority}|{reason.value}|{prev_hash}"
            integrity_hash = hashlib.sha256(hash_content.encode()).hexdigest()

            # Create audit log
            audit_log = EscalationAudit(
                grievance_id=grievance.id,
                previous_authority=previous_authority,
                new_authority=grievance.assigned_authority,
                reason=reason,
                notes=notes,
                integrity_hash=integrity_hash,
                previous_integrity_hash=prev_hash
            )

            db.add(audit_log)
            db.commit()

            # Update cache after successful commit
            audit_last_hash_cache.set(data=integrity_hash, key="last_hash")

            # Invalidate read caches since escalation changed status/authority
            from backend.cache import user_issues_cache, recent_issues_cache
            user_issues_cache.clear()
            recent_issues_cache.invalidate("escalation_stats")

            return True

        except Exception as e:
            db.rollback()
            print(f"Error during escalation: {e}")
            return False

    def _recalculate_sla(self, grievance: Grievance, db: Session) -> None:
        """
        Recalculate SLA deadline for a grievance.

        Args:
            grievance: Grievance object
            db: Database session
        """
        sla_hours = self.sla_service.get_sla_hours(
            severity=grievance.severity,
            jurisdiction_level=grievance.jurisdiction.level,
            department=grievance.category,
            db=db
        )

        now = datetime.datetime.now(datetime.timezone.utc)
        grievance.sla_deadline = now + datetime.timedelta(hours=sla_hours)