import pytest
from unittest.mock import MagicMock
from backend.models import Issue
from backend.trend_analyzer import TrendAnalyzer

@pytest.fixture
def sample_issues():
    issues = []
    for i in range(10):
        issue = Issue(
            id=i,
            description=f"This is a pothole issue {i}. Very dangerous.",
            category="Pothole" if i % 2 == 0 else "Garbage",
            latitude=12.9716 + (i * 0.0001),
            longitude=77.5946 + (i * 0.0001)
        )
        issues.append(issue)
    return issues

def test_extract_keywords(sample_issues):
    analyzer = TrendAnalyzer()
    keywords = analyzer._extract_keywords(sample_issues, top_n=3)

    # "pothole" appears 5 times. "dangerous" appears 10 times.
    # "issue" is stopword? Let's check trend_analyzer.py
    # Yes, "issue" is in stopword list.

    keyword_map = dict(keywords)
    assert "pothole" in keyword_map or "dangerous" in keyword_map
    assert keyword_map.get("dangerous", 0) == 10
    assert keyword_map.get("pothole", 0) == 10

def test_analyze_categories(sample_issues):
    analyzer = TrendAnalyzer()
    cats = analyzer._analyze_categories(sample_issues)
    assert cats["Pothole"] == 5
    assert cats["Garbage"] == 5

def test_analyze_clusters_simple(sample_issues):
    analyzer = TrendAnalyzer()
    # Mock simple clustering by forcing fallback or just rely on simple clustering if sklearn is mocked out or not installed
    # The analyzer checks HAS_SKLEARN.
    # We can mock HAS_SKLEARN to False to test simple clustering logic

    with pytest.MonkeyPatch.context() as m:
        m.setattr("backend.trend_analyzer.HAS_SKLEARN", False)
        clusters = analyzer._analyze_clusters(sample_issues)

        # Sample issues are very close (0.0001 deg approx 11m).
        # Should form one big cluster or few depending on radius.
        # radius is 100m. 10 * 11m = 110m spread.
        # Simple clustering is greedy.
        # Might form 1 or 2 clusters.

        # Check if we got any cluster (size >= 3)
        assert len(clusters) > 0
        assert clusters[0]["size"] >= 3
        assert "centroid" in clusters[0]
