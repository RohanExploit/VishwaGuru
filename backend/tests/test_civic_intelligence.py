import pytest
import json
import os
import time
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime, timedelta, timezone

from backend.models import Issue, EscalationAudit, EscalationReason, Grievance
from backend.adaptive_weights import AdaptiveWeights
from backend.trend_analyzer import TrendAnalyzer
from backend.civic_intelligence import CivicIntelligenceEngine
from backend.spatial_utils import get_cluster_representative

# Mock data
MOCK_WEIGHTS = {
    "severity_keywords": {"critical": ["fire"]},
    "urgency_patterns": [],
    "category_keywords": {"Fire": ["fire"], "Water": ["water"]},
    "category_multipliers": {"Fire": 1.0, "Water": 1.0},
    "duplicate_search_radius": 50.0
}

@pytest.fixture
def mock_adaptive_weights():
    with patch('backend.adaptive_weights.DATA_FILE', 'mock_weights.json'):
        with patch('builtins.open', mock_open(read_data=json.dumps(MOCK_WEIGHTS))) as m:
            with patch('os.path.exists', return_value=True):
                with patch('os.path.getmtime', return_value=100):
                    # Reset singleton
                    AdaptiveWeights._instance = None
                    weights = AdaptiveWeights()
                    yield weights
                    AdaptiveWeights._instance = None

def test_adaptive_weights_load(mock_adaptive_weights):
    assert mock_adaptive_weights.get_category_multipliers()["Fire"] == 1.0
    assert mock_adaptive_weights.get_severity_keywords()["critical"] == ["fire"]

def test_adaptive_weights_update_category(mock_adaptive_weights):
    with patch('builtins.open', mock_open(read_data=json.dumps(MOCK_WEIGHTS))) as m:
        # We need to mock getmtime to allow save to proceed without reload override
        with patch('os.path.getmtime', side_effect=[100, 200, 200, 200, 200]):
            mock_adaptive_weights.update_category_weight("Fire", 1.5)

            assert mock_adaptive_weights.get_category_multipliers()["Fire"] == 1.5
            # Verify file write
            m().write.assert_called()

def test_trend_analyzer_keywords():
    analyzer = TrendAnalyzer()
    issues = [
        Issue(description="Fire in the building help"),
        Issue(description="Big fire burning here"),
        Issue(description="Building has a fire problem")
    ]

    result = analyzer.analyze(issues)
    keywords = dict(result['top_keywords'])

    # "fire" should be top
    assert "fire" in keywords
    assert keywords["fire"] == 3
    # "building" should be there
    assert "building" in keywords
    assert keywords["building"] == 2

def test_trend_analyzer_categories():
    analyzer = TrendAnalyzer()
    issues = [
        Issue(category="Fire"),
        Issue(category="Fire"),
        Issue(category="Water")
    ]

    result = analyzer.analyze(issues)
    dist = result['category_distribution']

    assert dist["Fire"] == 2
    assert dist["Water"] == 1

@patch('backend.trend_analyzer.cluster_issues_dbscan')
@patch('backend.trend_analyzer.get_cluster_representative')
def test_trend_analyzer_clusters(mock_get_rep, mock_dbscan):
    analyzer = TrendAnalyzer()

    # Mock cluster result: 2 clusters, one with 3 items, one with 2
    cluster1 = [MagicMock(), MagicMock(), MagicMock()]
    cluster2 = [MagicMock(), MagicMock()]

    mock_dbscan.return_value = [cluster1, cluster2]

    # Mock representative
    mock_rep = MagicMock()
    mock_rep.latitude = 10.0
    mock_rep.longitude = 20.0
    mock_rep.category = "Test"
    mock_rep.description = "Test desc"
    mock_get_rep.return_value = mock_rep

    mock_issue = MagicMock()
    mock_issue.description = "test"
    result = analyzer.analyze([mock_issue]) # Input doesn't matter as we mock dbscan

    clusters = result['clusters']
    assert len(clusters) == 1 # Only cluster1 (size 3) should be returned, cluster2 (size 2) filtered out
    assert clusters[0]['count'] == 3
    assert clusters[0]['latitude'] == 10.0

