import logging
import os
import json
import statistics
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import Issue, Grievance, SeverityLevel
from backend.adaptive_weights import AdaptiveWeights
from backend.trend_analyzer import TrendAnalyzer
from backend.database import SessionLocal
from backend.priority_engine import PriorityEngine
from backend.spatial_utils import haversine_distance

logger = logging.getLogger(__name__)

class CivicIntelligenceEngine:
    def __init__(self, db_session: Session = None):
        self.db = db_session if db_session else SessionLocal()
        self.weights = AdaptiveWeights()
        self.analyzer = TrendAnalyzer()
        self.priority_engine = PriorityEngine() # Uses the same AdaptiveWeights singleton

        self.snapshot_dir = os.path.join(self.weights.data_dir, "dailySnapshots")
        if not os.path.exists(self.snapshot_dir):
            os.makedirs(self.snapshot_dir)

    def refine_daily(self) -> Dict[str, Any]:
        """
        Main entry point for the daily refinement process.
        """
        logger.info("Starting Daily Civic Intelligence Refinement...")

        # 1. Fetch Data
        start_time = datetime.now(timezone.utc) - timedelta(hours=24)
        recent_issues = self.db.query(Issue).filter(Issue.created_at >= start_time).all()

        # Also fetch grievances to check for manual severity overrides
        recent_grievances = self.db.query(Grievance).filter(Grievance.created_at >= start_time).all()

        logger.info(f"Analyzed {len(recent_issues)} issues and {len(recent_grievances)} grievances from last 24h.")

        # 2. Trend Analysis
        trends = self.analyzer.analyze(recent_issues)

        # 3. Adaptive Weight Optimization
        weight_adjustments = self._optimize_weights(recent_issues, recent_grievances)

        # 4. Duplicate Pattern Learning
        duplicate_stats = self._optimize_duplicate_detection(recent_issues)

        # 5. Civic Intelligence Index
        index_score = self._calculate_index(trends, recent_issues, recent_grievances)

        # 6. Generate Report/Snapshot
        snapshot = {
            "date": datetime.now(timezone.utc).isoformat(),
            "civic_intelligence_index": index_score,
            "trends": trends,
            "weight_adjustments": weight_adjustments,
            "duplicate_stats": duplicate_stats,
            "issue_count": len(recent_issues),
            "grievance_count": len(recent_grievances)
        }

        self._save_snapshot(snapshot)

        # 7. Persist updated weights
        self.weights.save_weights()

        logger.info(f"Daily refinement complete. Index: {index_score['score']}")
        return snapshot

    def _optimize_weights(self, issues: List[Issue], grievances: List[Grievance]) -> List[str]:
        adjustments = []

        # Map grievances to issues for severity comparison
        # We need to see if manual severity (in Grievance) differs from predicted

        # Group grievances by category
        category_severity = {} # category -> list of severity levels (0=low, 3=critical)
        severity_map = {
            SeverityLevel.LOW: 0,
            SeverityLevel.MEDIUM: 1,
            SeverityLevel.HIGH: 2,
            SeverityLevel.CRITICAL: 3
        }

        for g in grievances:
            if g.category not in category_severity:
                category_severity[g.category] = []
            category_severity[g.category].append(severity_map.get(g.severity, 0))

        # Check for categories that are consistently high severity
        for category, severities in category_severity.items():
            avg_severity = statistics.mean(severities) if severities else 0

            # If average severity is High/Critical (>= 2.0), ensure category keyword is in High/Critical list
            if avg_severity >= 2.0:
                cat_keyword = category.lower()

                # Check where it currently is
                current_level = "low"
                if any(cat_keyword in self.weights.severity_keywords[k] for k in ["critical"]):
                    current_level = "critical"
                elif any(cat_keyword in self.weights.severity_keywords[k] for k in ["high"]):
                    current_level = "high"
                elif any(cat_keyword in self.weights.severity_keywords[k] for k in ["medium"]):
                    current_level = "medium"

                # Upgrade if needed
                if avg_severity >= 2.5 and current_level != "critical":
                    # Move to critical
                    self._move_keyword(cat_keyword, "critical")
                    adjustments.append(f"Escalated '{cat_keyword}' to Critical severity keywords due to high manual severity.")
                elif avg_severity >= 1.5 and current_level in ["low", "medium"]:
                     # Move to high
                    self._move_keyword(cat_keyword, "high")
                    adjustments.append(f"Escalated '{cat_keyword}' to High severity keywords.")

        return adjustments

    def _move_keyword(self, keyword: str, target_level: str):
        # Remove from all other levels
        for level in self.weights.severity_keywords:
            if keyword in self.weights.severity_keywords[level]:
                self.weights.severity_keywords[level].remove(keyword)

        # Add to target
        if keyword not in self.weights.severity_keywords[target_level]:
            self.weights.severity_keywords[target_level].append(keyword)

    def _optimize_duplicate_detection(self, issues: List[Issue]) -> Dict[str, Any]:
        # Analyze spatial density of NEW issues (that passed duplicate check)
        # If we have many clusters of issues very close to each other (e.g. < 60m) created within 24h,
        # it suggests duplicate radius (50m) might be too small.

        close_pairs = 0
        total_pairs = 0

        valid_issues = [i for i in issues if i.latitude and i.longitude]
        n = len(valid_issues)

        # Check pairs (sample if too many)
        # Just check neighbor distances
        for i in range(n):
            for j in range(i+1, n):
                dist = haversine_distance(valid_issues[i].latitude, valid_issues[i].longitude,
                                          valid_issues[j].latitude, valid_issues[j].longitude)

                if dist < 100: # Only care about close ones
                    total_pairs += 1
                    if dist > 50 and dist < 70:
                        # In the "danger zone" just outside current radius
                        # Check if they are same category
                        if valid_issues[i].category == valid_issues[j].category:
                            close_pairs += 1

        # If we see many pairs just outside the radius, increase radius
        current_radius = self.weights.duplicate_search_radius
        new_radius = current_radius
        reason = "No change"

        if total_pairs > 0 and (close_pairs / total_pairs) > 0.3:
            # >30% of close issues are in 50-70m range and same category
            new_radius = min(current_radius + 5.0, 100.0) # Cap at 100m
            reason = f"Increased radius to {new_radius}m due to dense clustering of similar issues."
        elif total_pairs == 0 and current_radius > 50.0:
            # Decay back to baseline if no clusters found
            new_radius = max(current_radius - 1.0, 50.0)
            reason = "Decreasing radius slightly due to lack of clusters."

        if new_radius != current_radius:
            self.weights.update_duplicate_radius(new_radius)

        return {
            "old_radius": current_radius,
            "new_radius": new_radius,
            "reason": reason,
            "close_pairs_detected": close_pairs
        }

    def _calculate_index(self, trends: Dict, issues: List[Issue], grievances: List[Grievance]) -> Dict[str, Any]:
        # Synthetic score 0-100
        # Factors:
        # - Volume (normalized)
        # - Severity (ratio of high/critical)
        # - Resolution Rate (from grievances)

        if not issues:
            return {"score": 0, "level": "No Data"}

        # 1. Severity Score
        critical_count = sum(1 for g in grievances if g.severity == SeverityLevel.CRITICAL)
        high_count = sum(1 for g in grievances if g.severity == SeverityLevel.HIGH)
        severity_ratio = (critical_count * 2 + high_count) / len(grievances) if grievances else 0
        # Normalize: max possible is 2 (all critical). 2 -> 100, 0 -> 0.
        severity_component = min(severity_ratio * 50, 100)

        # 2. Activity/Engagement Score (Volume)
        # Assume 100 issues/day is "High" activity for this local system?
        volume_component = min(len(issues), 100)

        # 3. Resolution Efficiency (issues resolved / issues created)
        # This is hard to calc on just 24h creation window.
        # Check resolved_at in last 24h
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)
        resolved_count = self.db.query(Issue).filter(Issue.resolved_at >= start_time).count()
        resolution_rate = (resolved_count / len(issues)) if issues else 0
        efficiency_component = min(resolution_rate * 100, 100)

        # Composite Index
        # We want "Civic Intelligence" to reflect "Health/Activity".
        # High score = Good? Or High score = Many problems?
        # "Civic Intelligence Index" usually implies the *system's* intelligence or the *city's* health?
        # Prompt: "Civic Intelligence Index: 72.4 (+3.1 from yesterday)"
        # Let's assume it's a "City Health" or "System Effectiveness" score.
        # High resolution + Moderate volume (engagement) - Low Severity = Good.
        # But "Refining" implies the AI is getting smarter.
        # Let's make it a score of "System Activity & Insight".
        # Score = (Volume * 0.3) + (Severity * 0.3) + (Efficiency * 0.4)

        final_score = (volume_component * 0.3) + (severity_component * 0.3) + (efficiency_component * 0.4)

        return {
            "score": round(final_score, 1),
            "components": {
                "volume": volume_component,
                "severity": severity_component,
                "efficiency": efficiency_component
            },
            "top_concern": trends["top_keywords"][0][0] if trends["top_keywords"] else "None"
        }

    def _save_snapshot(self, data: Dict[str, Any]):
        filename = f"{datetime.now().strftime('%Y-%m-%d')}.json"
        filepath = os.path.join(self.snapshot_dir, filename)
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved daily snapshot to {filepath}")
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")
