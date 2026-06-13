import pytest
from unittest.mock import MagicMock, patch
from backend.civic_intelligence import CivicIntelligenceEngine
from backend.models import Issue, Grievance, SeverityLevel
from datetime import datetime, timezone

@pytest.fixture
def mock_db():
    session = MagicMock()
    return session

@pytest.fixture
def mock_engine(mock_db):
    engine = CivicIntelligenceEngine(db_session=mock_db)
    # Mock AdaptiveWeights to avoid actual file I/O
    engine.weights = MagicMock()
    engine.weights.severity_keywords = {
        "critical": ["fire", "death"],
        "high": ["pothole"],
        "medium": ["garbage"],
        "low": ["light"]
    }
    engine.weights.duplicate_search_radius = 50.0

    # Mock analyzer
    engine.analyzer = MagicMock()

    return engine

def test_refine_daily_basic(mock_engine, mock_db):
    # Mock queries
    issues = [
        Issue(id=1, category="Pothole", description="Big pothole", created_at=datetime.now(timezone.utc)),
        Issue(id=2, category="Pothole", description="Another pothole", created_at=datetime.now(timezone.utc))
    ]
    grievances = [
        Grievance(issue_id=1, category="Pothole", severity=SeverityLevel.HIGH),
        Grievance(issue_id=2, category="Pothole", severity=SeverityLevel.HIGH)
    ]

    issue_query_mock = MagicMock()
    issue_query_mock.filter.return_value.all.return_value = issues
    issue_query_mock.filter.return_value.count.return_value = 1

    grievance_query_mock = MagicMock()
    grievance_query_mock.filter.return_value.all.return_value = grievances

    def query_side_effect(model):
        if model == Issue:
            return issue_query_mock
        elif model == Grievance:
            return grievance_query_mock
        return MagicMock()

    mock_db.query.side_effect = query_side_effect

    # Mock analyzer
    mock_engine.analyzer.analyze.return_value = {
        "top_keywords": [("pothole", 2)],
        "category_distribution": {"Pothole": 2},
        "clusters": []
    }

    # Run
    snapshot = mock_engine.refine_daily()

    assert snapshot["issue_count"] == 2
    assert snapshot["grievance_count"] == 2
    assert snapshot["trends"]["top_keywords"][0][0] == "pothole"
    assert "civic_intelligence_index" in snapshot

def test_optimize_weights(mock_engine):
    # Setup grievances with CRITICAL severity for "Pothole" category
    # Pothole is currently in "high" (mocked above)
    grievances = [
        Grievance(category="Pothole", severity=SeverityLevel.CRITICAL),
        Grievance(category="Pothole", severity=SeverityLevel.CRITICAL)
    ]

    # Setup self.weights.severity_keywords on the mocked engine properly
    # The mock initialized in fixture might be reused or not correct for this test logic
    # _move_keyword accesses self.weights.severity_keywords dictionary

    # We need to ensure severity_keywords is a real dict on the mock, not a Mock object
    # The fixture sets it to a dict.

    adjustments = mock_engine._optimize_weights([], grievances)

    # Check if pothole moved
    assert len(adjustments) > 0
    assert "Escalated 'pothole' to Critical" in adjustments[0]

    # Verify modification
    assert "pothole" in mock_engine.weights.severity_keywords["critical"]
    # It might still be in high if remove logic failed or wasn't called correctly?
    # _move_keyword removes it.
    assert "pothole" not in mock_engine.weights.severity_keywords["high"]

def test_optimize_duplicate_detection(mock_engine):
    # Need issues with lat/lon
    issues = [
        Issue(latitude=10.0, longitude=10.0, category="Pothole"),
        Issue(latitude=10.0005, longitude=10.0005, category="Pothole"), # Very close (~55m)
    ]

    # With patch, we override haversine_distance import in civic_intelligence
    with patch("backend.civic_intelligence.haversine_distance") as mock_dist:
        mock_dist.return_value = 60.0 # Force 60m

        stats = mock_engine._optimize_duplicate_detection(issues)

        # 1 pair (issue 0 vs issue 1)
        # distance 60.0. > 50 and < 70.
        # same category.
        # close_pairs = 1.
        # total_pairs = 1.
        # ratio 1.0 > 0.3.
        # Should increase radius.

        assert stats["close_pairs_detected"] == 1
        assert "Increased radius" in stats["reason"]
        mock_engine.weights.update_duplicate_radius.assert_called()