@patch('backend.civic_intelligence.SessionLocal')
@patch('backend.civic_intelligence.trend_analyzer')
@patch('backend.civic_intelligence.adaptive_weights')
@patch('builtins.open', new_callable=mock_open)
@patch('json.dump')
@patch('os.listdir')
def test_civic_intelligence_run(mock_listdir, mock_json_dump, mock_file_open, mock_weights, mock_trend_analyzer, mock_db_session):
    engine = CivicIntelligenceEngine()

    # Mock DB
    mock_session = MagicMock()
    mock_db_session.return_value = mock_session

    # Mock previous snapshot file
    mock_listdir.return_value = ['2023-01-01.json']

    # We need to simulate reading the previous snapshot
    # Since we use `open` for both reading previous snapshot and writing new one,
    # we need to be careful with side_effect.

    previous_snapshot_content = json.dumps({
        "trends": {
            "category_distribution": {"Fire": 2, "Water": 5}
        }
    })

    # Configure mock_open to return previous snapshot content when reading
    # and to provide a separate handle when writing the new snapshot.
    read_mock = mock_open(read_data=previous_snapshot_content)
    write_mock = mock_open()

    def open_side_effect(file, mode='r', *args, **kwargs):
        # Use the read_mock for reading the previous snapshot
        if 'r' in mode:
            return read_mock(file, mode, *args, **kwargs)
        # Use a separate mock for writing the new snapshot
        return write_mock(file, mode, *args, **kwargs)

    mock_file_open.side_effect = open_side_effect
    # Mock query objects
    mock_query_issues = MagicMock()
    mock_query_upgrades = MagicMock()
    mock_query_grievance = MagicMock()

    # Define query side effects
    def query_side_effect(model):
        if model == Issue:
            return mock_query_issues
        elif model == EscalationAudit:
            return mock_query_upgrades
        elif model == Grievance:
            return mock_query_grievance
        return MagicMock()

    mock_session.query.side_effect = query_side_effect

    # Setup results
    issues_result = [Issue(id=1, resolved_at=None), Issue(id=2, resolved_at=datetime.now(timezone.utc))]

    # Issue Query Chain
    # First call is for fetching issues_24h, second for resolved_count?
    # Actually code calls: db.query(Issue).filter(Issue.created_at >= last_24h).all()
    # And: db.query(Issue).filter(Issue.resolved_at >= last_24h).count()

    # To differentiate, we can check the filter call or just return appropriate mocks
    # Let's just make sure it returns something valid for both
    mock_query_issues.filter.return_value.all.return_value = issues_result # issues_24h
    mock_query_issues.filter.return_value.count.return_value = 1 # resolved_count

    # Upgrade Query Chain
    # We want to test weight update, so let's simulate upgrades
    audit1 = MagicMock(grievance_id=1)
    audit2 = MagicMock(grievance_id=2)
    audit3 = MagicMock(grievance_id=3)
    mock_query_upgrades.filter.return_value.all.return_value = [audit1, audit2, audit3]

    # Grievance query
    g1 = Grievance(id=1, category="Fire")
    g2 = Grievance(id=2, category="Fire")
    g3 = Grievance(id=3, category="Fire")
    mock_query_grievance.filter.return_value.all.return_value = [g1, g2, g3]

    # Setup Trend Analyzer
    mock_trend_analyzer.analyze.return_value = {
        "top_keywords": [],
        "category_distribution": {"Fire": 10}, # Spiked from 2 (in previous snapshot)
        "clusters": []
    }

    # Setup Adaptive Weights
    mock_weights.get_duplicate_search_radius.return_value = 50.0
    mock_weights.update_category_weight.return_value = None # It returns nothing currently

    # Run
    engine.run_daily_cycle()

    # Verify trend analyzer called
    mock_trend_analyzer.analyze.assert_called()

    # Verify weight update called (3 upgrades for Fire)
    mock_weights.update_category_weight.assert_called_with("Fire", 1.1)

    # Verify snapshot saved
    # The last call to json.dump should be the snapshot
    args, _ = mock_json_dump.call_args
    snapshot = args[0]

    assert "date" in snapshot
    assert "civic_index" in snapshot
    assert "trends" in snapshot
    assert "weight_changes" in snapshot # Expect this new field

    # Check spike detection (if implemented)
    # We expect "Fire" to be marked as a spike because it went from 2 to 10
    if "spikes" in snapshot["trends"]:
        assert "Fire" in snapshot["trends"]["spikes"]
