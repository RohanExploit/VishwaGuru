import pytest
from backend.trend_analyzer import trend_analyzer
from backend.models import Issue

def test_trend_analyzer_extract_keywords():
    issues = [
        Issue(description="There is a large pothole on Main Street. Please fix it soon!"),
        Issue(description="Another pothole on Main Street, very dangerous."),
        Issue(description="The pothole is getting bigger.")
    ]
    keywords = trend_analyzer._extract_keywords(issues)
    words = [kw[0] for kw in keywords]
    assert "pothole" in words
    assert "main" in words
