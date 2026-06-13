"""
Tests for the Verifiable OnGround Resolution System (Issue #292)

Tests:
- Token generation and signature verification
- Token validation (expiry, used, invalid signature)
- Geofence validation (Haversine distance)
- Evidence submission pipeline
- Evidence verification
- Duplicate / fraud detection
- Pydantic schema validation
"""

import os
import sys
import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from unittest.mock import patch, MagicMock

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


# ──────────────────────────────────────────────
# Schema Tests
# ──────────────────────────────────────────────

class TestSchemas:
    """Test Pydantic schemas for resolution proof system."""

    def test_generate_rpt_request_valid(self):
        from backend.schemas import GenerateRPTRequest
        req = GenerateRPTRequest(
            grievance_id=1,
            authority_email="officer@gov.in",
            geofence_radius_meters=200.0
        )
        assert req.grievance_id == 1
        assert req.authority_email == "officer@gov.in"
        assert req.geofence_radius_meters == 200.0

    def test_generate_rpt_request_default_radius(self):
        from backend.schemas import GenerateRPTRequest
        req = GenerateRPTRequest(
            grievance_id=1,
            authority_email="officer@gov.in"
        )
        assert req.geofence_radius_meters == 200.0

    def test_generate_rpt_request_radius_bounds(self):
        from backend.schemas import GenerateRPTRequest
        # Valid: within 50-1000
        req = GenerateRPTRequest(
            grievance_id=1,
            authority_email="officer@gov.in",
            geofence_radius_meters=500.0
        )
        assert req.geofence_radius_meters == 500.0

        # Invalid: below 50
        with pytest.raises(Exception):
            GenerateRPTRequest(
                grievance_id=1,
                authority_email="officer@gov.in",
                geofence_radius_meters=10.0
            )

        # Invalid: above 1000
        with pytest.raises(Exception):
            GenerateRPTRequest(
                grievance_id=1,
                authority_email="officer@gov.in",
                geofence_radius_meters=5000.0
            )

    def test_submit_evidence_request_hash_length(self):
        from backend.schemas import SubmitEvidenceRequest
        valid_hash = "a" * 64  # SHA-256 is 64 hex chars
        req = SubmitEvidenceRequest(
            token_id="test-token",
            evidence_hash=valid_hash,
            gps_latitude=19.0760,
            gps_longitude=72.8777,
            capture_timestamp=datetime.now(timezone.utc)
        )
        assert req.evidence_hash == valid_hash

        # Invalid: too short
        with pytest.raises(Exception):
            SubmitEvidenceRequest(
                token_id="test-token",
                evidence_hash="abc",
                gps_latitude=19.0760,
                gps_longitude=72.8777,
                capture_timestamp=datetime.now(timezone.utc)
            )

        # Invalid: too long
        with pytest.raises(Exception):
            SubmitEvidenceRequest(
                token_id="test-token",
                evidence_hash="a" * 100,
                gps_latitude=19.0760,
                gps_longitude=72.8777,
                capture_timestamp=datetime.now(timezone.utc)
            )

    def test_submit_evidence_gps_bounds(self):
        from backend.schemas import SubmitEvidenceRequest
        # Valid GPS
        req = SubmitEvidenceRequest(
            token_id="test-token",
            evidence_hash="a" * 64,
            gps_latitude=19.0760,
            gps_longitude=72.8777,
            capture_timestamp=datetime.now(timezone.utc)
        )
        assert req.gps_latitude == 19.0760

        # Invalid latitude (> 90)
        with pytest.raises(Exception):
            SubmitEvidenceRequest(
                token_id="test-token",
                evidence_hash="a" * 64,
                gps_latitude=100.0,
                gps_longitude=72.8777,
                capture_timestamp=datetime.now(timezone.utc)
            )

    def test_verification_response(self):
        from backend.schemas import VerificationResponse
        resp = VerificationResponse(
            grievance_id=1,
            is_verified=True,
            verification_status="verified",
            location_match=True,
            evidence_integrity=True,
            evidence_hash="a" * 64,
            evidence_count=1,
            message="Resolution verified"
        )
        assert resp.is_verified is True
        assert resp.verification_status == "verified"

    def test_duplicate_check_response(self):
        from backend.schemas import DuplicateCheckResponse
        resp = DuplicateCheckResponse(
            is_duplicate=True,
            duplicate_grievance_ids=[1, 2, 3],
            message="Duplicate detected"
        )
        assert resp.is_duplicate is True
        assert len(resp.duplicate_grievance_ids) == 3


# ──────────────────────────────────────────────
# Geofence Tests
# ──────────────────────────────────────────────

