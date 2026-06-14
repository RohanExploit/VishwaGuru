import json
import os
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import Issue, Grievance, SeverityLevel, EscalationReason, EscalationAudit
from backend.trend_analyzer import trend_analyzer
from backend.adaptive_weights import adaptive_weights

logger = logging.getLogger(__name__)

class CivicIntelligenceEngine:
    """
    Orchestrates daily refinement of the civic intelligence system.
    """
    SNAPSHOT_DIR = "data/dailySnapshots"

    def __init__(self):
        os.makedirs(self.SNAPSHOT_DIR, exist_ok=True)

    def refine_daily(self, db: Session):
        logger.info("Starting daily civic intelligence refinement...")

        # 1. Trend Analysis
        trends = trend_analyzer.analyze_trends(db, time_window_hours=24)

        # 2. Adaptive Weight Optimization (Severity Learning)
        self._optimize_severity_weights(db, trends)

        # 3. Duplicate Threshold Adjustment
        self._adjust_duplicate_threshold(db)

        # 4. Calculate Civic Index
        index_data = self._calculate_civic_index(db, trends)

        # 5. Save Snapshot
        self._save_snapshot(index_data, trends)

        logger.info("Daily refinement complete.")
        return index_data

    def _optimize_severity_weights(self, db: Session, trends: dict):
        """
        Adjusts weights based on discrepancies between initial AI severity and final manual severity.
        """
        # Look for grievances where severity was upgraded manually
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        # Handle case where EscalationAudit table might be empty or not used yet
        try:
            upgrades = db.query(EscalationAudit).filter(
                EscalationAudit.timestamp >= cutoff_time,
                EscalationAudit.reason == EscalationReason.SEVERITY_UPGRADE
            ).all()
        except Exception as e:
            logger.warning(f"Could not query EscalationAudit: {e}")
            upgrades = []

        category_upgrades = {}

        for audit in upgrades:
            # Safely access grievance relationship
            grievance = audit.grievance
            if grievance and grievance.category:
                category_upgrades[grievance.category] = category_upgrades.get(grievance.category, 0) + 1

        # If a category has multiple upgrades, boost its weight
        for category, count in category_upgrades.items():
            if count >= 3: # Threshold: at least 3 manual upgrades in 24h
                logger.info(f"Boosting severity weight for category '{category}' due to {count} manual upgrades.")
                adaptive_weights.update_category_weight(category, 5.0) # Boost by 5 points

        # Also check trend spikes - if a category is spiking, maybe boost it slightly to prioritize
        for spike in trends.get("category_spikes", []):
            cat = spike["category"]
            count = spike["count"]
            if count > 10: # Significant spike
                 # Only boost if not already boosted heavily
                 current_boost = adaptive_weights.category_weights.get(cat, 0)
                 if current_boost < 10:
                     adaptive_weights.update_category_weight(cat, 2.0)
                     logger.info(f"Boosting severity weight for spiking category '{cat}'")

    def _adjust_duplicate_threshold(self, db: Session):
        """
        Adjusts the search radius for duplicates based on near-duplicate patterns.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        issues = db.query(Issue).filter(Issue.created_at >= cutoff_time).all()
        current_radius = adaptive_weights.duplicate_search_radius

        # Check for "near misses": issues created within (radius, radius*1.5) distance
        near_miss_count = 0
        from backend.spatial_utils import haversine_distance

        # O(N^2) check - optimization: only check if N is reasonable
        if len(issues) < 500:
            for i in range(len(issues)):
                for j in range(i + 1, len(issues)):
                    if issues[i].latitude and issues[j].latitude and issues[i].longitude and issues[j].longitude:
                        dist = haversine_distance(
                            issues[i].latitude, issues[i].longitude,
                            issues[j].latitude, issues[j].longitude
                        )
                        # Check if issues are just outside the current radius
                        if current_radius < dist < current_radius * 1.5:
                             # We could also check text similarity here, but simplified to spatial for now
                             near_miss_count += 1

        if near_miss_count > 5:
            # We have multiple issues just outside the radius. Increase radius.
            new_radius = min(100.0, current_radius + 5.0)
            adaptive_weights.update_duplicate_search_radius(new_radius)
            logger.info(f"Increased duplicate search radius to {new_radius}m due to {near_miss_count} near-misses.")
        elif near_miss_count == 0 and current_radius > 30.0:
            # No near misses, maybe we can tighten it?
            new_radius = max(20.0, current_radius - 1.0)
            adaptive_weights.update_duplicate_search_radius(new_radius)
            logger.info(f"Decreased duplicate search radius to {new_radius}m (optimization).")

    def _calculate_civic_index(self, db: Session, trends: dict) -> dict:
        """
        Calculates the daily Civic Intelligence Index.
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)

        resolved_count = db.query(func.count(Issue.id)).filter(
            Issue.resolved_at >= cutoff_time
        ).scalar() or 0

        created_count = trends["total_issues"]

        # Calculate score (Arbitrary Formula)
        base_score = 60.0

        # Resolution Bonus
        res_bonus = min(30.0, resolved_count * 2.0)

        # Trend Coverage Bonus
        hotspot_bonus = min(10.0, len(trends["cluster_hotspots"]) * 2.0)

        score = base_score + res_bonus + hotspot_bonus
        score = min(100.0, score)

        # Compare with yesterday (load previous snapshot)
        prev_score = self._get_previous_score()
        change = round(score - prev_score, 1)

        # Identifying top concern
        top_concern = "General"
        if trends["category_spikes"]:
            top_concern = trends["category_spikes"][0]["category"]

        # Highest severity region
        highest_severity_region = "Unknown"
        if trends["cluster_hotspots"]:
            # Pick the busiest hotspot
            best = trends["cluster_hotspots"][0]
            highest_severity_region = f"Lat: {best['latitude']:.3f}, Lon: {best['longitude']:.3f}"

        return {
            "score": round(score, 1),
            "change": change,
            "top_concern": top_concern,
            "highest_severity_region": highest_severity_region,
            "metrics": {
                "resolved_last_24h": resolved_count,
                "created_last_24h": created_count
            }
        }

    def _get_previous_score(self) -> float:
        # Load latest snapshot
        try:
            files = sorted(os.listdir(self.SNAPSHOT_DIR))
            if not files:
                return 60.0

            last_file = files[-1]
            with open(os.path.join(self.SNAPSHOT_DIR, last_file), 'r') as f:
                data = json.load(f)
                return data.get("index", {}).get("score", 60.0)
        except Exception:
            return 60.0

    def _save_snapshot(self, index_data: dict, trends: dict):
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filepath = os.path.join(self.SNAPSHOT_DIR, f"{date_str}.json")

        # Serialize datetime objects in trends if necessary
        # TrendAnalyzer output contains built-in types mostly.

        snapshot = {
            "date": date_str,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "index": index_data,
            "trends": trends,
            "weights_version": adaptive_weights.weights # snapshot current weights
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=4)
            logger.info(f"Saved daily snapshot to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

civic_engine = CivicIntelligenceEngine()
