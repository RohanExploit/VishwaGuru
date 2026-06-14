import json
import os
import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.adaptive_weights import AdaptiveWeights
from backend.trend_analyzer import TrendAnalyzer
from backend.intelligence_index import IntelligenceIndex
from backend.models import EscalationAudit, Issue, SeverityLevel, Grievance

logger = logging.getLogger(__name__)

class CivicIntelligenceEngine:
    """
    The central engine for daily civic intelligence refinement.
    Orchestrates trend analysis, weight adaptation, and index calculation.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CivicIntelligenceEngine, cls).__new__(cls)
            cls._instance.weights_manager = AdaptiveWeights()
            cls._instance.trend_analyzer = TrendAnalyzer()
            cls._instance.intelligence_index = IntelligenceIndex()
        return cls._instance

    def refine_daily(self, db: Session):
        """
        Runs the daily refinement process.
        """
        logger.info("Starting Daily Civic Intelligence Refinement...")

        # 1. Trend Detection
        trend_data = self.trend_analyzer.analyze_trends(db)

        # 2. Adaptive Weight Optimization
        self._optimize_weights(db)
        self._optimize_keywords(db, trend_data)
        self._optimize_duplicates(trend_data)

        # 3. Civic Intelligence Index
        index_data = self.intelligence_index.calculate_score(db, trend_data)

        # 4. Generate Snapshot
        snapshot = {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "civic_intelligence_index": index_data,
            "trends": trend_data,
            "weights_version": "v1.0", # Could be dynamic
            "weights_snapshot": self.weights_manager.get_weights()
        }

        self._save_snapshot(snapshot)

        logger.info(f"Daily Refinement Complete. Index Score: {index_data['score']}")
        return snapshot

    def _optimize_weights(self, db: Session):
        """
        Adjusts weights based on manual feedback (escalations and high severity reports).
        """
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(hours=24)

        # Find critical/high grievances from last 24h
        # We look for patterns where a category is consistently marked high/critical
        high_severity_grievances = db.query(Grievance.category, func.count(Grievance.id))\
            .filter(Grievance.created_at >= one_day_ago)\
            .filter(Grievance.severity.in_([SeverityLevel.CRITICAL, SeverityLevel.HIGH]))\
            .group_by(Grievance.category).all()

        for category, count in high_severity_grievances:
            # If we see many high severity issues for a category, ensure mapping reflects it
            if count >= 3: # Threshold
                current_mapping = self.weights_manager.severity_mapping.get(category.lower())

                # If current mapping is lower (medium/low), upgrade it
                # Logic: If it's mapped to 'low' or 'medium', but we see 3+ high/critical, upgrade to 'high'
                # If we see 5+ critical, upgrade to 'critical' (simplified)

                if current_mapping in ['low', 'medium']:
                    logger.info(f"Auto-adjusting severity for category '{category}' to 'high' due to {count} high/critical reports.")
                    self.weights_manager.update_severity_mapping(category, 'high')

    def _optimize_keywords(self, db: Session, trend_data: dict):
        """
        Adds trending keywords to category dictionaries if strong correlation is found.
        """
        top_keywords = trend_data.get("top_keywords", [])

        for kw_obj in top_keywords:
            keyword = kw_obj["keyword"]

            # Skip if keyword already known
            # (Checking all categories is expensive, just check if we should add it)

            # Find issues with this keyword in last 24h
            now = datetime.now(timezone.utc)
            one_day_ago = now - timedelta(hours=24)

            issues_with_kw = db.query(Issue.category, func.count(Issue.id))\
                .filter(Issue.created_at >= one_day_ago)\
                .filter(Issue.description.ilike(f"%{keyword}%"))\
                .group_by(Issue.category).all()

            total_with_kw = sum(count for _, count in issues_with_kw)

            if total_with_kw >= 3: # Minimum significance
                for category, count in issues_with_kw:
                    # If category accounts for > 60% of usage, assign keyword
                    if count / total_with_kw > 0.6:
                        # Check if already in category
                        current_keywords = self.weights_manager.categories.get(category, [])
                        if keyword not in current_keywords:
                            logger.info(f"Auto-adding keyword '{keyword}' to category '{category}'")
                            self.weights_manager.add_keyword_to_category(category, keyword)

    def _optimize_duplicates(self, trend_data: dict):
        """
        Adjusts duplicate search radius based on issue density.
        """
        hotspots = trend_data.get("hotspots", [])
        if not hotspots:
            return

        # Get density of top hotspot
        top_hotspot = hotspots[0]
        count = top_hotspot.get("count", 0)

        current_radius = self.weights_manager.duplicate_search_radius

        # Logic: If many issues in one spot (high density), increase radius to catch duplicates better
        if count >= 10 and current_radius < 100:
            new_radius = min(current_radius + 10.0, 100.0)
            logger.info(f"High issue density detected. Increasing duplicate search radius to {new_radius}m")
            self.weights_manager.duplicate_search_radius = new_radius
            self.weights_manager.save_weights()

        # Logic: If density is very low but we have many issues, maybe decrease radius?
        # (Omitted for safety to avoid missing duplicates)

    def _save_snapshot(self, snapshot: dict):
        """Saves the daily snapshot to JSON."""
        snapshot_dir = "data/dailySnapshots"
        os.makedirs(snapshot_dir, exist_ok=True)

        filename = f"{snapshot['date']}.json"
        filepath = os.path.join(snapshot_dir, filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=4)
            logger.info(f"Saved daily snapshot to {filepath}")
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

# Global instance accessor
def get_civic_intelligence_engine():
    return CivicIntelligenceEngine()
