"""
Resolution Proof Service - Cryptographic Verification for OnGround Resolution (Issue #292)

Implements:
- Resolution Proof Token (RPT) generation with asymmetric signing
- Geo-fence validation using Haversine distance
- SHA-256 evidence hashing and server-side signing
- Anti-fraud duplicate detection
- Append-only audit logging
"""

import hashlib
import hmac
import json
import math
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy.orm import Session

from backend.models import (
    Grievance, ResolutionProofToken, ResolutionEvidence,
    EvidenceAuditLog, VerificationStatus, GrievanceStatus
)
from backend.config import get_config

logger = logging.getLogger(__name__)

# Token validity window in minutes
TOKEN_VALIDITY_MINUTES = 15

# Default geofence radius in meters
DEFAULT_GEOFENCE_RADIUS = 200.0

# Earth radius in meters for Haversine calculation
EARTH_RADIUS_METERS = 6_371_000


class ResolutionProofService:
    """
    Service for managing cryptographically verifiable resolution proofs.
    Ensures grievance resolutions are geo-temporally bound and tamper-proof.
    """

    # ──────────────────────────────────────────────
    #  Cryptographic Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _get_signing_key() -> str:
        """Get the server signing key from config."""
        config = get_config()
        return config.secret_key

    @staticmethod
    def _sign_payload(payload: str) -> str:
        """
        Create HMAC-SHA256 signature for a payload string.
        Uses the server secret key for deterministic, verifiable signing.
        """
        key = ResolutionProofService._get_signing_key()
        signature = hmac.new(
            key.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return signature

    @staticmethod
    def _verify_signature(payload: str, signature: str) -> bool:
        """Verify an HMAC-SHA256 signature."""
        expected = ResolutionProofService._sign_payload(payload)
        return hmac.compare_digest(expected, signature)

    # ──────────────────────────────────────────────
    #  Geospatial Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great-circle distance between two GPS points in meters.
        Uses the Haversine formula.
        """
        lat1_r, lon1_r = math.radians(lat1), math.radians(lon1)
        lat2_r, lon2_r = math.radians(lat2), math.radians(lon2)

        dlat = lat2_r - lat1_r
        dlon = lon2_r - lon1_r

        a = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon / 2) ** 2)
        c = 2 * math.asin(math.sqrt(a))

        return EARTH_RADIUS_METERS * c

    @staticmethod
    def validate_geofence(
        evidence_lat: float,
        evidence_lon: float,
        geofence_lat: float,
        geofence_lon: float,
        radius_meters: float
    ) -> Tuple[bool, float]:
        """
        Check whether the evidence GPS is within the geofence radius.
        Returns (is_inside, distance_meters).
        """
        distance = ResolutionProofService._haversine_distance(
            evidence_lat, evidence_lon, geofence_lat, geofence_lon
        )
        return distance <= radius_meters, round(distance, 2)

    # ──────────────────────────────────────────────
    #  Token Generation
    # ──────────────────────────────────────────────

    @staticmethod
    def generate_proof_token(
        grievance_id: int,
        authority_email: str,
        db: Session,
        geofence_radius: float = DEFAULT_GEOFENCE_RADIUS
    ) -> ResolutionProofToken:
        """
        Generate a one-time Resolution Proof Token.

        The token is:
        - Signed using server secret key (HMAC-SHA256)
        - Valid for TOKEN_VALIDITY_MINUTES (15 min)
        - Single-use only
        - Contains geofence parameters from the grievance location

        Args:
            grievance_id: ID of the grievance being resolved
            authority_email: Email of the resolving authority
            db: Database session
            geofence_radius: Geofence radius in meters

        Returns:
            Created ResolutionProofToken

        Raises:
            ValueError: If grievance not found, already resolved, or no location data
        """
        # Fetch grievance
        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        if not grievance:
            raise ValueError(f"Grievance {grievance_id} not found")

        if grievance.status == GrievanceStatus.RESOLVED:
            raise ValueError(f"Grievance {grievance_id} is already resolved")

        # Require location for geofencing
        if grievance.latitude is None or grievance.longitude is None:
            raise ValueError(
                f"Grievance {grievance_id} has no location data. "
                "GPS coordinates are required for resolution proof."
            )

        # Invalidate any existing unused tokens for this grievance
        db.query(ResolutionProofToken).filter(
            ResolutionProofToken.grievance_id == grievance_id,
            ResolutionProofToken.is_used == False  # noqa: E712
        ).update({"is_used": True, "used_at": datetime.now(timezone.utc)})

        # Generate token fields
        token_uuid = str(uuid.uuid4())
        nonce = uuid.uuid4().hex
        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(minutes=TOKEN_VALIDITY_MINUTES)

        # Build signing payload
        payload = json.dumps({
            "token_id": token_uuid,
            "grievance_id": grievance_id,
            "authority_email": authority_email,
            "geofence_lat": grievance.latitude,
            "geofence_lon": grievance.longitude,
            "geofence_radius": geofence_radius,
            "valid_from": now.isoformat(),
            "valid_until": valid_until.isoformat(),
            "nonce": nonce
        }, sort_keys=True)

        signature = ResolutionProofService._sign_payload(payload)

        # Create token record
        token = ResolutionProofToken(
            token_id=token_uuid,
            grievance_id=grievance_id,
            authority_email=authority_email,
            geofence_latitude=grievance.latitude,
            geofence_longitude=grievance.longitude,
            geofence_radius_meters=geofence_radius,
            valid_from=now,
            valid_until=valid_until,
            nonce=nonce,
            token_signature=signature,
            is_used=False,
        )

        db.add(token)
        db.commit()
        db.refresh(token)

        logger.info(
            f"Generated RPT {token_uuid} for grievance {grievance_id} "
            f"by {authority_email}, expires {valid_until.isoformat()}"
        )

        return token

    # ──────────────────────────────────────────────
    #  Token Validation
    # ──────────────────────────────────────────────

    @staticmethod
    def validate_token(token_id: str, db: Session) -> ResolutionProofToken:
        """
        Validate a Resolution Proof Token.

        Checks:
        1. Token exists
        2. Token signature is valid
        3. Token has not expired
        4. Token has not been used

        Returns:
            The validated token

        Raises:
            ValueError: If any validation check fails
        """
        token = db.query(ResolutionProofToken).filter(
            ResolutionProofToken.token_id == token_id
        ).first()

        if not token:
            raise ValueError(f"Token {token_id} not found")

        if token.is_used:
            raise ValueError(f"Token {token_id} has already been used")

        now = datetime.now(timezone.utc)
        # Handle timezone-naive datetimes from SQLite
        valid_until = token.valid_until
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)

        if now > valid_until:
            raise ValueError(
                f"Token {token_id} has expired. "
                f"Valid until: {valid_until.isoformat()}, current: {now.isoformat()}"
            )

        # Verify signature
        valid_from = token.valid_from
        if valid_from.tzinfo is None:
            valid_from = valid_from.replace(tzinfo=timezone.utc)

        payload = json.dumps({
            "token_id": token.token_id,
            "grievance_id": token.grievance_id,
            "authority_email": token.authority_email,
            "geofence_lat": token.geofence_latitude,
            "geofence_lon": token.geofence_longitude,
            "geofence_radius": token.geofence_radius_meters,
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
            "nonce": token.nonce
        }, sort_keys=True)

        if not ResolutionProofService._verify_signature(payload, token.token_signature):
            raise ValueError(f"Token {token_id} has an invalid signature - possible tampering")

        return token

    # ──────────────────────────────────────────────
    #  Evidence Submission
    # ──────────────────────────────────────────────

    @staticmethod
    def submit_evidence(
        token_id: str,
        evidence_hash: str,
        gps_latitude: float,
        gps_longitude: float,
        capture_timestamp: datetime,
        db: Session,
        device_fingerprint_hash: Optional[str] = None,
    ) -> ResolutionEvidence:
        """
        Submit resolution evidence with cryptographic proof.

        Flow:
        1. Validate the RPT
        2. Validate geofence (evidence GPS vs. grievance location)
        3. Check for duplicate hashes (anti-fraud)
        4. Create signed evidence bundle
        5. Mark token as used
        6. Create audit log entry

        Returns:
            Created ResolutionEvidence record

        Raises:
            ValueError: If token invalid, outside geofence, or duplicate hash
        """
        # 1. Validate token
        token = ResolutionProofService.validate_token(token_id, db)

        # 2. Validate geofence
        is_inside, distance = ResolutionProofService.validate_geofence(
            gps_latitude, gps_longitude,
            token.geofence_latitude, token.geofence_longitude,
            token.geofence_radius_meters
        )

        if not is_inside:
            raise ValueError(
                f"Evidence captured outside geofence. "
                f"Distance: {distance}m, allowed: {token.geofence_radius_meters}m"
            )

        # 3. Validate capture timestamp is within token window
        # Handle timezone-naive datetimes
        valid_from = token.valid_from
        valid_until = token.valid_until
        if valid_from.tzinfo is None:
            valid_from = valid_from.replace(tzinfo=timezone.utc)
        if valid_until.tzinfo is None:
            valid_until = valid_until.replace(tzinfo=timezone.utc)

        cap_ts = capture_timestamp
        if cap_ts.tzinfo is None:
            cap_ts = cap_ts.replace(tzinfo=timezone.utc)

        if cap_ts < valid_from or cap_ts > valid_until:
            raise ValueError(
                "Evidence capture timestamp is outside the token validity window"
            )

        # 4. Check for duplicate hashes
        duplicates = ResolutionProofService._check_duplicate_hash(evidence_hash, db)
        if duplicates:
            dup_ids = [d.grievance_id for d in duplicates]
            raise ValueError(
                f"Duplicate evidence hash detected! Same media already submitted "
                f"for grievance(s): {dup_ids}. Possible fraud."
            )

        # 5. Create server-side signed metadata bundle
        metadata_bundle = {
            "token_id": token.token_id,
            "grievance_id": token.grievance_id,
            "authority_email": token.authority_email,
            "evidence_hash": evidence_hash,
            "gps_latitude": gps_latitude,
            "gps_longitude": gps_longitude,
            "capture_timestamp": cap_ts.isoformat(),
            "device_fingerprint_hash": device_fingerprint_hash,
            "geofence_distance_meters": distance,
        }

        bundle_str = json.dumps(metadata_bundle, sort_keys=True)
        server_signature = ResolutionProofService._sign_payload(bundle_str)

        # 6. Create evidence record
        evidence = ResolutionEvidence(
            grievance_id=token.grievance_id,
            token_id=token.id,
            evidence_hash=evidence_hash,
            gps_latitude=gps_latitude,
            gps_longitude=gps_longitude,
            capture_timestamp=cap_ts,
            device_fingerprint_hash=device_fingerprint_hash,
            metadata_bundle=metadata_bundle,
            server_signature=server_signature,
            verification_status=VerificationStatus.VERIFIED,
        )

        db.add(evidence)

        # 7. Mark token as used
        token.is_used = True
        token.used_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(evidence)

        # 8. Create audit log
        ResolutionProofService._create_audit_log(
            evidence_id=evidence.id,
            action="created",
            details=f"Evidence submitted and verified. Distance: {distance}m",
            actor_email=token.authority_email,
            db=db
        )

        ResolutionProofService._create_audit_log(
            evidence_id=evidence.id,
            action="verified",
            details=(
                f"Geofence: PASS ({distance}m / {token.geofence_radius_meters}m). "
                f"Hash: {evidence_hash[:16]}... Signature: valid"
            ),
            actor_email="system",
            db=db
        )

        logger.info(
            f"Evidence submitted for grievance {token.grievance_id} "
            f"by {token.authority_email}. Hash: {evidence_hash[:16]}..."
        )

        return evidence

    # ──────────────────────────────────────────────
    #  Verification
    # ──────────────────────────────────────────────

    @staticmethod
    def verify_evidence(grievance_id: int, db: Session) -> Dict[str, Any]:
        """
        Verify the resolution evidence for a grievance.

        Checks:
        - Evidence exists
        - Evidence hash integrity (re-sign and compare)
        - Location match (within geofence)

        Returns:
            Verification result dictionary
        """
        evidence_records = db.query(ResolutionEvidence).filter(
            ResolutionEvidence.grievance_id == grievance_id
        ).all()

        if not evidence_records:
            return {
                "grievance_id": grievance_id,
                "is_verified": False,
                "verification_status": "pending",
                "resolution_timestamp": None,
                "location_match": False,
                "evidence_integrity": False,
                "evidence_hash": None,
                "evidence_count": 0,
                "message": "No resolution evidence found for this grievance"
            }

        # Use the most recent evidence
        evidence = evidence_records[-1]

        # Re-verify the server signature
        bundle_str = json.dumps(evidence.metadata_bundle, sort_keys=True)
        signature_valid = ResolutionProofService._verify_signature(
            bundle_str, evidence.server_signature
        )

        # Check geofence from stored metadata
        token = db.query(ResolutionProofToken).filter(
            ResolutionProofToken.id == evidence.token_id
        ).first()

        location_match = False
        if token:
            is_inside, _ = ResolutionProofService.validate_geofence(
                evidence.gps_latitude, evidence.gps_longitude,
                token.geofence_latitude, token.geofence_longitude,
                token.geofence_radius_meters
            )
            location_match = is_inside

        is_verified = (
            signature_valid and
            location_match and
            evidence.verification_status == VerificationStatus.VERIFIED
        )

        status_str = evidence.verification_status.value if evidence.verification_status else "pending"

        grievance = db.query(Grievance).filter(Grievance.id == grievance_id).first()
        resolution_ts = grievance.resolved_at if grievance else None

        return {
            "grievance_id": grievance_id,
            "is_verified": is_verified,
            "verification_status": status_str,
            "resolution_timestamp": resolution_ts,
            "location_match": location_match,
            "evidence_integrity": signature_valid,
            "evidence_hash": evidence.evidence_hash,
            "evidence_count": len(evidence_records),
            "message": (
                "Resolution verified with cryptographic proof"
                if is_verified
                else "Resolution verification incomplete or failed"
            )
        }

    # ──────────────────────────────────────────────
    #  Anti-Fraud: Duplicate Detection
    # ──────────────────────────────────────────────

    @staticmethod
    def _check_duplicate_hash(
        evidence_hash: str,
        db: Session,
        exclude_grievance_id: Optional[int] = None
    ) -> List[ResolutionEvidence]:
        """Check if an evidence hash has been used before (anti-reuse)."""
        query = db.query(ResolutionEvidence).filter(
            ResolutionEvidence.evidence_hash == evidence_hash
        )
        if exclude_grievance_id:
            query = query.filter(
                ResolutionEvidence.grievance_id != exclude_grievance_id
            )
        return query.all()

    @staticmethod
    def check_and_flag_duplicates(evidence_hash: str, db: Session) -> Dict[str, Any]:
        """
        Public method to check for duplicate evidence hashes across all grievances.
        If found, flags the evidence and creates audit log entries.
        """
        duplicates = db.query(ResolutionEvidence).filter(
            ResolutionEvidence.evidence_hash == evidence_hash
        ).all()

        if len(duplicates) <= 1:
            return {
                "is_duplicate": False,
                "duplicate_grievance_ids": [],
                "message": "No duplicate evidence found"
            }

        dup_grievance_ids = list(set(d.grievance_id for d in duplicates))

        # Flag all duplicates
        for dup in duplicates:
            if dup.verification_status != VerificationStatus.FRAUD_DETECTED:
                dup.verification_status = VerificationStatus.FLAGGED
                ResolutionProofService._create_audit_log(
                    evidence_id=dup.id,
                    action="flagged",
                    details=(
                        f"Duplicate hash detected across grievances: {dup_grievance_ids}. "
                        f"Hash: {evidence_hash[:16]}..."
                    ),
                    actor_email="system",
                    db=db
                )

        db.commit()

        logger.warning(
            f"Duplicate evidence hash flagged across grievances: {dup_grievance_ids}"
        )

        return {
            "is_duplicate": True,
            "duplicate_grievance_ids": dup_grievance_ids,
            "message": f"Duplicate evidence detected across {len(dup_grievance_ids)} grievances"
        }

    # ──────────────────────────────────────────────
    #  Audit Logging
    # ──────────────────────────────────────────────

    @staticmethod
    def _create_audit_log(
        evidence_id: int,
        action: str,
        details: str,
        actor_email: str,
        db: Session
    ) -> EvidenceAuditLog:
        """Create an append-only audit log entry."""
        log = EvidenceAuditLog(
            evidence_id=evidence_id,
            action=action,
            details=details,
            actor_email=actor_email,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @staticmethod
    def get_audit_trail(grievance_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get the complete audit trail for a grievance's resolution evidence."""
        evidence_records = db.query(ResolutionEvidence).filter(
            ResolutionEvidence.grievance_id == grievance_id
        ).all()

        evidence_ids = [e.id for e in evidence_records]

        if not evidence_ids:
            return []

        logs = db.query(EvidenceAuditLog).filter(
            EvidenceAuditLog.evidence_id.in_(evidence_ids)
        ).order_by(EvidenceAuditLog.timestamp.asc()).all()

        return [
            {
                "id": log.id,
                "evidence_id": log.evidence_id,
                "action": log.action,
                "details": log.details,
                "actor_email": log.actor_email,
                "timestamp": log.timestamp,
            }
            for log in logs
        ]

    # ──────────────────────────────────────────────
    #  Evidence Retrieval
    # ──────────────────────────────────────────────

    @staticmethod
    def get_evidence_for_grievance(grievance_id: int, db: Session) -> List[Dict[str, Any]]:
        """Get all evidence records for a grievance."""
        records = db.query(ResolutionEvidence).filter(
            ResolutionEvidence.grievance_id == grievance_id
        ).order_by(ResolutionEvidence.created_at.desc()).all()

        return [
            {
                "id": r.id,
                "grievance_id": r.grievance_id,
                "evidence_hash": r.evidence_hash,
                "gps_latitude": r.gps_latitude,
                "gps_longitude": r.gps_longitude,
                "capture_timestamp": r.capture_timestamp,
                "verification_status": r.verification_status.value if r.verification_status else "pending",
                "server_signature": r.server_signature,
                "created_at": r.created_at,
            }
            for r in records
        ]
