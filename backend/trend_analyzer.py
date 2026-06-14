import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Tuple
import re
from collections import Counter

from backend.models import Issue
from backend.spatial_utils import cluster_issues_dbscan, calculate_cluster_centroid

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    """
    Analyzes civic issues to detect trends, keywords, and geographic hotspots.
    """
    def __init__(self):
        self.stop_words = {
            "the", "a", "an", "in", "on", "at", "to", "for", "of", "with", "is", "are",
            "was", "were", "this", "that", "it", "my", "our", "please", "help", "issue",
            "problem", "report", "reported", "and", "or", "but", "so", "if", "when",
            "where", "how", "why", "has", "have", "had", "been", "there", "their"
        }

    def analyze_trends(self, db: Session, time_window_hours: int = 24) -> Dict[str, Any]:
        """
        Analyzes issues from the last `time_window_hours` to find trends.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=time_window_hours)

        # Fetch recent issues
        recent_issues = db.query(Issue).filter(Issue.created_at >= cutoff_time).all()

        if not recent_issues:
            logger.info("No issues found in the last 24h for trend analysis.")
            return {
                "top_keywords": [],
                "category_spikes": [],
                "cluster_hotspots": [],
                "total_issues": 0
            }

        # 1. Top Keywords
        descriptions = [issue.description for issue in recent_issues if issue.description]
        top_keywords = self._extract_top_keywords(descriptions)

        # 2. Category Spikes (Frequency)
        categories = [issue.category for issue in recent_issues if issue.category]
        category_counts = Counter(categories)
        top_categories = category_counts.most_common(5)

        # 3. Geographic Clustering
        # Try DBSCAN first
        clusters = cluster_issues_dbscan(recent_issues, eps_meters=100)

        # Check if DBSCAN failed (returned all singletons) or wasn't available
        is_trivial = all(len(c) == 1 for c in clusters) if clusters else True
        if is_trivial and len(recent_issues) > 1:
            # Fallback to grid-based clustering
            clusters = self._grid_clustering(recent_issues)

        hotspots = []
        for cluster in clusters:
            # Only consider clusters with multiple issues as "hotspots"
            if len(cluster) >= 2:
                try:
                    lat, lon = calculate_cluster_centroid(cluster)
                    hotspots.append({
                        "latitude": lat,
                        "longitude": lon,
                        "count": len(cluster),
                        "primary_category": self._get_primary_category(cluster)
                    })
                except ValueError:
                    continue

        # Sort hotspots by count descending
        hotspots.sort(key=lambda x: x["count"], reverse=True)

        return {
            "top_keywords": top_keywords,
            "category_spikes": [{"category": c, "count": n} for c, n in top_categories],
            "cluster_hotspots": hotspots[:5], # Top 5 hotspots
            "total_issues": len(recent_issues)
        }

    def _extract_top_keywords(self, texts: List[str], top_n: int = 5) -> List[Tuple[str, int]]:
        all_words = []
        for text in texts:
            # Simple tokenization: lowercase, remove punctuation
            words = re.findall(r'\b\w+\b', text.lower())
            filtered_words = [w for w in words if w not in self.stop_words and len(w) > 3]
            all_words.extend(filtered_words)

        return Counter(all_words).most_common(top_n)

    def _get_primary_category(self, cluster: List[Issue]) -> str:
        cats = [issue.category for issue in cluster if issue.category]
        if not cats:
            return "Unknown"
        return Counter(cats).most_common(1)[0][0]

    def _grid_clustering(self, issues: List[Issue]) -> List[List[Issue]]:
        """Simple grid-based clustering fallback."""
        grid = {}
        for issue in issues:
            if issue.latitude is None or issue.longitude is None:
                continue
            # Round to 3 decimal places (approx 100m resolution)
            key = (round(issue.latitude, 3), round(issue.longitude, 3))
            if key not in grid:
                grid[key] = []
            grid[key].append(issue)
        return list(grid.values())

trend_analyzer = TrendAnalyzer()
