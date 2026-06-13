from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, case
from typing import List, Optional
import os
import json
import logging
import hashlib
from datetime import datetime, timezone

from backend.database import get_db
import hmac
from backend.config import get_auth_config
from backend.models import Grievance, EscalationAudit, GrievanceFollower, ClosureConfirmation, GrievanceStatus
from backend.schemas import (
    GrievanceSummaryResponse,
    EscalationAuditResponse,
    EscalationStatsResponse,
    ResponsibilityMapResponse,
    FollowGrievanceRequest,
    FollowGrievanceResponse,
    RequestClosureRequest,
    RequestClosureResponse,
    ConfirmClosureRequest,
    ConfirmClosureResponse,
    ClosureStatusResponse,
    BlockchainVerificationResponse,
)
from backend.cache import grievances_list_cache, grievance_stats_cache
from fastapi import Response
from backend.grievance_service import GrievanceService
from backend.closure_service import ClosureService
from backend.cache import grievance_list_cache, escalation_stats_cache

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/grievances", response_model=List[GrievanceSummaryResponse])
def get_grievances(
    status: Optional[str] = Query(None, description="Filter by status"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db),
):
    """
    Get list of grievances with escalation history.
    Optimized: Uses serialization caching and selectinload for audit_logs.
    """
    try:
        # Check cache
        cache_key = f"grievances_{status}_{category}_{limit}_{offset}"
        cached_json = grievances_list_cache.get(cache_key)
        if cached_json:
            return Response(content=cached_json, media_type="application/json")

        query = db.query(Grievance).options(
            selectinload(Grievance.audit_logs), joinedload(Grievance.jurisdiction)
        )

        if status:
            query = query.filter(Grievance.status == status)
        if category:
            query = query.filter(Grievance.category == category)

        grievances = query.offset(offset).limit(limit).all()

        # Convert to response format (dictionaries for faster JSON serialization)
        result = []
        for grievance in grievances:
            escalation_history = [
                {
                    "id": audit.id,
                    "grievance_id": audit.grievance_id,
                    "previous_authority": audit.previous_authority,
                    "new_authority": audit.new_authority,
                    "timestamp": audit.timestamp.isoformat() if audit.timestamp else None,
                    "reason": audit.reason.value
                }
                for audit in grievance.audit_logs
            ]

            result.append({
                "id": grievance.id,
                "unique_id": grievance.unique_id,
                "category": grievance.category,
                "severity": grievance.severity.value,
                "pincode": grievance.pincode,
                "city": grievance.city,
                "district": grievance.district,
                "state": grievance.state,
                "current_jurisdiction_id": grievance.current_jurisdiction_id,
                "assigned_authority": grievance.assigned_authority,
                "sla_deadline": grievance.sla_deadline.isoformat() if grievance.sla_deadline else None,
                "status": grievance.status.value,
                "created_at": grievance.created_at.isoformat() if grievance.created_at else None,
                "updated_at": grievance.updated_at.isoformat() if grievance.updated_at else None,
                "resolved_at": grievance.resolved_at.isoformat() if grievance.resolved_at else None,
                "escalation_history": escalation_history
            })

        # Cache serialized JSON to bypass Pydantic overhead on hits
        json_data = json.dumps(result)
        grievances_list_cache.set(json_data, cache_key)

        return Response(content=json_data, media_type="application/json")

    except Exception as e:
        logger.error(f"Error getting grievances: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve grievances")


