import os
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from backend.trend_analyzer import TrendAnalyzer
from backend.adaptive_weights import AdaptiveWeights
from backend.civic_intelligence import CivicIntelligenceEngine
from backend.models import Issue

class TestTrendAnalyzer:
    def test_extract_keywords(self):
        analyzer = TrendAnalyzer()
        issues = [
            Issue(description="dangerous pothole on main road", category="Pothole"),
            Issue(description="another big pothole detected", category="Pothole"),
            Issue(description="garbage dump smelling bad", category="Garbage")
        ]

        keywords = analyzer._extract_top_keywords(issues, top_n=5)
        # expected: pothole (2), dangerous, main, big, detected, garbage, dump, smelling, bad

        keyword_map = {k['keyword']: k['count'] for k in keywords}
        assert keyword_map.get('pothole') == 2
        assert 'road' not in keyword_map # 'road' is in STOPWORDS list in TrendAnalyzer

    def test_analyze_categories(self):
        analyzer = TrendAnalyzer()
        issues = [
            Issue(category="Pothole"),
            Issue(category="Pothole"),
            Issue(category="Garbage"),
            Issue(category="Pothole")
        ]

        stats = analyzer._analyze_categories(issues)
        assert stats['distribution']['Pothole'] == 3
        assert stats['distribution']['Garbage'] == 1
        assert "Pothole" in stats['dominant_categories'] # 75% > 30%

class TestAdaptiveWeights:
    def test_init_and_io(self, tmp_path):
        # Initialize with temp dir
        weights_mgr = AdaptiveWeights(data_dir=str(tmp_path))

        # Check file creation
        weights_file = os.path.join(tmp_path, "modelWeights.json")
        assert os.path.exists(weights_file)

        # Check defaults
        weights = weights_mgr.get_weights()
        assert weights["duplicate_search_radius"] == 50.0

        # Update weights
        weights["duplicate_search_radius"] = 75.0
        weights_mgr.update_weights(weights)

        # Verify persistence
        weights_mgr2 = AdaptiveWeights(data_dir=str(tmp_path))
        assert weights_mgr2.get_duplicate_search_radius() == 75.0

        # Check backup
        history_dir = os.path.join(tmp_path, "weight_history")
        assert os.path.exists(history_dir)
        assert len(os.listdir(history_dir)) == 1

class TestCivicIntelligenceEngine:
    @patch("backend.civic_intelligence.adaptive_weights")
    def test_refine_daily(self, mock_adaptive_weights, tmp_path):
        # Setup mock adaptive weights behavior
        mock_adaptive_weights.get_weights.return_value = {
            "duplicate_search_radius": 50.0,
            "severity_keywords": {"high": [], "medium": [], "low": []},
            "categories": {}
        }
        mock_adaptive_weights.get_duplicate_search_radius.return_value = 50.0

        # Mock DB session
        db_session = MagicMock()

        # Mock recent issues query
        issues = [
            Issue(
                description="test issue 1",
                category="Pothole",
                created_at=datetime.now(),
                latitude=10.0, longitude=20.0
            ),
            Issue(
                description="test issue 2",
                category="Pothole",
                created_at=datetime.now(),
                latitude=10.001, longitude=20.001 # Close to issue 1
            )
        ]

        # Configure mock query chain
        # db.query(Issue).filter(...).all() -> issues
        # db.query(Issue).filter(...).count() -> count
        query_mock = db_session.query.return_value
        filter_mock = query_mock.filter.return_value
        filter_mock.all.return_value = issues
        filter_mock.count.return_value = 5 # arbitrary count for previous period

        # Initialize engine
        engine = CivicIntelligenceEngine(data_dir=str(tmp_path))

        # Run refinement
        snapshot = engine.refine_daily(db_session)

        # Verify snapshot structure
        assert "civic_intelligence_index" in snapshot
        assert "trends" in snapshot
        assert snapshot["trends"]["total_issues"] == 2

        # Verify snapshot file created
        snapshots_dir = os.path.join(tmp_path, "dailySnapshots")
        assert os.path.exists(snapshots_dir)
        assert len(os.listdir(snapshots_dir)) == 1
