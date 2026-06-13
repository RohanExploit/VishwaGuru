import collections
import re
from typing import List, Dict, Any, Tuple
from backend.models import Issue
from backend.spatial_utils import cluster_issues_dbscan, get_cluster_representative, calculate_cluster_centroid, HAS_SKLEARN, haversine_distance

class TrendAnalyzer:
    def __init__(self):
        self.stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "is", "are", "was", "were", "be", "been", "this", "that", "these", "those",
            "it", "they", "he", "she", "i", "we", "you", "my", "your", "his", "her", "their",
            "has", "have", "had", "do", "does", "did", "can", "could", "will", "would",
            "should", "must", "may", "might", "from", "up", "down", "out", "over", "under",
            "again", "further", "then", "once", "here", "there", "when", "where", "why",
            "how", "all", "any", "both", "each", "few", "more", "most", "other", "some",
            "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
            "just", "issue", "problem", "please", "help", "need", "urgent", "report", "location",
            "near", "next", "front", "behind", "across"
        }

    def analyze(self, issues: List[Issue]) -> Dict[str, Any]:
        """
        Analyzes a list of issues to identify trends.
        """
        if not issues:
            return {
                "top_keywords": [],
                "category_distribution": {},
                "clusters": [],
                "total_issues": 0
            }

        return {
            "top_keywords": self._extract_keywords(issues),
            "category_distribution": self._analyze_categories(issues),
            "clusters": self._analyze_clusters(issues),
            "total_issues": len(issues)
        }

    def _extract_keywords(self, issues: List[Issue], top_n: int = 5) -> List[Tuple[str, int]]:
        text_corpus = " ".join([issue.description for issue in issues if issue.description]).lower()
        # Remove punctuation
        text_corpus = re.sub(r'[^\w\s]', '', text_corpus)
        words = text_corpus.split()

        filtered_words = [w for w in words if w not in self.stopwords and len(w) > 2]
        counter = collections.Counter(filtered_words)
        return counter.most_common(top_n)

    def _analyze_categories(self, issues: List[Issue]) -> Dict[str, int]:
        categories = [issue.category for issue in issues if issue.category]
        return dict(collections.Counter(categories))

    def _analyze_clusters(self, issues: List[Issue]) -> List[Dict[str, Any]]:
        radius = 100.0 # meters for trend clustering

        if HAS_SKLEARN:
            clusters = cluster_issues_dbscan(issues, eps_meters=radius)
        else:
            clusters = self._simple_clustering(issues, radius_meters=radius)

        analyzed_clusters = []
        for cluster in clusters:
            if len(cluster) < 3: # Ignore small clusters/noise
                continue

            centroid_lat, centroid_lon = calculate_cluster_centroid(cluster)
            representative = get_cluster_representative(cluster)

            analyzed_clusters.append({
                "size": len(cluster),
                "centroid": {"lat": centroid_lat, "lon": centroid_lon},
                "representative_description": representative.description,
                "category": representative.category,
                "representative_id": representative.id
            })

        # Sort by size descending
        analyzed_clusters.sort(key=lambda x: x["size"], reverse=True)
        return analyzed_clusters

    def _simple_clustering(self, issues: List[Issue], radius_meters: float = 100.0) -> List[List[Issue]]:
        """
        A simple greedy clustering algorithm O(N^2) used when sklearn is not available.
        """
        valid_issues = [i for i in issues if i.latitude is not None and i.longitude is not None]
        clusters = []
        visited = set()

        # Sort by location to potentially optimize (not really without spatial index)
        # Just iterate

        for i, issue in enumerate(valid_issues):
            if i in visited:
                continue

            cluster = [issue]
            visited.add(i)

            for j, other_issue in enumerate(valid_issues):
                if j in visited:
                    continue

                # Check if other_issue is close to ANY issue in current cluster?
                # Greedy: Check distance to the seed issue (center-ish)
                # Or checking all-to-all makes it true linkage, but seed-based is faster (K-means like but fixed K)
                # Let's use distance to the seed issue 'issue'.
                dist = haversine_distance(issue.latitude, issue.longitude, other_issue.latitude, other_issue.longitude)
                if dist <= radius_meters:
                    cluster.append(other_issue)
                    visited.add(j)

            clusters.append(cluster)

        return clusters
