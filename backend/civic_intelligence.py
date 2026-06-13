import json
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import Issue, EscalationAudit, EscalationReason, Grievance
from backend.trend_analyzer import trend_analyzer
from backend.adaptive_weights import adaptive_weights
from backend.database import SessionLocal

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), 'data', 'dailySnapshots')

class CivicIntelligenceEngine:
    def __init__(self):
        os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    def _get_previous_snapshot(self) -> Dict[str, Any]:
        """
        Retrieves the most recent daily snapshot file, if available.
        """
        try:
            files = sorted([f for f in os.listdir(SNAPSHOT_DIR) if f.endswith('.json')])
            if not files:
                return {}

            # Use the most recent file
            latest_file = files[-1]
            with open(os.path.join(SNAPSHOT_DIR, latest_file), 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load previous snapshot: {e}")
            return {}

    def run_daily_cycle(self):
        """
        Main entry point for the daily refinement job.
        Analyzes issues, updates weights, and generates intelligence index.
        """
        logger.info("Starting Daily Civic Intelligence Refinement...")
        db = SessionLocal()
        weight_changes = [] # For auditability

        try:
            now = datetime.now(timezone.utc)
            last_24h = now - timedelta(hours=24)

            # 1. Fetch Data
            # Get issues created in the last 24 hours
            issues_24h = db.query(Issue).filter(Issue.created_at >= last_24h).all()

            # 2. Trend Analysis
            trends = trend_analyzer.analyze(issues_24h)
            logger.info(f"Analyzed {len(issues_24h)} issues.")

            # 2a. Spike Detection
            previous_snapshot = self._get_previous_snapshot()
            previous_dist = previous_snapshot.get('trends', {}).get('category_distribution', {})
            current_dist = trends.get('category_distribution', {})

            spikes = []
            for category, count in current_dist.items():
                prev_count = previous_dist.get(category, 0)
                # Spike definition: > 50% increase AND significant volume (> 5)
                if prev_count > 0 and count > 5:
                    increase = (count - prev_count) / prev_count
                    if increase > 0.5:
                        spikes.append(category)
                elif prev_count == 0 and count > 5:
                     spikes.append(category) # New surge

            trends['spikes'] = spikes

            # 3. Adaptive Weight Optimization (Severity)
            # Find manual severity upgrades in the last 24h
            upgrades = db.query(EscalationAudit).filter(
                EscalationAudit.timestamp >= last_24h,
                EscalationAudit.reason == EscalationReason.SEVERITY_UPGRADE
            ).all()

            # Map upgrades to categories
            upgrade_counts = {}

            # Optimization: Fetch all related grievances in one query to avoid N+1
            grievance_ids = [audit.grievance_id for audit in upgrades]
            if grievance_ids:
                grievances = db.query(Grievance).filter(Grievance.id.in_(grievance_ids)).all()
                grievance_map = {g.id: g for g in grievances}
            else:
                grievance_map = {}

            for audit in upgrades:
                grievance = grievance_map.get(audit.grievance_id)
                if grievance and grievance.category:
                    upgrade_counts[grievance.category] = upgrade_counts.get(grievance.category, 0) + 1

            # Update weights if threshold met
            for category, count in upgrade_counts.items():
                if count >= 3: # Threshold for auto-adjustment
                    old_multipliers = adaptive_weights.get_category_multipliers()
                    old_weight = old_multipliers.get(category, 1.0)

                    # Increase weight by 10%
                    adaptive_weights.update_category_weight(category, 1.1)

                    # Verify new weight (fetch fresh)
                    new_multipliers = adaptive_weights.get_category_multipliers()
                    new_weight = new_multipliers.get(category, 1.1)

                    weight_changes.append({
                        "category": category,
                        "old_weight": old_weight,
                        "new_weight": new_weight,
                        "reason": f"Manual severity upgrades count: {count}"
                    })
                    logger.info(f"Increased severity weight for {category} due to {count} manual upgrades.")

            # 4. Duplicate Pattern Learning (Radius Adjustment)
            # Heuristic: High clustering density suggests we might need larger radius to group effectively
            # or if many duplicate/nearby issues are found.
            clusters = trends.get('clusters', [])
            cluster_count = len(clusters)

            current_radius = adaptive_weights.get_duplicate_search_radius()
            radius_update_factor = 1.0

            if cluster_count > 5:
                # High clustering activity, increase radius slightly to ensure we catch neighbors
                radius_update_factor = 1.05
            elif cluster_count == 0 and len(issues_24h) > 50:
                # Many issues but no clusters detected - radius might be too small
                radius_update_factor = 1.05
            elif len(issues_24h) < 10 and current_radius > 50:
                # Low volume, maybe decay radius back to default if it grew too large
                radius_update_factor = 0.95

            if radius_update_factor != 1.0:
                adaptive_weights.update_duplicate_radius(radius_update_factor)
                new_radius = adaptive_weights.get_duplicate_search_radius()
                weight_changes.append({
                    "category": "GLOBAL_DUPLICATE_RADIUS",
                    "old_weight": current_radius,
                    "new_weight": new_radius,
                    "reason": f"Cluster density analysis (clusters: {cluster_count}, issues: {len(issues_24h)})"
                })

            # 5. Civic Intelligence Index
            index_data = self._calculate_index(db, issues_24h, trends)

            # 6. Snapshot
            snapshot = {
                "date": now.isoformat(),
                "trends": trends,
                "civic_index": index_data,
                "weight_updates": upgrade_counts,
                "weight_changes": weight_changes,
                "model_weights": adaptive_weights._weights if adaptive_weights._weights else {}
            }

            filename = f"{now.strftime('%Y-%m-%d')}.json"
            filepath = os.path.join(SNAPSHOT_DIR, filename)

            # Atomic write (write to temp then rename) not strictly necessary for this file but good practice
            # using simple write for now
            with open(filepath, 'w') as f:
                json.dump(snapshot, f, indent=2)

            logger.info(f"Daily snapshot saved to {filepath}")

        except Exception as e:
            logger.error(f"Error in daily civic intelligence cycle: {e}", exc_info=True)
        finally:
            db.close()

    def _calculate_index(self, db: Session, issues_24h: List[Issue], trends: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a daily 'Civic Intelligence Index' score.
        """
        total_new = len(issues_24h)

        now = datetime.now(timezone.utc)
        last_24h = now - timedelta(hours=24)

        # Count resolutions in last 24h
        resolved_count = db.query(Issue).filter(
            Issue.resolved_at >= last_24h
        ).count()

        # Score Calculation
        # Base: 70
        # +2 per resolution
        # -0.5 per new issue (burden)
        score = 70.0
        score += (resolved_count * 2.0)
        score -= (total_new * 0.5)

        # Clamp 0-100
        score = max(0.0, min(100.0, score))

        # Top emerging concern
        top_cat = "None"
        category_dist = trends.get('category_distribution', {})
        if category_dist:
            top_cat = max(category_dist, key=category_dist.get)

        # Highest severity region (from clusters)
        highest_severity_region = "None"
        clusters = trends.get('clusters', [])
        if clusters:
            # Assume first cluster is largest/most significant
            # In real app, we would reverse geocode the lat/lon to get Ward/Area name
            # For now, just return lat/lon
            top_cluster = clusters[0]
            highest_severity_region = f"Lat {top_cluster['latitude']:.4f}, Lon {top_cluster['longitude']:.4f}"

        return {
            "score": round(score, 1),
            "new_issues_count": total_new,
            "resolved_issues_count": resolved_count,
            "top_emerging_concern": top_cat,
            "highest_severity_region": highest_severity_region
        }

civic_intelligence_engine = CivicIntelligenceEngine()
