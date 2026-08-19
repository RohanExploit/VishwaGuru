"""HTTP routes for the grievance and escalation feature.

backend/grievance_service.py, escalation_engine.py, routing_service.py and
sla_config_service.py were all implemented, and frontend/src/api/grievances.js
plus frontend/src/views/GrievanceView.jsx were written against them -- but no
router was ever mounted, so every one of these paths returned 404. This module
wires the existing service layer to the paths the frontend already calls.
"""
from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.grievance_service import GrievanceService
from backend.models import Grievance, GrievanceStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["grievances"])

RULES_PATH = Path(__file__).resolve().parent / "grievance_rules.json"

# Statuses that count as still open for the stats tile.
_ACTIVE_STATUSES = {
    GrievanceStatus.OPEN,
    getattr(GrievanceStatus, "IN_PROGRESS", GrievanceStatus.OPEN),
    getattr(GrievanceStatus, "ESCALATED", GrievanceStatus.OPEN),
}


@lru_cache(maxsize=1)
def get_grievance_service() -> GrievanceService:
    """One shared service instance.

    GrievanceService defaults its rules path to the relative string
    "backend/grievance_rules.json", which only resolves when the process
    happens to run from the repository root. An absolute path is passed here so
    it works regardless of working directory.
    """
    return GrievanceService(rules_config_path=str(RULES_PATH))


def _enum_value(value: Any) -> Any:
    return value.value if hasattr(value, "value") else value


def _serialise_escalation(audit) -> dict[str, Any]:
    return {
        "id": audit.id,
        "grievance_id": audit.grievance_id,
        "previous_authority": audit.previous_authority,
        "new_authority": audit.new_authority,
        "timestamp": audit.timestamp,
        "reason": _enum_value(audit.reason),
        "notes": audit.notes,
    }


def _serialise_grievance(grievance: Grievance) -> dict[str, Any]:
    """GrievanceView.jsx reads escalation_history unconditionally -- it calls
    `.length` on it and maps over it -- so it is always present, never null."""
    return {
        "id": grievance.id,
        "unique_id": grievance.unique_id,
        "category": grievance.category,
        "severity": _enum_value(grievance.severity),
        "status": _enum_value(grievance.status),
        "pincode": grievance.pincode,
        "city": grievance.city,
        "district": grievance.district,
        "state": grievance.state,
        "latitude": grievance.latitude,
        "longitude": grievance.longitude,
        "address": grievance.address,
        "assigned_authority": grievance.assigned_authority,
        "sla_deadline": grievance.sla_deadline,
        "created_at": grievance.created_at,
        "updated_at": grievance.updated_at,
        "resolved_at": grievance.resolved_at,
        "escalation_history": [
            _serialise_escalation(audit)
            for audit in sorted(
                grievance.audit_logs or [],
                key=lambda a: (a.timestamp is None, a.timestamp),
            )
        ],
    }


@router.get("/grievances")
def list_grievances(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(Grievance).options(joinedload(Grievance.audit_logs))

    if status:
        try:
            query = query.filter(Grievance.status == GrievanceStatus(status))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Unknown status: {status}")
    if category:
        query = query.filter(Grievance.category == category)

    rows = (
        query.order_by(Grievance.created_at.desc()).offset(offset).limit(limit).all()
    )
    return [_serialise_grievance(row) for row in rows]


@router.get("/grievances/{grievance_id}")
def get_grievance(grievance_id: int, db: Session = Depends(get_db)):
    grievance = (
        db.query(Grievance)
        .options(joinedload(Grievance.audit_logs), joinedload(Grievance.jurisdiction))
        .filter(Grievance.id == grievance_id)
        .first()
    )
    if grievance is None:
        raise HTTPException(status_code=404, detail="Grievance not found.")
    return _serialise_grievance(grievance)


@router.get("/escalation-stats")
def escalation_stats(db: Session = Depends(get_db)):
    """Tile values consumed by GrievanceView.jsx.

    escalation_rate is returned as a percentage because the view renders it as
    `stats.escalation_rate.toFixed(1)%`.
    """
    total = db.query(Grievance).count()
    resolved = (
        db.query(Grievance).filter(Grievance.status == GrievanceStatus.RESOLVED).count()
        if hasattr(GrievanceStatus, "RESOLVED")
        else 0
    )
    escalated = (
        db.query(Grievance.id)
        .join(Grievance.audit_logs)
        .distinct()
        .count()
    )
    active = total - resolved

    return {
        "total_grievances": total,
        "escalated_grievances": escalated,
        "active_grievances": active,
        "resolved_grievances": resolved,
        "escalation_rate": (escalated / total * 100) if total else 0.0,
    }


@router.post("/grievances/{grievance_id}/escalate")
def escalate_grievance(
    grievance_id: int,
    reason: str = Query("", description="Why the grievance is being escalated"),
    db: Session = Depends(get_db),
):
    grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
    if grievance is None:
        raise HTTPException(status_code=404, detail="Grievance not found.")

    try:
        escalated = get_grievance_service().manual_escalate(grievance_id, reason)
    except Exception:
        logger.exception("Manual escalation failed for grievance %s", grievance_id)
        raise HTTPException(status_code=502, detail="Escalation service unavailable.")

    if not escalated:
        raise HTTPException(
            status_code=409,
            detail="Grievance could not be escalated; it may already be at the top level.",
        )

    db.refresh(grievance)
    return {"status": "escalated", "grievance": _serialise_grievance(grievance)}
