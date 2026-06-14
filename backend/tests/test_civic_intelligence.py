from unittest.mock import MagicMock, patch
from backend.civic_intelligence import CivicIntelligenceEngine
from backend.adaptive_weights import AdaptiveWeights

@patch("backend.civic_intelligence.trend_analyzer")
@patch("backend.civic_intelligence.adaptive_weights")
def test_refine_daily(mock_weights, mock_trend_analyzer):
    # Initialize engine
    engine = CivicIntelligenceEngine()

    mock_db = MagicMock()

    # Mock trends
    trends_data = {
        "top_keywords": [("pothole", 10)],
        "category_spikes": [{"category": "Pothole", "count": 20}],
        "cluster_hotspots": [{"latitude": 10.0, "longitude": 10.0, "count": 5}],
        "total_issues": 100
    }
    mock_trend_analyzer.analyze_trends.return_value = trends_data

    # Configure mock_weights properties
    # Since category_weights is accessed as a property, we mock it as a dict
    mock_weights.category_weights = {}
    mock_weights.duplicate_search_radius = 50.0

    # Mock DB counts for resolved issues (scalar)
    mock_db.query.return_value.filter.return_value.scalar.return_value = 50

    # Mock EscalationAudit for manual upgrades (empty list)
    mock_db.query.return_value.filter.return_value.all.return_value = []

    # Run refinement
    result = engine.refine_daily(mock_db)

    # Verify results
    assert result["metrics"]["created_last_24h"] == 100
    assert result["metrics"]["resolved_last_24h"] == 50

    # Check if update_category_weight was called for the spike "Pothole"
    # Logic: if count > 10 (20 > 10), and current boost < 10 (0 < 10), boost +2
    mock_weights.update_category_weight.assert_called_with("Pothole", 2.0)

def test_calculate_civic_index_score():
    engine = CivicIntelligenceEngine()
    mock_db = MagicMock()

    trends = {
        "total_issues": 100,
        "cluster_hotspots": [
            {"latitude": 10.0, "longitude": 20.0, "count": 5},
            {"latitude": 11.0, "longitude": 21.0, "count": 4},
            {"latitude": 12.0, "longitude": 22.0, "count": 3}
        ],
        "category_spikes": []
    }

    # Resolved = 30 -> bonus min(30, 60) = 30
    mock_db.query.return_value.filter.return_value.scalar.return_value = 30

    # Base 60 + 30 + 6 = 96

    # Mock previous score (file read)
    with patch("backend.civic_intelligence.os.listdir", return_value=[]):
        result = engine._calculate_civic_index(mock_db, trends)

    assert result["score"] == 96.0