class TestGeofence:
    """Test Haversine geofence validation."""

    def test_same_location(self):
        from backend.resolution_proof_service import ResolutionProofService
        is_inside, distance = ResolutionProofService.validate_geofence(
            19.0760, 72.8777,  # evidence
            19.0760, 72.8777,  # geofence center
            200.0              # radius
        )
        assert is_inside is True
        assert distance == 0.0

    def test_inside_geofence(self):
        from backend.resolution_proof_service import ResolutionProofService
        # ~50 meters apart (very small offset)
        is_inside, distance = ResolutionProofService.validate_geofence(
            19.0760, 72.8777,
            19.0764, 72.8777,
            200.0
        )
        assert is_inside is True
        assert distance < 200.0

    def test_outside_geofence(self):
        from backend.resolution_proof_service import ResolutionProofService
        # ~1.5 km apart
        is_inside, distance = ResolutionProofService.validate_geofence(
            19.0760, 72.8777,
            19.0900, 72.8777,
            200.0
        )
        assert is_inside is False
        assert distance > 200.0

    def test_edge_case_large_radius(self):
        from backend.resolution_proof_service import ResolutionProofService
        # ~1.5 km apart but with 2 km radius
        is_inside, distance = ResolutionProofService.validate_geofence(
            19.0760, 72.8777,
            19.0900, 72.8777,
            2000.0
        )
        assert is_inside is True

    def test_haversine_known_distance(self):
        from backend.resolution_proof_service import ResolutionProofService
        # Mumbai (19.0760, 72.8777) to Pune (18.5204, 73.8567) ≈ 118-120 km
        _, distance = ResolutionProofService.validate_geofence(
            19.0760, 72.8777,
            18.5204, 73.8567,
            200.0
        )
        assert 115_000 < distance < 125_000  # ~120 km


# ──────────────────────────────────────────────
# Cryptographic Signing Tests
# ──────────────────────────────────────────────