@router.get("/grievances/{grievance_id}", response_model=GrievanceSummaryResponse)
def get_grievance(grievance_id: int, db: Session = Depends(get_db)):
    """
    Get detailed grievance information with escalation history.
    Optimized: Uses selectinload for audit_logs for consistent fetching performance.
    """
    try:
        grievance = (
            db.query(Grievance)
            .options(
                selectinload(Grievance.audit_logs), joinedload(Grievance.jurisdiction)
            )
            .filter(Grievance.id == grievance_id)
            .first()
        )

        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        escalation_history = [
            EscalationAuditResponse(
                id=audit.id,
                grievance_id=audit.grievance_id,
                previous_authority=audit.previous_authority,
                new_authority=audit.new_authority,
                timestamp=audit.timestamp,
                reason=audit.reason.value,
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
            escalation_history=escalation_history,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve grievance")


@router.get("/escalation-stats", response_model=EscalationStatsResponse)
def get_escalation_stats(db: Session = Depends(get_db)):
    """
    Get escalation statistics.
    Optimized: Uses a single aggregate query with case sum for multiple metrics, avoiding Python dictionary overhead.
    """
    try:
        # Check cache
        cached_json = grievance_stats_cache.get("default")
        if cached_json:
            return Response(content=cached_json, media_type="application/json")

        # Perform aggregation in a single query for performance
        stats = db.query(
            func.count(Grievance.id).label("total"),
            func.sum(case((Grievance.status == GrievanceStatus.ESCALATED, 1), else_=0)).label("escalated"),
            func.sum(case((Grievance.status.in_([GrievanceStatus.OPEN, GrievanceStatus.IN_PROGRESS]), 1), else_=0)).label("active"),
            func.sum(case((Grievance.status == GrievanceStatus.RESOLVED, 1), else_=0)).label("resolved")
        ).first()

        total_grievances = stats.total or 0
        escalated_grievances = int(stats.escalated or 0)
        active_grievances = int(stats.active or 0)
        resolved_grievances = int(stats.resolved or 0)

        escalation_rate = (escalated_grievances / total_grievances * 100) if total_grievances > 0 else 0

        stats_data = {
            "total_grievances": total_grievances,
            "escalated_grievances": escalated_grievances,
            "active_grievances": active_grievances,
            "resolved_grievances": resolved_grievances,
            "escalation_rate": escalation_rate
        }

        # Cache serialized JSON to bypass Pydantic overhead on hits
        json_data = json.dumps(stats_data)
        grievance_stats_cache.set(json_data, "default")

        return Response(content=json_data, media_type="application/json")

    except Exception as e:
        logger.error(f"Error getting escalation stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve escalation statistics"
        )


@router.post("/grievances/{grievance_id}/escalate")
def manual_escalate_grievance(
    grievance_id: int,
    request: Request,
    reason: str = Query(..., description="Reason for manual escalation"),
    db: Session = Depends(get_db),
):
    """Manually escalate a grievance"""
    try:
        grievance_service = getattr(request.app.state, "grievance_service", None)
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
            db=db,
        )

        if success:
            # Invalidate cache
            grievance_list_cache.clear()
            escalation_stats_cache.clear()
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
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "data",
        "responsibility_map.json",
    )
    if not os.path.exists(file_path):
        # Fallback to backend/../data ? No, backend is root usually
        file_path = os.path.join("data", "responsibility_map.json")

    with open(file_path, "r") as f:
        return json.load(f)


@router.get("/responsibility-map", response_model=ResponsibilityMapResponse)
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


