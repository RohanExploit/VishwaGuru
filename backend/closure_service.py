from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from backend.models import Grievance, GrievanceFollower, ClosureConfirmation, GrievanceStatus
import logging

logger = logging.getLogger(__name__)

class ClosureService:
    """Service for handling grievance closure confirmation logic"""
    
    # Configuration
    CONFIRMATION_THRESHOLD = 0.60  # 60% of followers must confirm
    TIMEOUT_DAYS = 7  # 7 days to confirm
    MINIMUM_FOLLOWERS = 3  # Minimum followers needed for confirmation process
    
    @staticmethod
    def request_closure(grievance_id: int, db: Session) -> dict:
        """Request closure for a grievance - triggers confirmation process"""
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise ValueError("Grievance not found")
        
        if grievance.status == GrievanceStatus.RESOLVED:
            raise ValueError("Grievance is already resolved")
        
        # Count followers
        follower_count = db.query(func.count(GrievanceFollower.id)).filter(
            GrievanceFollower.grievance_id == grievance_id
        ).scalar()
        
        # If less than minimum followers, skip confirmation process
        if follower_count < ClosureService.MINIMUM_FOLLOWERS:
            grievance.status = GrievanceStatus.RESOLVED
            grievance.resolved_at = datetime.now(timezone.utc)
            grievance.closure_approved = True
            db.commit()
            
            return {
                "message": "Grievance resolved (no confirmation needed - insufficient followers)",
                "skip_confirmation": True,
                "follower_count": follower_count
            }
        
        # Set closure pending
        grievance.pending_closure = True
        grievance.closure_requested_at = datetime.now(timezone.utc)
        grievance.closure_confirmation_deadline = datetime.now(timezone.utc) + timedelta(days=ClosureService.TIMEOUT_DAYS)
        db.commit()
        
        required_confirmations = max(1, int(follower_count * ClosureService.CONFIRMATION_THRESHOLD))
        
        return {
            "message": "Closure confirmation requested - waiting for community approval",
            "skip_confirmation": False,
            "follower_count": follower_count,
            "required_confirmations": required_confirmations,
            "deadline": grievance.closure_confirmation_deadline
        }
    
    @staticmethod
    def submit_confirmation(grievance_id: int, user_email: str, confirmation_type: str, reason: str, db: Session) -> dict:
        """Submit a closure confirmation or dispute"""
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise ValueError("Grievance not found")
        
        if not grievance.pending_closure:
            raise ValueError("Grievance is not pending closure confirmation")
        
        # Check if user is a follower
        is_follower = db.query(GrievanceFollower).filter(
            GrievanceFollower.grievance_id == grievance_id,
            GrievanceFollower.user_email == user_email
        ).first()
        
        if not is_follower:
            raise ValueError("Only followers can confirm or dispute closure")
        
        # Check if user already submitted confirmation
        existing = db.query(ClosureConfirmation).filter(
            ClosureConfirmation.grievance_id == grievance_id,
            ClosureConfirmation.user_email == user_email
        ).first()
        
        if existing:
            raise ValueError("You have already submitted a response for this closure")
        
        # Create confirmation record
        confirmation = ClosureConfirmation(
            grievance_id=grievance_id,
            user_email=user_email,
            confirmation_type=confirmation_type,
            reason=reason
        )
        db.add(confirmation)
        db.commit()
        
        # Check if threshold is met
        return ClosureService.check_and_finalize_closure(grievance_id, db)
    
    @staticmethod
    def check_and_finalize_closure(grievance_id: int, db: Session) -> dict:
        """Check if closure threshold is met and finalize if needed"""
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance or not grievance.pending_closure:
            return {"closure_finalized": False}
        
        # Count followers and confirmations
        total_followers = db.query(func.count(GrievanceFollower.id)).filter(
            GrievanceFollower.grievance_id == grievance_id
        ).scalar()
        
        confirmations_count = db.query(func.count(ClosureConfirmation.id)).filter(
            ClosureConfirmation.grievance_id == grievance_id,
            ClosureConfirmation.confirmation_type == "confirmed"
        ).scalar()
        
        disputes_count = db.query(func.count(ClosureConfirmation.id)).filter(
            ClosureConfirmation.grievance_id == grievance_id,
            ClosureConfirmation.confirmation_type == "disputed"
        ).scalar()
        
        required_confirmations = max(1, int(total_followers * ClosureService.CONFIRMATION_THRESHOLD))
        
        # Check if threshold is met
        if confirmations_count >= required_confirmations:
            grievance.status = GrievanceStatus.RESOLVED
            grievance.resolved_at = datetime.now(timezone.utc)
            grievance.closure_approved = True
            grievance.pending_closure = False
            db.commit()
            
            return {
                "closure_finalized": True,
                "approved": True,
                "confirmations": confirmations_count,
                "required": required_confirmations,
                "message": "Grievance closure approved by community"
            }
        
        return {
            "closure_finalized": False,
            "confirmations": confirmations_count,
            "disputes": disputes_count,
            "required": required_confirmations,
            "total_followers": total_followers
        }
    
    @staticmethod
    def check_timeout_and_finalize(db: Session):
        """Background task to check for timed-out closure requests"""
        now = datetime.now(timezone.utc)
        
        # Find grievances with expired deadlines
        expired_grievances = db.query(Grievance).filter(
            Grievance.pending_closure == True,
            Grievance.closure_confirmation_deadline < now
        ).all()
        
        for grievance in expired_grievances:
            # Check current status
            result = ClosureService.check_and_finalize_closure(grievance.id, db)
            
            if not result.get("closure_finalized"):
                # Timeout - log dispute and keep open
                logger.warning(f"Grievance {grievance.id} closure timeout - threshold not met")
                grievance.pending_closure = False
                grievance.closure_approved = False
                # Keep status as is (not resolved)
                db.commit()
        
        return len(expired_grievances)