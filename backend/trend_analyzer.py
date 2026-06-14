from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from collections import Counter
import re
from typing import Dict, Any, List

from backend.models import Issue

class TrendAnalyzer:
    """
    Analyzes civic issues to detect trends, keyword spikes, and category patterns.
    """

    def __init__(self):
        pass

    def analyze_trends(self, db: Session) -> Dict[str, Any]:
        """
        Analyzes issues from the last 24 hours.
        Returns top keywords, category distribution, and emerging trends.
        """
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(hours=24)
        two_days_ago = now - timedelta(hours=48)

        # Fetch issues from last 24h
        recent_issues = db.query(Issue.description, Issue.category, Issue.latitude, Issue.longitude)\
            .filter(Issue.created_at >= one_day_ago).all()

        # Fetch issues from previous period (24-48h ago) for baseline comparison
        previous_issues = db.query(Issue.category)\
            .filter(Issue.created_at >= two_days_ago, Issue.created_at < one_day_ago).all()

        # 1. Top Keywords
        keywords = self._extract_top_keywords([i.description for i in recent_issues if i.description])

        # 2. Category Analysis & Spikes
        current_categories = Counter([i.category for i in recent_issues if i.category])
        previous_categories = Counter([i.category for i in previous_issues if i.category])

        category_spikes = []
        for cat, count in current_categories.items():
            prev_count = previous_categories.get(cat, 0)
            if prev_count > 0:
                growth = ((count - prev_count) / prev_count) * 100
                if growth > 50: # >50% increase
                    category_spikes.append({"category": cat, "growth_percent": round(growth, 1), "current_count": count})
            elif count >= 3: # New spike if at least 3 issues and none before
                 category_spikes.append({"category": cat, "growth_percent": 100.0, "current_count": count, "note": "New emerging category"})

        # 3. Geographic Clustering (Simple)
        # Identify regions with high density (simplification: group by rounded lat/lon)
        hotspots = self._find_hotspots(recent_issues)

        return {
            "period_start": one_day_ago.isoformat(),
            "period_end": now.isoformat(),
            "total_issues": len(recent_issues),
            "top_keywords": keywords,
            "category_distribution": dict(current_categories),
            "category_spikes": category_spikes,
            "hotspots": hotspots
        }

    def _extract_top_keywords(self, texts: List[str], top_n: int = 5) -> List[Dict[str, Any]]:
        words = []
        stop_words = set([
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "and", "is", "are", "was", "were",
            "this", "that", "it", "with", "from", "by", "near", "my", "please", "help", "issue", "problem",
            "there", "has", "been", "have", "not", "be", "very", "so", "can", "will", "would", "should"
        ])

        for text in texts:
            # Simple tokenization
            tokens = re.findall(r'\b[a-z]{3,}\b', text.lower())
            words.extend([t for t in tokens if t not in stop_words])

        counter = Counter(words)
        return [{"keyword": word, "count": count} for word, count in counter.most_common(top_n)]

    def _find_hotspots(self, issues: List[Any]) -> List[Dict[str, Any]]:
        # Group by approximate location (0.01 degree ~ 1.1km)
        loc_counter = Counter()
        for issue in issues:
            if issue.latitude and issue.longitude:
                # Round to 2 decimal places (approx 1.1km resolution)
                key = (round(issue.latitude, 2), round(issue.longitude, 2))
                loc_counter[key] += 1

        hotspots = []
        for (lat, lon), count in loc_counter.most_common(5):
            if count > 1: # Only report if more than 1 issue
                hotspots.append({
                    "latitude": lat,
                    "longitude": lon,
                    "count": count
                })
        return hotspots
