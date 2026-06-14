import os
import json
import pytest
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from backend.database import Base
from backend.models import Issue, EscalationAudit, EscalationReason, Grievance, SeverityLevel, JurisdictionLevel, GrievanceStatus, Jurisdiction
from backend.civic_intelligence import CivicIntelligenceEngine
from backend.adaptive_weights import AdaptiveWeights

# Test Data
MOCK_WEIGHTS = {
    "category_multipliers": {
        "pothole": 1.0,
        "garbage": 1.0
    },
    "duplicate_search_radius": 50.0,
    "severity_keywords": {},
    "urgency_patterns": [],
    "category_keywords": {}
}

@pytest.fixture
def temp_dirs():
    # Create temp directories for snapshots and weights
    temp_dir = tempfile.mkdtemp()
    weights_file = os.path.join(temp_dir, "modelWeights.json")
    snapshots_dir = os.path.join(temp_dir, "dailySnapshots")
    os.makedirs(snapshots_dir)

    # Initialize weights
    with open(weights_file, 'w') as f:
        json.dump(MOCK_WEIGHTS, f)

    yield temp_dir, weights_file, snapshots_dir

    shutil.rmtree(temp_dir)

@pytest.fixture
def db_session():
    # In-memory SQLite DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_daily_civic_intelligence_cycle(temp_dirs, db_session):
    temp_dir, weights_file, snapshots_dir = temp_dirs

    # Patch paths to use temp directory
    with patch("backend.adaptive_weights.DATA_FILE", weights_file), \
         patch("backend.civic_intelligence.SNAPSHOT_DIR", snapshots_dir), \
         patch("backend.civic_intelligence.SessionLocal", return_value=db_session):

        # Reload adaptive weights to pick up temp file
        weights_system = AdaptiveWeights()
        weights_system._weights = None # Force reload
        weights_system._load_weights()

        assert weights_system.get_category_multipliers()["pothole"] == 1.0
        assert weights_system.get_duplicate_search_radius() == 50.0

        # --- 1. Setup Data ---
        now = datetime.now(timezone.utc)

        # A. Create scattered issues to trigger "many issues, no clusters" -> increase radius
        # Create 51 issues far apart so they don't form clusters (TrendAnalyzer requires >=3 items per cluster)
        # But total volume > 50 triggers radius increase if no clusters found.
        for i in range(51):
            issue = Issue(
                description=f"Scattered issue {i}",
                category="pothole",
                latitude=18.5204 + (i * 0.005), # ~500m apart
                longitude=73.8567 + (i * 0.005),
                created_at=now - timedelta(hours=2)
            )
            db_session.add(issue)

        # B. Create manual severity upgrades (to trigger weight increase)
        # We need Grievances linked to EscalationAudits
        # Create a Jurisdiction first
        jurisdiction = Jurisdiction(
             level=JurisdictionLevel.LOCAL,
             geographic_coverage={"city": "Pune"},
             responsible_authority="PMC",
             default_sla_hours=48
        )
        db_session.add(jurisdiction)
        db_session.flush()

        for i in range(4): # 4 upgrades > 3 threshold
            grievance = Grievance(
                category="pothole",
                severity=SeverityLevel.LOW,
                current_jurisdiction_id=jurisdiction.id,
                assigned_authority="PMC",
                sla_deadline=now + timedelta(days=2),
                status=GrievanceStatus.OPEN
            )
            db_session.add(grievance)
            db_session.flush()

            audit = EscalationAudit(
                grievance_id=grievance.id,
                previous_authority="Bot",
                new_authority="Admin",
                reason=EscalationReason.SEVERITY_UPGRADE,
                timestamp=now - timedelta(hours=5)
            )
            db_session.add(audit)

        db_session.commit()

        # --- 2. Run Cycle ---
        engine = CivicIntelligenceEngine()
        engine.run_daily_cycle()

        # --- 3. Verify Results ---

        # A. Check Snapshot creation
        snapshot_files = os.listdir(snapshots_dir)
        assert len(snapshot_files) == 1, "Snapshot file was not created"

        with open(os.path.join(snapshots_dir, snapshot_files[0]), 'r') as f:
            snapshot = json.load(f)

        # Verify Index Data
        assert snapshot["civic_index"]["new_issues_count"] >= 51

        # Verify Weight Updates Logged
        assert "pothole" in snapshot["weight_updates"]
        assert snapshot["weight_updates"]["pothole"] == 4

        # B. Check Weight Updates Persistence
        # Force reload to verify persistence
        weights_system._last_loaded = 0 # Force reload
        weights_system._load_weights()

        # Severity weight for "pothole" should increase
        new_pothole_weight = weights_system.get_category_multipliers()["pothole"]
        assert new_pothole_weight > 1.0, f"Pothole weight should increase from 1.0, got {new_pothole_weight}"

        # Radius should increase because of clustering (> 5 clusters)
        new_radius = weights_system.get_duplicate_search_radius()
        assert new_radius > 50.0, f"Radius should have increased from 50.0, got {new_radius}"
