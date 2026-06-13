"""
Resolution Proof Router - API endpoints for Verifiable OnGround Resolution (Issue #292)

Provides endpoints for:
- Generating Resolution Proof Tokens (RPT)
- Submitting geo-temporally bound evidence
- Public verification of resolution authenticity
- Evidence audit trail
- Duplicate/fraud detection
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.resolution_proof_service import ResolutionProofService
from backend.schemas import (
    GenerateRPTRequest, RPTResponse,
    SubmitEvidenceRequest, EvidenceResponse,
    VerificationResponse, AuditTrailResponse,
    DuplicateCheckResponse, BlockchainVerificationResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/resolution-proof",
    tags=["Resolution Proof"]
)


# ============================================================================
# TOKEN GENERATION
# ============================================================================

@router.post("/generate-token", response_model=RPTResponse)
def generate_resolution_token(
    request: GenerateRPTRequest,
    db: Session = Depends(get_db)
):
    """
    Generate a one-time Resolution Proof Token (RPT) for a grievance.

    - Only officials/admins should call this when initiating resolution
    - Token is valid for 15 minutes
    - Token is bound to the grievance's GPS location (geofence)
    - Previous unused tokens for the same grievance are invalidated
    """
    try:
        token = ResolutionProofService.generate_proof_token(
            grievance_id=request.grievance_id,
            authority_email=request.authority_email,
            db=db,
            geofence_radius=request.geofence_radius_meters or 200.0
        )

        return RPTResponse(
            token_id=token.token_id,
            grievance_id=token.grievance_id,
            geofence_latitude=token.geofence_latitude,
            geofence_longitude=token.geofence_longitude,
            geofence_radius_meters=token.geofence_radius_meters,
            valid_from=token.valid_from,
            valid_until=token.valid_until,
            token_signature=token.token_signature,
            message="Resolution Proof Token generated successfully. Valid for 15 minutes."
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating RPT: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate resolution proof token")


# ============================================================================
# EVIDENCE SUBMISSION
# ============================================================================

@router.post("/submit-evidence", response_model=EvidenceResponse)
def submit_resolution_evidence(
    request: SubmitEvidenceRequest,
    db: Session = Depends(get_db)
):
    """
    Submit resolution evidence with cryptographic proof.

    - Requires a valid, unexpired RPT
    - Evidence must be captured within the geofence radius
    - Evidence hash (SHA-256) must be unique (anti-fraud)
    - Server signs the evidence bundle for integrity verification
    """
    try:
        evidence = ResolutionProofService.submit_evidence(
            token_id=request.token_id,
            evidence_hash=request.evidence_hash,
            gps_latitude=request.gps_latitude,
            gps_longitude=request.gps_longitude,
            capture_timestamp=request.capture_timestamp,
            db=db,
            device_fingerprint_hash=request.device_fingerprint_hash,
        )

        return EvidenceResponse(
            id=evidence.id,
            grievance_id=evidence.grievance_id,
            evidence_hash=evidence.evidence_hash,
            gps_latitude=evidence.gps_latitude,
            gps_longitude=evidence.gps_longitude,
            capture_timestamp=evidence.capture_timestamp,
            verification_status=evidence.verification_status.value,
            server_signature=evidence.server_signature,
            created_at=evidence.created_at,
            message="Evidence submitted and verified successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error submitting evidence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to submit resolution evidence")


# ============================================================================
# PUBLIC VERIFICATION
# ============================================================================

@router.get("/verify/{grievance_id}", response_model=VerificationResponse)
def verify_resolution(
    grievance_id: int,
    db: Session = Depends(get_db)
):
    """
    Verify the resolution of a grievance (public endpoint).

    Citizens can use this to check:
    - Whether evidence exists and is cryptographically valid
    - Whether the evidence was captured within the geofence
    - The evidence hash fingerprint for transparency
    """
    try:
        result = ResolutionProofService.verify_evidence(grievance_id, db)
        return VerificationResponse(**result)
    except Exception as e:
        logger.error(f"Error verifying grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify resolution")


# ============================================================================
# EVIDENCE RETRIEVAL
# ============================================================================

@router.get("/evidence/{grievance_id}")
def get_evidence(
    grievance_id: int,
    db: Session = Depends(get_db)
):
    """
    Get evidence details for a grievance (public endpoint).

    Returns all evidence records with their integrity status.
    """
    try:
        records = ResolutionProofService.get_evidence_for_grievance(grievance_id, db)
        return {
            "grievance_id": grievance_id,
            "evidence": records,
            "total": len(records)
        }
    except Exception as e:
        logger.error(f"Error fetching evidence for grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch evidence")


# ============================================================================
# AUDIT TRAIL
# ============================================================================

@router.get("/audit-log/{grievance_id}", response_model=AuditTrailResponse)
def get_audit_log(
    grievance_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the append-only audit trail for a grievance's resolution evidence.

    Provides complete transparency into evidence lifecycle.
    """
    try:
        entries = ResolutionProofService.get_audit_trail(grievance_id, db)
        return AuditTrailResponse(
            grievance_id=grievance_id,
            audit_entries=entries,
            total_entries=len(entries)
        )
    except Exception as e:
        logger.error(f"Error fetching audit log for grievance {grievance_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to fetch audit log")


