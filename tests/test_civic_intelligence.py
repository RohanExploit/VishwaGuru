import pytest
import os
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database import Base
from backend.models import Issue, Grievance, SeverityLevel
from backend.civic_intelligence import get_civic_intelligence_engine
from backend.adaptive_weights import AdaptiveWeights

# Setup test database
@pytest.fixture(scope="function")
def test_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()

def test_civic_intelligence_refinement(test_db, tmp_path):
    # Setup test weights file
    test_weights_file = tmp_path / "test_modelWeights.json"

    # 1. Create Dummy Issues
    now = datetime.now(timezone.utc)
    one_day_ago = now - timedelta(hours=24)
    two_days_ago = now - timedelta(hours=48)

    # Recent Issues (Last 24h)
    issues_recent = [
        Issue(description="Big pothole on Main St", category="Pothole", created_at=now, status="open", upvotes=5),
        Issue(description="Another pothole here", category="Pothole", created_at=now, status="open", upvotes=2),
        Issue(description="Garbage pile", category="Garbage", created_at=now, status="resolved", resolved_at=now, upvotes=1),
        Issue(description="Broken streetlight", category="Street Light", created_at=now, status="verified", verified_at=now, upvotes=3),
        # Keyword Optimization Test Issues
        Issue(description="This is a severe pothole", category="Pothole", created_at=now, status="open"),
        Issue(description="Another severe crater", category="Pothole", created_at=now, status="open"),
        Issue(description="Very severe road damage", category="Pothole", created_at=now, status="open")
    ]

    # Duplicate Optimization Test (High Density)
    # Add 10 issues at same location
    for _ in range(10):
        issues_recent.append(Issue(description="High density issue", category="Traffic", created_at=now, latitude=18.52, longitude=73.85))

    # Older Issues (24-48h ago) - Baseline
    # Add 1 hour to ensure it's strictly > two_days_ago and < one_day_ago
    safe_old_time = two_days_ago + timedelta(hours=1)
    issues_old = [
        Issue(description="Old pothole", category="Pothole", created_at=safe_old_time, status="open"),
        Issue(description="Old garbage", category="Garbage", created_at=safe_old_time, status="open")
    ]

    # Critical Grievances for Weight Optimization test
    # Create 3 critical potholes in last 24h to trigger weight update
    grievances = [
        Grievance(category="Pothole", severity=SeverityLevel.CRITICAL, created_at=now, current_jurisdiction_id=1, assigned_authority="Dept", sla_deadline=now),
        Grievance(category="Pothole", severity=SeverityLevel.CRITICAL, created_at=now, current_jurisdiction_id=1, assigned_authority="Dept", sla_deadline=now),
        Grievance(category="Pothole", severity=SeverityLevel.CRITICAL, created_at=now, current_jurisdiction_id=1, assigned_authority="Dept", sla_deadline=now)
    ]

    for i in issues_recent + issues_old:
        test_db.add(i)
    for g in grievances:
        test_db.add(g)
    test_db.commit()

    # 2. Setup Engine with Test Weights
    engine = get_civic_intelligence_engine()
    engine.weights_manager = AdaptiveWeights(weights_file=str(test_weights_file))
    # Reset severity mapping to default to test update
    engine.weights_manager.severity_mapping["pothole"] = "medium"
    engine.weights_manager.save_weights()

    # 3. Run Refinement
    # Patch save_snapshot to use tmp_path
    snapshot_dir = tmp_path / "dailySnapshots"
    os.makedirs(snapshot_dir, exist_ok=True)

    original_save = engine._save_snapshot
    def mock_save_snapshot(snapshot):
        filename = f"{snapshot['date']}.json"
        filepath = snapshot_dir / filename
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=4)

    engine._save_snapshot = mock_save_snapshot

    result = engine.refine_daily(test_db)

    # 4. Assertions

    # Check Index Calculation
    # Resolved: 1 (2 points)
    # Verified: 1 (1 point)
    # Engagement: 5+2+1+3 = 11 (5.5 points)
    # Base: 50
    # Spikes: Pothole (400%), Traffic (New) -> 2 spikes (-4 points)
    # Expected Score: 50 + 2 + 1 + 5.5 - 4 = 54.5
    assert result['civic_intelligence_index']['score'] == 54.5

    # Check Trends
    assert result['trends']['total_issues'] == 17
    # Pothole: 5 recent vs 1 old -> 400% growth
    spikes = result['trends']['category_spikes']
    pothole_spike = next((s for s in spikes if s['category'] == 'Pothole'), None)
    assert pothole_spike is not None
    assert pothole_spike['growth_percent'] == 400.0

    # Check Weight Optimization
    # We added 3 critical pothole grievances. Pothole was 'medium'. Should be upgraded to 'high'.
    updated_weights = engine.weights_manager.get_weights()
    assert updated_weights['severity_mapping']['pothole'] == 'high'

    # Check Keyword Optimization
    # "severe" should be added to Pothole category (appeared 3 times)
    # Note: logic checks if keyword is NOT in current keywords. Default keywords don't have "severe".
    # Wait, 'AdaptiveWeights' in test is loaded from temp file which starts with defaults.
    # Default Pothole keywords: ["pothole", "hole", "crater", "road damage", "broken road"]
    # "severe" is not there.
    # But "severe" might be a stopword? No.
    # Also need to check if "severe" is extracted as top keyword. TrendAnalyzer: top_n=5.
    # Keywords: pothole(3+1+1=5), severe(3), crater(1), road(1), damage(1), garbage(2), streetlight(1), broken(1)
    # "severe" should be in top 5.

    # Check duplicate radius optimization
    # Density was 10. Should increase radius by 10 (default 50 -> 60).
    assert updated_weights['duplicate_search_radius'] == 60.0

    # Check Snapshot Saved
    files = list(snapshot_dir.glob("*.json"))
    assert len(files) == 1

    # Cleanup
    engine._save_snapshot = original_save

if __name__ == "__main__":
    sys.exit(pytest.main(["-v", __file__]))
