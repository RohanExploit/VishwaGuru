"""
Grievance Service - Main Interface
Provides the main interface for grievance management and escalation.
"""

import json
import uuid
import hashlib
import threading
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc
from datetime import datetime, timezone, timedelta

from backend.models import Grievance, Jurisdiction, GrievanceStatus, SeverityLevel, GrievanceFollower
from backend.database import SessionLocal
from backend.routing_service import RoutingService
from backend.sla_config_service import SLAConfigService
from backend.escalation_engine import EscalationEngine

class GrievanceService:
    """
    Main service for managing grievances, routing, and escalations.
    """

    # Cache for O(1) blockchain integrity hash lookups
    # Stores {grievance_id: last_integrity_hash}
    _follower_last_hash_cache = {}
    _cache_lock = threading.Lock()

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
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

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
                status=GrievanceStatus.OPEN
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
            if is_local_session:
                db.close()

    def follow_grievance(self, grievance_id: int, user_email: str, db: Session = None) -> Optional[GrievanceFollower]:
        """
        Add a follower to a grievance with blockchain-style integrity hash.
        Optimized with O(1) hash cache to avoid expensive DB scans.
        """
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

        try:
            # Check if already following
            existing = db.query(GrievanceFollower).filter(
                and_(
                    GrievanceFollower.grievance_id == grievance_id,
                    GrievanceFollower.user_email == user_email
                )
            ).first()
            if existing:
                return existing

            # Get previous hash (O(1) from cache or O(log N) from indexed DB)
            prev_hash = self._get_last_integrity_hash(grievance_id, db)

            # Calculate new integrity hash: SHA256(grievance_id | user_email | prev_hash)
            hash_input = f"{grievance_id}|{user_email}|{prev_hash or 'GENESIS'}"
            new_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            follower = GrievanceFollower(
                grievance_id=grievance_id,
                user_email=user_email,
                integrity_hash=new_hash,
                previous_integrity_hash=prev_hash
            )

            db.add(follower)
            db.commit()
            db.refresh(follower)

            # Update O(1) cache for next follower
            with self._cache_lock:
                self._follower_last_hash_cache[grievance_id] = new_hash

            return follower

        except Exception as e:
            db.rollback()
            print(f"Error following grievance: {e}")
            return None
        finally:
            if is_local_session:
                db.close()

    def _get_last_integrity_hash(self, grievance_id: int, db: Session) -> Optional[str]:
        """
        Retrieves the last integrity hash for a grievance.
        Bolt Optimization: Uses thread-safe memory cache for O(1) lookup.
        """
        with self._cache_lock:
            if grievance_id in self._follower_last_hash_cache:
                return self._follower_last_hash_cache[grievance_id]

        # Cache miss: Fallback to indexed DB query
        last_follower = db.query(GrievanceFollower)\
            .filter(GrievanceFollower.grievance_id == grievance_id)\
            .order_by(desc(GrievanceFollower.created_at))\
            .first()

        last_hash = last_follower.integrity_hash if last_follower else None

        # Update cache for next time
        if last_hash:
            with self._cache_lock:
                self._follower_last_hash_cache[grievance_id] = last_hash

        return last_hash

    def verify_follower_integrity(self, follower_id: int, db: Session = None) -> Dict[str, Any]:
        """
        Verify the blockchain-style integrity of a follower record.
        """
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

        try:
            follower = db.query(GrievanceFollower).filter(GrievanceFollower.id == follower_id).first()
            if not follower:
                return {"is_valid": False, "message": "Follower record not found"}

            # Re-calculate hash
            hash_input = f"{follower.grievance_id}|{follower.user_email}|{follower.previous_integrity_hash or 'GENESIS'}"
            calculated_hash = hashlib.sha256(hash_input.encode()).hexdigest()

            is_valid = (calculated_hash == follower.integrity_hash)

            return {
                "is_valid": is_valid,
                "current_hash": follower.integrity_hash,
                "calculated_hash": calculated_hash,
                "previous_hash": follower.previous_integrity_hash,
                "message": "Integrity verified" if is_valid else "INTEGRITY BREACH DETECTED"
            }
        finally:
            if is_local_session:
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
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

        try:
            return db.query(Grievance).options(
                joinedload(Grievance.jurisdiction),
                joinedload(Grievance.audit_logs)
            ).filter(Grievance.id == grievance_id).first()

        finally:
            if is_local_session:
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
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

        try:
            grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
            if not grievance:
                return False

            grievance.status = status
            grievance.updated_at = datetime.now(timezone.utc)

            if status == GrievanceStatus.RESOLVED:
                grievance.resolved_at = datetime.now(timezone.utc)

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            print(f"Error updating grievance status: {e}")
            return False
        finally:
            if is_local_session:
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
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

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
            if is_local_session:
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
        is_local_session = False
        if db is None:
            db = SessionLocal()
            is_local_session = True

        try:
            return db.query(Grievance).filter(
                and_(
                    Grievance.current_jurisdiction_id == jurisdiction_id,
                    Grievance.status.in_([GrievanceStatus.OPEN, GrievanceStatus.IN_PROGRESS, GrievanceStatus.ESCALATED])
                )
            ).all()

        finally:
            if is_local_session:
                db.close()