# ============================================================================
# DUPLICATE / FRAUD DETECTION
# ============================================================================

from backend.models import ResolutionEvidence

@router.get("/{evidence_id}/blockchain-verify", response_model=BlockchainVerificationResponse)
def verify_evidence_blockchain(
    evidence_id: int,
    db: Session = Depends(get_db)
):
    """
    Verify the cryptographic integrity of a resolution evidence record using blockchain-style chaining.
    Optimized: Uses previous_integrity_hash column for O(1) verification.
    """
    try:
        evidence = db.query(ResolutionEvidence).filter(ResolutionEvidence.id == evidence_id).first()

        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")

        # Determine previous hash (O(1) from stored column)
        prev_hash = evidence.previous_integrity_hash or ""

        # Chaining logic: hash(evidence_hash|token_id|gps_latitude|gps_longitude|prev_hash)
        # Re-derive token_id for hash (it's in metadata_bundle)
        token_uuid = evidence.metadata_bundle.get("token_id", "")
        hash_content = f"{evidence.evidence_hash}|{token_uuid}|{evidence.gps_latitude}|{evidence.gps_longitude}|{prev_hash}"
        computed_hash = ResolutionProofService._sign_payload(hash_content)

        is_valid = (computed_hash == evidence.integrity_hash)

        if is_valid:
            message = "Integrity verified. This evidence record is cryptographically sealed and part of a secure chain."
        else:
            message = "Integrity check failed! The evidence data does not match its cryptographic seal."

        return BlockchainVerificationResponse(
            is_valid=is_valid,
            current_hash=evidence.integrity_hash,
            computed_hash=computed_hash,
            message=message
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying evidence blockchain for {evidence_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify evidence integrity")


@router.post("/flag-duplicate", response_model=DuplicateCheckResponse)
def flag_duplicate_evidence(
    evidence_hash: str,
    db: Session = Depends(get_db)
):
    """
    Check for and flag duplicate evidence hashes across grievances.

    Used internally to detect media reuse and trigger escalation.
    """
    try:
        result = ResolutionProofService.check_and_flag_duplicates(evidence_hash, db)
        return DuplicateCheckResponse(**result)
    except Exception as e:
        logger.error(f"Error checking duplicates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to check for duplicates")


# ============================================================================
# BLOCKCHAIN VERIFICATION (O(1))
# ============================================================================

@router.get("/{evidence_id}/blockchain-verify", response_model=BlockchainVerificationResponse)
def verify_evidence_blockchain(
    evidence_id: int,
    db: Session = Depends(get_db)
):
    """
    Verify the cryptographic integrity of an individual resolution evidence record.
    Optimized: Uses previous_integrity_hash column for O(1) verification.
    """
    try:
        from backend.models import ResolutionEvidence
        evidence = db.query(
            ResolutionEvidence.evidence_hash,
            ResolutionEvidence.gps_latitude,
            ResolutionEvidence.gps_longitude,
            ResolutionEvidence.integrity_hash,
            ResolutionEvidence.previous_integrity_hash
        ).filter(ResolutionEvidence.id == evidence_id).first()

        if not evidence:
            raise HTTPException(status_code=404, detail="Evidence not found")

        # Determine previous hash (O(1) from stored column)
        prev_hash = evidence.previous_integrity_hash or ""

        # Recompute hash based on current data and previous hash
        # Chaining logic: HMAC-SHA256(evidence_hash|gps_lat|gps_lon|prev_hash)
        hash_content = f"{evidence.evidence_hash}|{evidence.gps_latitude}|{evidence.gps_longitude}|{prev_hash}"
        computed_hash = ResolutionProofService._sign_payload(hash_content)

        if evidence.integrity_hash is None:
            # Legacy or unsealed record
            is_valid = False
            message = "No integrity hash present; cryptographic integrity cannot be verified."
        else:
            is_valid = (computed_hash == evidence.integrity_hash)
            message = (
                "Integrity verified. This evidence record is cryptographically sealed."
                if is_valid
                else "Integrity check failed! The evidence data does not match its cryptographic seal."
            )
        return BlockchainVerificationResponse(
            is_valid=is_valid,
            current_hash=evidence.integrity_hash,
            computed_hash=computed_hash,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying evidence blockchain for {evidence_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify evidence integrity")
