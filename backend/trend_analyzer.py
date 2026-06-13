import logging
import datetime
from collections import Counter
import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models import Issue
from backend.spatial_utils import haversine_distance

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """
    Analyzes recent civic issues to detect trends, spikes, and clusters.
    """

    STOPWORDS = {
        "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were",
        "and", "or", "but", "so", "it", "this", "that", "there", "here", "my", "your", "his", "her",
        "from", "by", "as", "be", "have", "has", "had", "do", "does", "did", "will", "would", "should",
        "can", "could", "may", "might", "must", "issue", "problem", "complaint", "please", "help",
        "near", "opposite", "behind", "front", "road", "street", "area", "city", "ward", "zone"
    }

    def analyze_recent_issues(self, db: Session, hours: int = 24) -> Dict[str, Any]:
        """
        Analyzes issues from the last `hours` to extract trends.
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = now - datetime.timedelta(hours=hours)
        prev_start_time = start_time - datetime.timedelta(hours=hours)

        # Fetch recent issues
        recent_issues = db.query(Issue).filter(
            Issue.created_at >= start_time
        ).all()

        # Fetch previous window issues for comparison (for spikes)
        previous_issues_count = db.query(Issue).filter(
            Issue.created_at >= prev_start_time,
            Issue.created_at < start_time
        ).count()

        # 1. Keyword Analysis
        keywords = self._extract_top_keywords(recent_issues)

        # 2. Category Analysis (Spikes)
        category_stats = self._analyze_categories(recent_issues)

        # 3. Spatial Analysis (Clustering & Density)
        spatial_stats = self._analyze_spatial_distribution(recent_issues)

        # 4. Global Stats
        total_issues = len(recent_issues)
        growth_rate = 0
        if previous_issues_count > 0:
            growth_rate = ((total_issues - previous_issues_count) / previous_issues_count) * 100

        return {
            "period_hours": hours,
            "total_issues": total_issues,
            "previous_period_issues": previous_issues_count,
            "growth_rate_percent": round(growth_rate, 1),
            "top_keywords": keywords,
            "category_stats": category_stats,
            "spatial_stats": spatial_stats,
            "timestamp": now.isoformat()
        }

    def _extract_top_keywords(self, issues: List[Issue], top_n: int = 5) -> List[Dict[str, Any]]:
        if not issues:
            return []

        text_blob = " ".join([issue.description or "" for issue in issues]).lower()
        # Simple tokenization: remove non-alphanumeric (keep spaces), split
        tokens = re.findall(r'\b[a-z]{3,}\b', text_blob)

        filtered_tokens = [t for t in tokens if t not in self.STOPWORDS]

        counter = Counter(filtered_tokens)
        most_common = counter.most_common(top_n)

        return [{"keyword": word, "count": count} for word, count in most_common]

    def _analyze_categories(self, issues: List[Issue]) -> Dict[str, Any]:
        if not issues:
            return {"distribution": {}, "spikes": []}

        counter = Counter([issue.category for issue in issues if issue.category])
        total = len(issues)

        distribution = {cat: count for cat, count in counter.items()}

        # Detect simple dominance (if one category is > 30% of issues)
        spikes = []
        for cat, count in counter.items():
            percentage = (count / total) * 100
            if percentage > 30: # Arbitrary threshold for "spike" in daily trend
                spikes.append(cat)

        return {
            "distribution": distribution,
            "dominant_categories": spikes
        }

    def _analyze_spatial_distribution(self, issues: List[Issue]) -> Dict[str, Any]:
        """
        Analyzes geographic distribution to find hotspots and density.
        """
        valid_issues = [i for i in issues if i.latitude is not None and i.longitude is not None]
        if not valid_issues:
            return {"clusters": [], "avg_neighbor_dist": None}

        # 1. Grid-based clustering (simple hotspot detection)
        # Round lat/lon to ~1km precision (2 decimal places)
        grid_counter = Counter()
        for issue in valid_issues:
            grid_key = (round(issue.latitude, 2), round(issue.longitude, 2))
            grid_counter[grid_key] += 1

        # Identify hotspots (grids with > 2 issues)
        hotspots = []
        for (lat, lon), count in grid_counter.items():
            if count >= 3:
                hotspots.append({"lat": lat, "lon": lon, "count": count})

        hotspots.sort(key=lambda x: x["count"], reverse=True)

        # 2. Average Nearest Neighbor Distance (for density estimation)
        # If avg distance is small, issues are clumped -> maybe need larger deduplication radius?
        total_min_dist = 0
        count = 0

        if len(valid_issues) > 1:
            for i in range(len(valid_issues)):
                min_dist = float('inf')
                found = False
                for j in range(len(valid_issues)):
                    if i == j:
                        continue
                    dist = haversine_distance(
                        valid_issues[i].latitude, valid_issues[i].longitude,
                        valid_issues[j].latitude, valid_issues[j].longitude
                    )
                    if dist < min_dist:
                        min_dist = dist
                        found = True

                if found:
                    total_min_dist += min_dist
                    count += 1

            avg_neighbor_dist = total_min_dist / count if count > 0 else 0
        else:
            avg_neighbor_dist = 0

        return {
            "hotspots": hotspots[:5], # Top 5 hotspots
            "avg_neighbor_dist": round(avg_neighbor_dist, 1)
        }
