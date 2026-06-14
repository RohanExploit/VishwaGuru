from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
from backend.trend_analyzer import TrendAnalyzer
from backend.models import Issue

def test_extract_keywords():
    analyzer = TrendAnalyzer()
    texts = [
        "There is a big pothole on the road.",
        "Another pothole here.",
        "Road is blocked by debris."
    ]
    # top_n=3
    # keywords: pothole (2), road (2), blocked (1), debris (1), big (1), another (1), here (1)
    # stop_words removed: is, a, on, the, by, there

    keywords = analyzer._extract_top_keywords(texts, top_n=3)
    keys = [k[0] for k in keywords]
    assert "pothole" in keys
    assert "road" in keys

def test_analyze_trends_empty():
    analyzer = TrendAnalyzer()
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = analyzer.analyze_trends(mock_db)
    assert result["total_issues"] == 0
    assert result["top_keywords"] == []
    assert result["category_spikes"] == []
    assert result["cluster_hotspots"] == []

def test_analyze_trends_with_data():
    analyzer = TrendAnalyzer()
    mock_db = MagicMock()

    # Mock issues
    # Need to mock attributes so TrendAnalyzer can access them
    issue1 = MagicMock(spec=Issue)
    issue1.description = "Bad pothole on main street"
    issue1.category = "Pothole"
    issue1.created_at = datetime.now(timezone.utc)
    issue1.latitude = 10.0
    issue1.longitude = 20.0

    issue2 = MagicMock(spec=Issue)
    issue2.description = "Another pothole nearby"
    issue2.category = "Pothole"
    issue2.created_at = datetime.now(timezone.utc)
    issue2.latitude = 10.0001
    issue2.longitude = 20.0001

    issue3 = MagicMock(spec=Issue)
    issue3.description = "Fire in building complex"
    issue3.category = "Fire"
    issue3.created_at = datetime.now(timezone.utc)
    issue3.latitude = 12.0
    issue3.longitude = 22.0

    mock_db.query.return_value.filter.return_value.all.return_value = [issue1, issue2, issue3]

    # We need to mock cluster_issues_dbscan or rely on fallback if it's imported
    # Since we can't easily mock imports inside the function without patch, let's just let it run.
    # If sklearn is missing, it will use fallback. If present, it will cluster issue1 and issue2.

    result = analyzer.analyze_trends(mock_db)

    assert result["total_issues"] == 3
    # Pothole (2), Fire (1)
    cats = {c["category"]: c["count"] for c in result["category_spikes"]}
    assert cats["Pothole"] == 2
    assert cats["Fire"] == 1

    # Check keywords
    keys = [k[0] for k in result["top_keywords"]]
    assert "pothole" in keys
