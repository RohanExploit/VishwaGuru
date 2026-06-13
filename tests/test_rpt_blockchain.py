import os
import sys
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta

# Add backend to path
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, backend_path)

from backend.resolution_proof_service import ResolutionProofService
from backend.models import ResolutionProofToken, Grievance, GrievanceStatus
from backend.cache import rpt_last_hash_cache

class TestRPTBlockchain:
    @pytest.fixture(autouse=True)
    def setup_cache(self):
        rpt_last_hash_cache.clear()
        yield
        rpt_last_hash_cache.clear()

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    @patch('backend.resolution_proof_service.get_auth_config')
    def test_rpt_integrity_chaining(self, mock_auth_config, mock_signing_key):
        mock_signing_key.return_value = "test-secret"
        mock_auth_config.return_value.secret_key = "test-secret"

        db = MagicMock()

        # Mock grievance
        grievance = Grievance(
            id=1,
            status=GrievanceStatus.OPEN,
            latitude=19.0760,
            longitude=72.8777
        )

        # First call: cache miss, DB empty
        db.query.return_value.filter.return_value.first.side_effect = [grievance, None]
        db.query.return_value.order_by.return_value.first.return_value = None

        token1 = ResolutionProofService.generate_proof_token(
            grievance_id=1,
            authority_email="test@example.com",
            db=db
        )

        assert token1.previous_integrity_hash == ""
        assert token1.integrity_hash is not None

        # Verify cache was updated
        assert rpt_last_hash_cache.get("last_hash") == token1.integrity_hash

        # Second call: should use cache
        db.query.return_value.filter.return_value.first.side_effect = [grievance]

        token2 = ResolutionProofService.generate_proof_token(
            grievance_id=1,
            authority_email="test2@example.com",
            db=db
        )

        assert token2.previous_integrity_hash == token1.integrity_hash
        assert token2.integrity_hash != token1.integrity_hash
        assert rpt_last_hash_cache.get("last_hash") == token2.integrity_hash

    @patch('backend.resolution_proof_service.ResolutionProofService._get_signing_key')
    @patch('backend.resolution_proof_service.get_auth_config')
    def test_rpt_chaining_with_cache_miss(self, mock_auth_config, mock_signing_key):
        mock_signing_key.return_value = "test-secret"
        mock_auth_config.return_value.secret_key = "test-secret"

        db = MagicMock()

        grievance = Grievance(
            id=1,
            status=GrievanceStatus.OPEN,
            latitude=19.0760,
            longitude=72.8777
        )

        # Mock DB returning a previous hash
        prev_hash = "previous-hash-123"
        db.query.return_value.filter.return_value.first.return_value = grievance
        db.query.return_value.order_by.return_value.first.return_value = [prev_hash]

        token = ResolutionProofService.generate_proof_token(
            grievance_id=1,
            authority_email="test@example.com",
            db=db
        )

        assert token.previous_integrity_hash == prev_hash
        assert token.integrity_hash is not None
        assert rpt_last_hash_cache.get("last_hash") == token.integrity_hash