@router.post(
    "/grievances/{grievance_id}/follow", response_model=FollowGrievanceResponse
)
def follow_grievance(
    grievance_id: int, request: FollowGrievanceRequest, db: Session = Depends(get_db)
):
    """Follow a grievance to receive updates and participate in closure confirmation"""
    try:
        # Check if grievance exists
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        # Check if already following
        existing = (
            db.query(GrievanceFollower)
            .filter(
                GrievanceFollower.grievance_id == grievance_id,
                GrievanceFollower.user_email == request.user_email,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=400, detail="Already following this grievance"
            )

        # Create follower record
        follower = GrievanceFollower(
            grievance_id=grievance_id, user_email=request.user_email
        )
        db.add(follower)
        db.commit()

        # Invalidate caches
        grievance_list_cache.clear()
        
        # Invalidate cache
        grievance_list_cache.clear()

        # Count total followers
        total_followers = (
            db.query(func.count(GrievanceFollower.id))
            .filter(GrievanceFollower.grievance_id == grievance_id)
            .scalar()
        )

        return FollowGrievanceResponse(
            grievance_id=grievance_id,
            user_email=request.user_email,
            message="Successfully following grievance",
            total_followers=total_followers,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error following grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to follow grievance")


@router.delete("/grievances/{grievance_id}/follow")
def unfollow_grievance(
    grievance_id: int,
    user_email: str = Query(..., description="Email of user to unfollow"),
    db: Session = Depends(get_db),
):
    """Unfollow a grievance"""
    try:
        follower = (
            db.query(GrievanceFollower)
            .filter(
                GrievanceFollower.grievance_id == grievance_id,
                GrievanceFollower.user_email == user_email,
            )
            .first()
        )

        if not follower:
            raise HTTPException(status_code=404, detail="Not following this grievance")

        db.delete(follower)
        db.commit()

        # Invalidate caches
        grievance_list_cache.clear()
        
        # Invalidate cache
        grievance_list_cache.clear()

        return {"message": "Successfully unfollowed grievance"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unfollowing grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to unfollow grievance")


@router.post(
    "/grievances/{grievance_id}/request-closure", response_model=RequestClosureResponse
)
def request_grievance_closure(
    grievance_id: int,
    request_data: RequestClosureRequest,
    db: Session = Depends(get_db),
):
    """Request closure of a grievance (admin only) - triggers community confirmation"""
    try:
        result = ClosureService.request_closure(grievance_id, db)
        
        # Invalidate cache
        grievance_list_cache.clear()
        escalation_stats_cache.clear()

        if result.get("skip_confirmation"):
            # Invalidate caches as status might have changed to resolved
            grievance_list_cache.clear()
            escalation_stats_cache.clear()
            return RequestClosureResponse(
                grievance_id=grievance_id,
                message=result["message"],
                confirmation_deadline=datetime.now(timezone.utc),
                total_followers=result["follower_count"],
                required_confirmations=0,
            )
        
        # Invalidate caches
        grievance_list_cache.clear()
        escalation_stats_cache.clear()

        return RequestClosureResponse(
            grievance_id=grievance_id,
            message=result["message"],
            confirmation_deadline=result["deadline"],
            total_followers=result["follower_count"],
            required_confirmations=result["required_confirmations"],
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error requesting closure for grievance {grievance_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to request closure")


@router.post(
    "/grievances/{grievance_id}/confirm-closure", response_model=ConfirmClosureResponse
)
def confirm_grievance_closure(
    grievance_id: int,
    confirmation: ConfirmClosureRequest,
    db: Session = Depends(get_db),
):
    """Confirm or dispute a grievance closure (followers only)"""
    try:
        # Invalidate caches as status or approval might change
        grievance_list_cache.clear()
        escalation_stats_cache.clear()

        result = ClosureService.submit_confirmation(
            grievance_id=grievance_id,
            user_email=confirmation.user_email,
            confirmation_type=confirmation.confirmation_type,
            reason=confirmation.reason,
            db=db,
        )

        message = "Confirmation recorded"
        if result.get("closure_finalized"):
            if result.get("approved"):
                message = "Grievance closure approved by community!"
            else:
                message = "Confirmation recorded - grievance remains open"
        
        # Invalidate cache
        grievance_list_cache.clear()
        escalation_stats_cache.clear()

        return ConfirmClosureResponse(
            grievance_id=grievance_id,
            message=message,
            current_confirmations=result.get("confirmations", 0),
            required_confirmations=result.get("required", 0),
            current_disputes=result.get("disputes", 0),
            closure_approved=result.get("approved", False),
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(
            f"Error confirming closure for grievance {grievance_id}: {e}", exc_info=True
        )
        raise HTTPException(status_code=500, detail="Failed to confirm closure")


@router.get(
    "/grievances/{grievance_id}/closure-status", response_model=ClosureStatusResponse
)
def get_closure_status(grievance_id: int, db: Session = Depends(get_db)):
    """Get current closure confirmation status for a grievance"""
    try:
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        # Optimized: Use a single aggregate query to calculate total followers, confirmations and disputes in one database roundtrip
        total_followers = db.query(func.count(GrievanceFollower.id)).filter(
            GrievanceFollower.grievance_id == grievance_id
        ).scalar()
        
        # Get all confirmation counts in a single query instead of multiple round-trips
        # Optimized: Group by is faster than sum(case()) in SQLite/Postgres for this workload
        counts = db.query(
            ClosureConfirmation.confirmation_type,
            func.count(ClosureConfirmation.id)
        ).filter(ClosureConfirmation.grievance_id == grievance_id).group_by(ClosureConfirmation.confirmation_type).all()
        
        counts_dict = {ctype: count for ctype, count in counts}
        confirmations_count = counts_dict.get("confirmed", 0)
        disputes_count = counts_dict.get("disputed", 0)
        
        required_confirmations = max(1, int(total_followers * ClosureService.CONFIRMATION_THRESHOLD))
        
        counts_dict = dict(counts)

        confirmations_count = counts_dict.get("confirmed", 0)
        disputes_count = counts_dict.get("disputed", 0)

        required_confirmations = max(
            1, int(total_followers * ClosureService.CONFIRMATION_THRESHOLD)
        )

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
            days_remaining=days_remaining,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting closure status for grievance {grievance_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to get closure status")


@router.get(
    "/audit/{audit_id}/blockchain-verify", response_model=BlockchainVerificationResponse
)
def verify_escalation_audit_blockchain(audit_id: int, db: Session = Depends(get_db)):
    """
    Verify the cryptographic integrity of an escalation audit log using blockchain-style chaining.
    Optimized: Uses previous_integrity_hash column for O(1) verification.
    """
    try:
        audit = (
            db.query(
                EscalationAudit.grievance_id,
                EscalationAudit.previous_authority,
                EscalationAudit.new_authority,
                EscalationAudit.reason,
                EscalationAudit.integrity_hash,
                EscalationAudit.previous_integrity_hash,
            )
            .filter(EscalationAudit.id == audit_id)
            .first()
        )

        if not audit:
            raise HTTPException(status_code=404, detail="Audit log not found")

        # Determine previous hash (O(1) from stored column)
        prev_hash = audit.previous_integrity_hash or ""

        # Recompute hash based on current data and previous hash
        # Chaining logic: hash(grievance_id|previous_authority|new_authority|reason|prev_hash)
        reason_str = (
            audit.reason.value if hasattr(audit.reason, "value") else str(audit.reason)
        )
        hash_content = f"{audit.grievance_id}|{audit.previous_authority}|{audit.new_authority}|{reason_str}|{prev_hash}"

        secret_key = get_auth_config().secret_key
        computed_hash = hmac.new(
            secret_key.encode("utf-8"), hash_content.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if audit.integrity_hash is None:
            is_valid = False
            message = "No integrity hash present for this audit log; cryptographic integrity cannot be verified."
        else:
            is_valid = computed_hash == audit.integrity_hash
            message = (
                "Integrity verified. This escalation audit log is cryptographically sealed."
                if is_valid
                else "Integrity check failed! The audit data does not match its cryptographic seal."
            )

        return BlockchainVerificationResponse(
            is_valid=is_valid,
            current_hash=audit.integrity_hash,
            computed_hash=computed_hash,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error verifying escalation audit blockchain for {audit_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to verify audit integrity")


@router.get(
    "/grievances/{grievance_id}/blockchain-verify",
    response_model=BlockchainVerificationResponse,
)
def verify_grievance_blockchain(grievance_id: int, db: Session = Depends(get_db)):
    """
    Verify the cryptographic integrity of a grievance using blockchain-style chaining.
    Optimized: Uses previous_integrity_hash column for O(1) verification.
    """
    try:
        grievance = (
            db.query(
                Grievance.unique_id,
                Grievance.category,
                Grievance.severity,
                Grievance.integrity_hash,
                Grievance.previous_integrity_hash,
            )
            .filter(Grievance.id == grievance_id)
            .first()
        )

        if not grievance:
            raise HTTPException(status_code=404, detail="Grievance not found")

        # Determine previous hash (O(1) from stored column)
        prev_hash = grievance.previous_integrity_hash or ""

        # Recompute hash based on current data and previous hash
        # Chaining logic: hash(unique_id|category|severity|prev_hash)
        severity_value = (
            grievance.severity.value
            if hasattr(grievance.severity, "value")
            else grievance.severity
        )
        hash_content = (
            f"{grievance.unique_id}|{grievance.category}|{severity_value}|{prev_hash}"
        )
        computed_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        if grievance.integrity_hash is None:
            # Legacy or unsealed grievance: no integrity hash stored, so we cannot verify tampering.
            is_valid = False
            message = "No integrity hash present for this grievance; cryptographic integrity cannot be verified."
        else:
            is_valid = computed_hash == grievance.integrity_hash
            message = (
                "Integrity verified. This grievance record is cryptographically sealed."
                if is_valid
                else "Integrity check failed! The grievance data does not match its cryptographic seal."
            )
        return BlockchainVerificationResponse(
            is_valid=is_valid,
            current_hash=grievance.integrity_hash,
            computed_hash=computed_hash,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error verifying grievance blockchain for {grievance_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to verify grievance integrity"
        )


@router.get(
    "/closure-confirmation/{confirmation_id}/blockchain-verify",
    response_model=BlockchainVerificationResponse,
)
def verify_closure_confirmation_blockchain(
    confirmation_id: int, db: Session = Depends(get_db)
):
    """
    Verify the cryptographic integrity of a closure confirmation using blockchain-style chaining.
    Optimized: Uses previous_integrity_hash column for O(1) verification.
    """
    try:
        confirmation = (
            db.query(
                ClosureConfirmation.grievance_id,
                ClosureConfirmation.user_email,
                ClosureConfirmation.confirmation_type,
                ClosureConfirmation.integrity_hash,
                ClosureConfirmation.previous_integrity_hash,
            )
            .filter(ClosureConfirmation.id == confirmation_id)
            .first()
        )

        if not confirmation:
            raise HTTPException(
                status_code=404, detail="Closure confirmation not found"
            )

        # Determine previous hash (O(1) from stored column)
        prev_hash = confirmation.previous_integrity_hash or ""

        # Recompute hash based on current data and previous hash
        # Chaining logic: hash(grievance_id|user_email|confirmation_type|prev_hash)
        hash_content = f"{confirmation.grievance_id}|{confirmation.user_email}|{confirmation.confirmation_type}|{prev_hash}"

        secret_key = get_auth_config().secret_key
        computed_hash = hmac.new(
            secret_key.encode("utf-8"), hash_content.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if confirmation.integrity_hash is None:
            is_valid = False
            message = "No integrity hash present for this confirmation; cryptographic integrity cannot be verified."
        else:
            is_valid = hmac.compare_digest(computed_hash, confirmation.integrity_hash)
            message = (
                "Integrity verified. This closure confirmation is cryptographically sealed."
                if is_valid
                else "Integrity check failed! The confirmation data does not match its cryptographic seal."
            )

        return BlockchainVerificationResponse(
            is_valid=is_valid,
            current_hash=confirmation.integrity_hash,
            computed_hash=computed_hash,
            message=message,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error verifying closure confirmation blockchain for {confirmation_id}: {e}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail="Failed to verify confirmation integrity"
        )
