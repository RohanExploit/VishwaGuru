import re
from typing import List, Dict, Any, Tuple
from collections import Counter
import logging
from backend.models import Issue
from backend.spatial_utils import cluster_issues_dbscan

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "the", "is", "at", "which", "on", "and", "a", "an", "of", "in", "to", "for", "with", "by",
    "this", "that", "these", "those", "it", "its", "from", "as", "be", "are", "was", "were",
    "have", "has", "had", "but", "not", "or", "if", "when", "where", "there", "here", "my",
    "your", "our", "their", "please", "help", "need", "issue", "problem", "complaint", "regarding"
}

class TrendAnalyzer:
    """
    Analyzes civic issues to detect trends, keywords, and geographic clusters.
    """

    def analyze(self, issues: List[Issue], historical_category_counts: Dict[str, float] = None) -> Dict[str, Any]:
        """
        Analyzes a list of issues to find top keywords, category distribution, and clusters.
        """
        if not issues:
            return {
                "top_keywords": [],
                "category_counts": {},
                "spiking_categories": [],
                "clusters": []
            }

        keywords = self._extract_top_keywords(issues)
        category_counts = self._count_categories(issues)
        spikes = self._detect_spikes(category_counts, historical_category_counts)
        clusters = self._identify_geographic_clustering(issues)

        return {
            "top_keywords": keywords,
            "category_counts": category_counts,
            "spiking_categories": spikes,
            "clusters": clusters
        }

    def _extract_top_keywords(self, issues: List[Issue], top_n: int = 5) -> List[Tuple[str, int]]:
        """Extracts most common words from issue descriptions."""
        all_text = " ".join([issue.description for issue in issues if issue.description]).lower()
        words = re.findall(r'\b[a-z]{3,}\b', all_text) # Words with 3+ chars

        filtered_words = [w for w in words if w not in STOP_WORDS]
        return Counter(filtered_words).most_common(top_n)

    def _count_categories(self, issues: List[Issue]) -> Dict[str, int]:
        """Counts issues per category."""
        categories = [issue.category for issue in issues if issue.category]
        return dict(Counter(categories))

    def _detect_spikes(self, current_counts: Dict[str, int], historical_averages: Dict[str, float]) -> List[str]:
        """
        Identifies categories with a sudden spike in reports (> 50% increase).
        """
        if not historical_averages:
            return []

        spiking = []
        for category, count in current_counts.items():
            avg = historical_averages.get(category, 0)
            if avg > 5 and count > avg * 1.5: # Only consider if historical avg is significant (>5)
                spiking.append(category)

        return spiking

    def _identify_geographic_clustering(self, issues: List[Issue]) -> List[Dict[str, Any]]:
        """
        Uses spatial utilities to find clusters of issues.
        """
        # Filter issues with location
        located_issues = [i for i in issues if i.latitude and i.longitude]

        if not located_issues:
            return []

        # Use DBSCAN via spatial_utils
        # Default eps=30m might be too small for "geographic clustering" of trends.
        # Let's use larger radius like 500m to find hotspots.
        clusters = cluster_issues_dbscan(located_issues, eps_meters=500.0)

        cluster_summaries = []
        for cluster in clusters:
            if len(cluster) < 3: # Ignore small clusters
                continue

            # Find centroid
            lats = [i.latitude for i in cluster]
            lons = [i.longitude for i in cluster]
            avg_lat = sum(lats) / len(lats)
            avg_lon = sum(lons) / len(lons)

            # Most common category in this cluster
            cats = [i.category for i in cluster if i.category]
            top_cat = Counter(cats).most_common(1)[0][0] if cats else "Unknown"

            cluster_summaries.append({
                "count": len(cluster),
                "centroid": {"lat": avg_lat, "lon": avg_lon},
                "dominant_category": top_cat
            })

        # Sort by size
        cluster_summaries.sort(key=lambda x: x["count"], reverse=True)
        return cluster_summaries

trend_analyzer = TrendAnalyzer()
