from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
import os
import json
import logging
from datetime import datetime, timezone

from backend.database import get_db
from backend.models import Grievance, EscalationAudit, GrievanceFollower, ClosureConfirmation
from backend.schemas import (
    GrievanceSummaryResponse, EscalationAuditResponse, EscalationStatsResponse,
    ResponsibilityMapResponse,
    FollowGrievanceRequest, FollowGrievanceResponse,
    RequestClosureRequest, RequestClosureResponse,
    ConfirmClosureRequest, ConfirmClosureResponse,
    ClosureStatusResponse
)
from backend.grievance_service import GrievanceService
from backend.closure_service import ClosureService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/api/grievances", response_model=List[GrievanceSummaryResponse])
def get_grievances(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """Get list of grievances with escalation history"""
    try:
        query = db.query(Grievance).options(
            joinedload(Grievance.audit_logs),
            joinedload(Grievance.jurisdiction)
        )

        if status:
            query = query.filter(Grievance.status == status)
        if category:
            query = query.filter(Grievance.category == category)

        grievances = query.offset(offset).limit(limit).all()

        # Convert to response format
        result = []
        for grievance in grievances:
            escalation_history = [
                EscalationAuditResponse(
                    id=audit.id,
                    grievance_id=audit.grievance_id,
                    previous_authority=audit.previous_authority,
                    new_authority=audit.new_authority,
                    timestamp=audit.timestamp,
                    reason=audit.reason.value
                )
                for audit in grievance.audit_logs
            ]

            result.append(GrievanceSummaryResponse(
                id=grievance.id,
                unique_id=grievance.unique_id,
                category=grievance.category,
                severity=grievance.severity.value,
                pincode=grievance.pincode,
                city=grievance.city,
                district=grievance.district,
                state=grievance.state,
                current_jurisdiction_id=grievance.current_jurisdiction_id,
                assigned_authority=grievance.assigned_authority,
                sla_deadline=grievance.sla_deadline,
                status=grievance.status.value,
                created_at=grievance.created_at,
                updated_at=grievance.updated_at,
                resolved_at=grievance.resolved_at,
                escalation_history=escalation_history
            ))

        return result

    except Exception as e:
        logger.error(f"Error getting grievances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve grievances")

@router.get("/api/grievances/{grievance_id}", response_model=GrievanceSummaryResponse)
def get_grievance(grievance_id: int, db: Session = Depends(get_db)):
    """Get detailed grievance information with escalation history"""
    try:
        grievance = db.query(Grievance).options(
            joinedload(Grievance.audit_logs),
            joinedload(Grievance.jurisdiction)
        ).filter(Grievance.id == grievance_id).first()

        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        escalation_history = [
            EscalationAuditResponse(
                id=audit.id,
                grievance_id=audit.grievance_id,
                previous_authority=audit.previous_authority,
                new_authority=audit.new_authority,
                timestamp=audit.timestamp,
                reason=audit.reason.value
            )
            for audit in grievance.audit_logs
        ]

        return GrievanceSummaryResponse(
            id=grievance.id,
            unique_id=grievance.unique_id,
            category=grievance.category,
            severity=grievance.severity.value,
            pincode=grievance.pincode,
            city=grievance.city,
            district=grievance.district,
            state=grievance.state,
            current_jurisdiction_id=grievance.current_jurisdiction_id,
            assigned_authority=grievance.assigned_authority,
            sla_deadline=grievance.sla_deadline,
            status=grievance.status.value,
            created_at=grievance.created_at,
            updated_at=grievance.updated_at,
            resolved_at=grievance.resolved_at,
            escalation_history=escalation_history
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve grievance")

@router.get("/api/escalation-stats", response_model=EscalationStatsResponse)
def get_escalation_stats(db: Session = Depends(get_db)):
    """Get escalation statistics"""
    try:
        total_grievances = db.query(func.count(Grievance.id)).scalar()
        escalated_grievances = db.query(func.count(Grievance.id)).filter(Grievance.status == "escalated").scalar()
        active_grievances = db.query(func.count(Grievance.id)).filter(Grievance.status.in_(["open", "in_progress"])).scalar()
        resolved_grievances = db.query(func.count(Grievance.id)).filter(Grievance.status == "resolved").scalar()

        escalation_rate = (escalated_grievances / total_grievances * 100) if total_grievances > 0 else 0

        return EscalationStatsResponse(
            total_grievances=total_grievances,
            escalated_grievances=escalated_grievances,
            active_grievances=active_grievances,
            resolved_grievances=resolved_grievances,
            escalation_rate=escalation_rate
        )

    except Exception as e:
        logger.error(f"Error getting escalation stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve escalation statistics")

@router.post("/api/grievances/{grievance_id}/escalate")
def manual_escalate_grievance(
    grievance_id: int,
    request: Request,
    reason: str = Query(..., description="Reason for manual escalation"),
    db: Session = Depends(get_db)
):
    """Manually escalate a grievance"""
    try:
        grievance_service = getattr(request.app.state, 'grievance_service', None)
        if not grievance_service:
            # Try to initialize if missing (fallback)
            grievance_service = GrievanceService()

        # Get the grievance
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        # Perform manual escalation
        success = grievance_service.escalation_engine.escalate_grievance_severity(
            grievance_id=grievance_id,
            new_severity=grievance.severity,  # Keep same severity, just escalate jurisdiction
            reason=reason,
            db=db
        )

        if success:
            return {"message": "Grievance escalated successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to escalate grievance")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error escalating grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to escalate grievance")

def _load_responsibility_map():
    # Assuming the data folder is at the root level relative to where backend is run
    # Adjust path as necessary.
    file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "responsibility_map.json")
    if not os.path.exists(file_path):
        # Fallback to backend/../data ? No, backend is root usually
        file_path = os.path.join("data", "responsibility_map.json")

    with open(file_path, "r") as f:
        return json.load(f)

@router.get("/api/responsibility-map", response_model=ResponsibilityMapResponse)
def get_responsibility_map():
    """Get responsibility mapping data for civic authorities"""
    try:
        data = _load_responsibility_map()
        return ResponsibilityMapResponse(data=data)
    except FileNotFoundError:
        logger.error("Responsibility map file not found", exc_info=True)
        raise HTTPException(status_code=404, detail="Responsibility map data not found")
    except Exception as e:
        logger.error(f"Error loading responsibility map: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to load responsibility map")


# ============================================================================
# COMMUNITY CONFIRMATION ENDPOINTS (Issue #289)
# ============================================================================

@router.post("/api/grievances/{grievance_id}/follow", response_model=FollowGrievanceResponse)
def follow_grievance(
    grievance_id: int,
    request: FollowGrievanceRequest,
    db: Session = Depends(get_db)
):
    """Follow a grievance to receive updates and participate in closure confirmation"""
    try:
        # Check if grievance exists
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
        # Check if already following
        existing = db.query(GrievanceFollower).filter(
            GrievanceFollower.grievance_id == grievance_id,
            GrievanceFollower.user_email == request.user_email
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Already following this grievance")
        
        # Create follower record
        follower = GrievanceFollower(
            grievance_id=grievance_id,
            user_email=request.user_email
        )
        db.add(follower)
        db.commit()
        
        # Count total followers
        total_followers = db.query(func.count(GrievanceFollower.id)).filter(
            GrievanceFollower.grievance_id == grievance_id
        ).scalar()
        
        return FollowGrievanceResponse(
            grievance_id=grievance_id,
            user_email=request.user_email,
            message="Successfully following grievance",
            total_followers=total_followers
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error following grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to follow grievance")


@router.delete("/api/grievances/{grievance_id}/follow")
def unfollow_grievance(
    grievance_id: int,
    user_email: str = Query(..., description="Email of user to unfollow"),
    db: Session = Depends(get_db)
):
    """Unfollow a grievance"""
    try:
        follower = db.query(GrievanceFollower).filter(
            GrievanceFollower.grievance_id == grievance_id,
            GrievanceFollower.user_email == user_email
        ).first()
        
        if not follower:
            raise HTTPException(status_code=404, detail="Not following this grievance")
        
        db.delete(follower)
        db.commit()
        
        return {"message": "Successfully unfollowed grievance"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unfollow grievance")


@router.post("/api/grievances/{grievance_id}/request-closure", response_model=RequestClosureResponse)
def request_grievance_closure(
    grievance_id: int,
    request_data: RequestClosureRequest,
    db: Session = Depends(get_db)
):
    """Request closure of a grievance (admin only) - triggers community confirmation"""
    try:
        result = ClosureService.request_closure(grievance_id, db)
        
        if result.get("skip_confirmation"):
            return RequestClosureResponse(
                grievance_id=grievance_id,
                message=result["message"],
                confirmation_deadline=datetime.now(timezone.utc),
                total_followers=result["follower_count"],
                required_confirmations=0
            )
        
        return RequestClosureResponse(
            grievance_id=grievance_id,
            message=result["message"],
            confirmation_deadline=result["deadline"],
            total_followers=result["follower_count"],
            required_confirmations=result["required_confirmations"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error requesting closure for grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to request closure")


@router.post("/api/grievances/{grievance_id}/confirm-closure", response_model=ConfirmClosureResponse)
def confirm_grievance_closure(
    grievance_id: int,
    confirmation: ConfirmClosureRequest,
    db: Session = Depends(get_db)
):
    """Confirm or dispute a grievance closure (followers only)"""
    try:
        result = ClosureService.submit_confirmation(
            grievance_id=grievance_id,
            user_email=confirmation.user_email,
            confirmation_type=confirmation.confirmation_type,
            reason=confirmation.reason,
            db=db
        )
        
        message = "Confirmation recorded"
        if result.get("closure_finalized"):
            if result.get("approved"):
                message = "Grievance closure approved by community!"
            else:
                message = "Confirmation recorded - grievance remains open"
        
        return ConfirmClosureResponse(
            grievance_id=grievance_id,
            message=message,
            current_confirmations=result.get("confirmations", 0),
            required_confirmations=result.get("required", 0),
            current_disputes=result.get("disputes", 0),
            closure_approved=result.get("approved", False)
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error confirming closure for grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to confirm closure")


@router.get("/api/grievances/{grievance_id}/closure-status", response_model=ClosureStatusResponse)
def get_closure_status(
    grievance_id: int,
    db: Session = Depends(get_db)
):
    """Get current closure confirmation status for a grievance"""
    try:
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")
        
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
        
        days_remaining = None
        if grievance.closure_confirmation_deadline:
            delta = grievance.closure_confirmation_deadline - datetime.now(timezone.utc)
            days_remaining = max(0, delta.days)
        
        return ClosureStatusResponse(
            grievance_id=grievance_id,
            pending_closure=grievance.pending_closure or False,
            closure_approved=grievance.closure_approved or False,
            total_followers=total_followers,
            confirmations_count=confirmations_count,
            disputes_count=disputes_count,
            required_confirmations=required_confirmations,
            confirmation_deadline=grievance.closure_confirmation_deadline,
            days_remaining=days_remaining
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting closure status for grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get closure status")