class TestCryptoSigning:
    """Test HMAC-SHA256 signing and verification."""

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_sign_and_verify(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-secret-key-12345"

        payload = json.dumps({"test": "data", "nonce": "abc123"})
        signature = ResolutionProofService._sign_payload(payload)

        assert isinstance(signature, str)
        assert len(signature) == 64  # SHA-256 hex is 64 chars

        # Verify
        assert ResolutionProofService._verify_signature(payload, signature) is True

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_tampered_payload_fails(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-secret-key-12345"

        payload = json.dumps({"test": "data"})
        signature = ResolutionProofService._sign_payload(payload)

        tampered = json.dumps({"test": "tampered_data"})
        assert ResolutionProofService._verify_signature(tampered, signature) is False

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_wrong_signature_fails(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-secret-key-12345"

        payload = json.dumps({"test": "data"})
        wrong_sig = "0" * 64

        assert ResolutionProofService._verify_signature(payload, wrong_sig) is False

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_different_keys_produce_different_sigs(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService

        payload = json.dumps({"test": "data"})

        mock_key.return_value = "key-1"
        sig1 = ResolutionProofService._sign_payload(payload)

        mock_key.return_value = "key-2"
        sig2 = ResolutionProofService._sign_payload(payload)

        assert sig1 != sig2


# ──────────────────────────────────────────────
# Token Lifecycle Tests (with mocked DB)
# ──────────────────────────────────────────────

class TestTokenLifecycle:
    """Test token generation and validation with mocked database."""

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_generate_token_no_grievance(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-key"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            ResolutionProofService.generate_proof_token(
                grievance_id=999,
                authority_email="officer@gov.in",
                db=db
            )

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_generate_token_already_resolved(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        from backend.models import GrievanceStatus
        mock_key.return_value = "test-key"

        mock_grievance = MagicMock()
        mock_grievance.id = 1
        mock_grievance.status = GrievanceStatus.RESOLVED
        mock_grievance.latitude = 19.0760
        mock_grievance.longitude = 72.8777

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_grievance

        with pytest.raises(ValueError, match="already resolved"):
            ResolutionProofService.generate_proof_token(
                grievance_id=1,
                authority_email="officer@gov.in",
                db=db
            )

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_generate_token_no_location(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        from backend.models import GrievanceStatus
        mock_key.return_value = "test-key"

        mock_grievance = MagicMock()
        mock_grievance.id = 1
        mock_grievance.status = GrievanceStatus.OPEN
        mock_grievance.latitude = None
        mock_grievance.longitude = None

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_grievance

        with pytest.raises(ValueError, match="no location data"):
            ResolutionProofService.generate_proof_token(
                grievance_id=1,
                authority_email="officer@gov.in",
                db=db
            )

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_validate_token_expired(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-key"

        mock_token = MagicMock()
        mock_token.token_id = "test-token-id"
        mock_token.is_used = False
        mock_token.valid_until = datetime.now(timezone.utc) - timedelta(hours=1)
        mock_token.valid_from = datetime.now(timezone.utc) - timedelta(hours=2)

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_token

        with pytest.raises(ValueError, match="expired"):
            ResolutionProofService.validate_token("test-token-id", db)

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_validate_token_already_used(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-key"

        mock_token = MagicMock()
        mock_token.token_id = "test-token-id"
        mock_token.is_used = True

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = mock_token

        with pytest.raises(ValueError, match="already been used"):
            ResolutionProofService.validate_token("test-token-id", db)

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    def test_validate_token_not_found(self, mock_key):
        from backend.resolution_proof_service import ResolutionProofService
        mock_key.return_value = "test-key"

        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = None

        with pytest.raises(ValueError, match="not found"):
            ResolutionProofService.validate_token("nonexistent", db)


# ──────────────────────────────────────────────
# Model Tests
# ──────────────────────────────────────────────

class TestModels:
    """Test that new models are importable and have correct fields."""

    def test_verification_status_enum(self):
        from backend.models import VerificationStatus
        assert VerificationStatus.PENDING.value == "pending"
        assert VerificationStatus.VERIFIED.value == "verified"
        assert VerificationStatus.FLAGGED.value == "flagged"
        assert VerificationStatus.FRAUD_DETECTED.value == "fraud_detected"

    def test_resolution_proof_token_model(self):
        from backend.models import ResolutionProofToken
        # Check key columns exist
        assert hasattr(ResolutionProofToken, 'token_id')
        assert hasattr(ResolutionProofToken, 'grievance_id')
        assert hasattr(ResolutionProofToken, 'authority_email')
        assert hasattr(ResolutionProofToken, 'geofence_latitude')
        assert hasattr(ResolutionProofToken, 'geofence_longitude')
        assert hasattr(ResolutionProofToken, 'geofence_radius_meters')
        assert hasattr(ResolutionProofToken, 'valid_from')
        assert hasattr(ResolutionProofToken, 'valid_until')
        assert hasattr(ResolutionProofToken, 'nonce')
        assert hasattr(ResolutionProofToken, 'token_signature')
        assert hasattr(ResolutionProofToken, 'is_used')

    def test_resolution_evidence_model(self):
        from backend.models import ResolutionEvidence
        assert hasattr(ResolutionEvidence, 'evidence_hash')
        assert hasattr(ResolutionEvidence, 'gps_latitude')
        assert hasattr(ResolutionEvidence, 'gps_longitude')
        assert hasattr(ResolutionEvidence, 'capture_timestamp')
        assert hasattr(ResolutionEvidence, 'device_fingerprint_hash')
        assert hasattr(ResolutionEvidence, 'metadata_bundle')
        assert hasattr(ResolutionEvidence, 'server_signature')
        assert hasattr(ResolutionEvidence, 'verification_status')

    def test_evidence_audit_log_model(self):
        from backend.models import EvidenceAuditLog
        assert hasattr(EvidenceAuditLog, 'evidence_id')
        assert hasattr(EvidenceAuditLog, 'action')
        assert hasattr(EvidenceAuditLog, 'details')
        assert hasattr(EvidenceAuditLog, 'actor_email')
        assert hasattr(EvidenceAuditLog, 'timestamp')


# ──────────────────────────────────────────────
# Hash Utility Tests
# ──────────────────────────────────────────────

class TestHashUtilities:
    """Test SHA-256 hashing utilities."""

    def test_sha256_produces_correct_length(self):
        data = b"test evidence image data"
        hash_hex = hashlib.sha256(data).hexdigest()
        assert len(hash_hex) == 64

    def test_sha256_deterministic(self):
        data = b"same data produces same hash"
        h1 = hashlib.sha256(data).hexdigest()
        h2 = hashlib.sha256(data).hexdigest()
        assert h1 == h2

    def test_sha256_different_data_different_hash(self):
        h1 = hashlib.sha256(b"data1").hexdigest()
        h2 = hashlib.sha256(b"data2").hexdigest()
        assert h1 != h2

    def test_sha256_single_bit_change(self):
        """A single byte change should produce completely different hash."""
        h1 = hashlib.sha256(b"evidence_photo_a").hexdigest()
        h2 = hashlib.sha256(b"evidence_photo_b").hexdigest()
        # Count differing characters
        diff = sum(1 for a, b in zip(h1, h2) if a != b)
        assert diff > 10  # Should be substantially different


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
