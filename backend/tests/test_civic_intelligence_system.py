import pytest
import os
import json
import time
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock

from backend.models import Base, Issue, EscalationAudit, EscalationReason, Grievance, SeverityLevel, GrievanceStatus, Jurisdiction, JurisdictionLevel
from backend.civic_intelligence import civic_intelligence_engine, SNAPSHOT_DIR
from backend.adaptive_weights import AdaptiveWeights

# Test DB Setup
TEST_DB_URL = "sqlite:///./test_system.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_system.db"):
            os.remove("./test_system.db")

@pytest.fixture
def mock_snapshot_dir(tmp_path):
    # Override SNAPSHOT_DIR
    snapshot_dir = tmp_path / "snapshots"
    os.makedirs(snapshot_dir, exist_ok=True)
    with patch("backend.civic_intelligence.SNAPSHOT_DIR", str(snapshot_dir)):
        yield str(snapshot_dir)

@pytest.fixture
def mock_weights_file(tmp_path):
    # Create a temporary weights file
    weights_file = tmp_path / "modelWeights.json"
    initial_weights = {
        "severity_keywords": {"critical": ["fire"]},
        "category_multipliers": {"Fire": 1.0, "Pothole": 1.0},
        "duplicate_search_radius": 50.0,
        "category_keywords": {"Fire": ["fire"]},
        "urgency_patterns": []
    }
    with open(weights_file, "w") as f:
        json.dump(initial_weights, f)

    # Patch DATA_FILE in adaptive_weights
    with patch("backend.adaptive_weights.DATA_FILE", str(weights_file)):
        # Reset singleton to ensure it loads from new file
        AdaptiveWeights._instance = None
        # Initialize
        AdaptiveWeights()
        yield str(weights_file)
        # Cleanup
        AdaptiveWeights._instance = None

def test_system_daily_cycle(test_db, mock_snapshot_dir, mock_weights_file):
    """
    System test for Civic Intelligence Engine.
    1. Populate DB with issues and audits.
    2. Run the daily cycle.
    3. Verify snapshot creation and content.
    4. Verify weight updates in the JSON file.
    """

    # 1. Setup Data
    now = datetime.now(timezone.utc)

    # Create Issues (Cluster for Potholes to trigger radius increase if logic met)
    # 6 Potholes very close to each other
    for i in range(6):
        issue = Issue(
            description=f"Pothole {i}",
            category="Pothole",
            latitude=10.0001 + (i * 0.0001), # Very close
            longitude=20.0001,
            created_at=now,
            status="open",
            integrity_hash="hash",
            reference_id=f"ref-{i}"
        )
        test_db.add(issue)

    # Create manual upgrades for Fire category to trigger weight increase
    # Need associated Grievances

    # Create Jurisdiction first (required FK)
    j = Jurisdiction(
        level=JurisdictionLevel.LOCAL,
        geographic_coverage={"city": "Test City"},
        responsible_authority="Test Auth",
        default_sla_hours=24
    )
    test_db.add(j)
    test_db.flush()

    for i in range(3):
        g = Grievance(
            issue_id=100+i, # Dummy ID
            category="Fire",
            severity=SeverityLevel.CRITICAL,
            status=GrievanceStatus.IN_PROGRESS,
            current_jurisdiction_id=j.id,
            assigned_authority="Test Auth",
            sla_deadline=now + timedelta(days=1),
            unique_id=f"G-{i}"
        )
        test_db.add(g)
        test_db.flush()

        audit = EscalationAudit(
            grievance_id=g.id,
            previous_authority="System",
            new_authority="Admin",
            reason=EscalationReason.SEVERITY_UPGRADE,
            timestamp=now,
            notes="Manual Upgrade by Admin"
        )
        test_db.add(audit)

    test_db.commit()

    # 2. Run Engine
    # We need to patch SessionLocal in civic_intelligence to use our test_db
    with patch("backend.civic_intelligence.SessionLocal", return_value=test_db):
        civic_intelligence_engine.run_daily_cycle()

    # 3. Verify Snapshot
    snapshots = os.listdir(mock_snapshot_dir)
    assert len(snapshots) == 1, "Snapshot file should be created"
    with open(os.path.join(mock_snapshot_dir, snapshots[0]), 'r') as f:
        snapshot_data = json.load(f)

    assert "civic_index" in snapshot_data
    assert snapshot_data["civic_index"]["new_issues_count"] == 6

    # Verify cluster detected
    clusters = snapshot_data["trends"]["clusters"]
    # DBSCAN clustering depends on scikit-learn availability.
    # If scikit-learn is missing, it returns all issues as clusters (if fallback logic is used)
    # or empty if strictly depending on sklearn.
    # But current implementation in trend_analyzer calls spatial_utils.cluster_issues_dbscan
    # which falls back to list of lists if sklearn missing.
    # So we should see clusters.
    assert len(clusters) > 0

    # 4. Verify Weight Updates
    # Check Fire category weight increase.
    # We added 3 upgrades for Fire. Logic: count >= 3 -> factor 1.1.

    # Reload weights file
    with open(mock_weights_file, 'r') as f:
        updated_weights = json.load(f)

    fire_multiplier = updated_weights["category_multipliers"]["Fire"]
    assert fire_multiplier > 1.0, "Fire multiplier should increase"
    assert round(fire_multiplier, 1) == 1.1
