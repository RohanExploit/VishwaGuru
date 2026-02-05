from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, case
from typing import List, Optional
import os
import json
import logging

from backend.database import get_db
from backend.models import Grievance, EscalationAudit, SeverityLevel
from backend.schemas import (
    GrievanceSummaryResponse, EscalationAuditResponse, EscalationStatsResponse,
    ResponsibilityMapResponse
)
from backend.grievance_service import GrievanceService

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

        # Priority Queue Logic: Sort by Severity (Critical > High > Medium > Low) then by Date (Oldest first for resolution)
        severity_order = case(
            (Grievance.severity == SeverityLevel.CRITICAL, 1),
            (Grievance.severity == SeverityLevel.HIGH, 2),
            (Grievance.severity == SeverityLevel.MEDIUM, 3),
            (Grievance.severity == SeverityLevel.LOW, 4),
            else_=5
        )
        query = query.order_by(severity_order.asc(), Grievance.created_at.asc())

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
