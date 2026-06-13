import json
import os
import datetime
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.trend_analyzer import TrendAnalyzer
from backend.adaptive_weights import adaptive_weights
from backend.models import Issue, SeverityLevel

logger = logging.getLogger(__name__)

class CivicIntelligenceEngine:
    """
    Orchestrates daily refinement of the civic intelligence system.
    """

    def __init__(self, data_dir: str = "data"):
        # Resolve absolute path relative to this file to handle Render environment correctly
        # In Render, the app runs from repo root, but data might be mounted or just local
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # repo root
        if data_dir == "data":
             # If default 'data' is used, assume it's at repo root
             self.data_dir = os.path.join(base_dir, "data")
        else:
             self.data_dir = data_dir

        self.snapshots_dir = os.path.join(self.data_dir, "dailySnapshots")
        self.trend_analyzer = TrendAnalyzer()

    def refine_daily(self, db: Session) -> Dict[str, Any]:
        """
        Main entry point for daily refinement job.
        """
        logger.info("Starting daily civic intelligence refinement...")

        # 1. Analyze Trends
        trend_report = self.trend_analyzer.analyze_recent_issues(db, hours=24)

        # 2. Adaptive Weight Optimization
        weight_updates = self._optimize_weights(db, trend_report)

        # 3. Duplicate Pattern Learning
        duplicate_updates = self._refine_duplicate_detection(trend_report)

        # 4. Generate Index
        index_score = self._calculate_index(db, trend_report)

        # 5. Create Snapshot
        snapshot = {
            "date": datetime.datetime.now().strftime("%Y-%m-%d"),
            "timestamp": datetime.datetime.now().isoformat(),
            "civic_intelligence_index": index_score,
            "trends": trend_report,
            "optimizations": {
                "weights": weight_updates,
                "duplicate_detection": duplicate_updates
            }
        }

        self._save_snapshot(snapshot)
        logger.info(f"Daily refinement complete. Index: {index_score}")

        return snapshot

    def _optimize_weights(self, db: Session, trend_report: Dict[str, Any]) -> List[str]:
        """
        Adjust severity weights based on manual overrides or high-frequency keywords in critical issues.
        """
        updates = []
        current_weights = adaptive_weights.get_weights()
        severity_keywords = current_weights.get("severity_keywords", {})

        # Logic: Find keywords in manually marked 'Critical' issues that are currently 'Medium' or 'Low'
        # Since we don't have a clean "manual override" log, we look at issues with status='critical' (if we had that status)
        # or verify if severity column exists in Issue model.
        # Checking Issue model: it has 'upvotes', 'status', 'category'. It does NOT have 'severity' column.
        # 'severity' is in 'Grievance' model!
        # So we should look at Grievances linked to Issues.

        # For now, we'll use a heuristic based on category spikes.
        # If a category is spiking (dominant), we might want to temporarily boost its associated keywords.

        dominant_categories = trend_report.get("category_stats", {}).get("dominant_categories", [])
        categories_map = current_weights.get("categories", {})

        changed = False

        for cat in dominant_categories:
            # If category is spiking, find its keywords
            keywords = categories_map.get(cat, [])
            # Check if these keywords are in 'medium' severity, move to 'high' temporarily?
            # This might be too aggressive.
            # Let's just log it for now.
            updates.append(f"Detected spike in {cat}. Recommendation: Monitor severity weights for {keywords[:3]}")

        # Real adaptation: If "Pothole" is spiking, ensure "pothole" keyword is at least HIGH.
        if "Pothole" in dominant_categories:
            # Check if pothole is in high
            if "pothole" not in severity_keywords.get("high", []) and "pothole" not in severity_keywords.get("critical", []):
                # Move to high
                if "pothole" in severity_keywords.get("medium", []):
                    severity_keywords["medium"].remove("pothole")
                if "pothole" in severity_keywords.get("low", []):
                    severity_keywords["low"].remove("pothole")

                severity_keywords.setdefault("high", []).append("pothole")
                updates.append("Upgraded 'pothole' to HIGH severity due to spike.")
                changed = True

        if changed:
            current_weights["severity_keywords"] = severity_keywords
            adaptive_weights.update_weights(current_weights)

        return updates

    def _refine_duplicate_detection(self, trend_report: Dict[str, Any]) -> List[str]:
        """
        Adjust duplicate detection threshold based on spatial density.
        """
        updates = []
        spatial_stats = trend_report.get("spatial_stats", {})
        avg_dist = spatial_stats.get("avg_neighbor_dist") or 0

        current_radius = adaptive_weights.get_duplicate_search_radius()
        new_radius = current_radius

        # If issues are very close (high density) but distinct (avg dist < current radius/2),
        # it might mean our radius is too small to catch them?
        # No, if they are distinct and < radius, they WOULD have been caught if they were open.
        # So maybe they were reported after the first was resolved?
        # Or maybe the system failed to catch them.

        # Heuristic:
        # If avg neighbor distance is very small (< 20m), users are reporting the same thing. Increase radius to catch more.
        if avg_dist > 0 and avg_dist < 20:
            new_radius = min(current_radius + 5.0, 100.0) # Cap at 100m
            updates.append(f"High spatial density (avg dist {avg_dist}m). Increased duplicate radius to {new_radius}m")

        # If avg neighbor distance is large (> 100m), we can relax the radius to be more precise (reduce false positives)
        elif avg_dist > 100:
             new_radius = max(current_radius - 5.0, 20.0) # Min 20m
             updates.append(f"Low spatial density (avg dist {avg_dist}m). Decreased duplicate radius to {new_radius}m")

        if new_radius != current_radius:
            current_weights = adaptive_weights.get_weights()
            current_weights["duplicate_search_radius"] = new_radius
            adaptive_weights.update_weights(current_weights)

        return updates

    def _calculate_index(self, db: Session, trend_report: Dict[str, Any]) -> float:
        """
        Calculates the Civic Intelligence Index (0-100).
        """
        # 1. Participation Score (Volume)
        total_issues = trend_report.get("total_issues", 0)
        participation_score = min(total_issues * 2, 40) # Cap at 40

        # 2. Resolution Efficiency (simulated as % of verified/resolved in last 24h)
        # We need to query resolved counts
        now = datetime.datetime.now(datetime.timezone.utc)
        start_time = now - datetime.timedelta(hours=24)

        # Count resolved or verified issues in the last 24h
        resolved_count = db.query(Issue).filter(
            ((Issue.status == "resolved") & (Issue.resolved_at >= start_time)) |
            ((Issue.status == "verified") & (Issue.verified_at >= start_time))
        ).count()

        efficiency_score = 0
        if total_issues > 0:
            efficiency_score = (resolved_count / total_issues) * 40
        else:
             efficiency_score = 20 # Baseline if no issues

        efficiency_score = min(efficiency_score, 40)

        # 3. Sentiment/Severity Balance
        # Lower severity average is better? Or handling high severity is better?
        # Let's add a constant base.
        base_score = 20

        index = base_score + participation_score + efficiency_score
        return round(min(index, 100.0), 1)

    def _save_snapshot(self, snapshot: Dict[str, Any]):
        if not os.path.exists(self.snapshots_dir):
            os.makedirs(self.snapshots_dir, exist_ok=True)

        filename = f"{snapshot['date']}.json"
        filepath = os.path.join(self.snapshots_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save snapshot to {filepath}: {e}")
