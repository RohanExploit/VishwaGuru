import json
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Set

from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import Issue, Grievance, SeverityLevel, GrievanceStatus
from backend.adaptive_weights import adaptive_weights
from backend.trend_analyzer import trend_analyzer
# from backend.priority_engine import priority_engine # Not strictly needed here unless we re-run priority check

logger = logging.getLogger(__name__)

# Use absolute path relative to repo root data directory
# This file is in backend/civic_intelligence.py
# Repo root is ../../
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SNAPSHOT_DIR = os.path.join(BASE_DIR, "data", "dailySnapshots")

class CivicIntelligenceEngine:
    """
    Orchestrates daily refinement of the civic intelligence system.
    """

    def refine_daily(self, db: Session) -> Dict[str, Any]:
        """
        Runs the daily analysis and refinement process.
        """
        logger.info("Starting daily civic intelligence refinement...")

        # 1. Fetch data from last 24h
        # Ensure we use UTC aware datetime if models use it
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=24)

        # We might need to handle timezone naive/aware mismatch depending on DB driver
        # But assuming consistency with models.py

        issues_24h = db.query(Issue).filter(Issue.created_at >= start_time).all()
        grievances_24h = db.query(Grievance).filter(Grievance.created_at >= start_time).all()

        logger.info(f"Analyzed {len(issues_24h)} issues and {len(grievances_24h)} grievances from last 24h.")

        # 2. Trend Analysis
        previous_snapshot = self._load_last_snapshot()
        historical_counts = previous_snapshot.get("trends", {}).get("category_counts", {}) if previous_snapshot else {}

        trends = trend_analyzer.analyze(issues_24h, historical_counts)

        # 3. Adaptive Weight Optimization
        weight_updates = self._optimize_weights(db, grievances_24h)
        self._adjust_duplicate_threshold(issues_24h)

        # 4. Civic Intelligence Index
        index_score = self._calculate_index(issues_24h, grievances_24h)
        previous_score = previous_snapshot.get("index_score", 50.0) if previous_snapshot else 50.0
        index_change = index_score - previous_score

        # 5. Generate Snapshot
        snapshot = {
            "date": end_time.strftime("%Y-%m-%d"),
            "timestamp": end_time.isoformat(),
            "index_score": round(index_score, 2),
            "index_change": round(index_change, 2),
            "stats": {
                "total_issues": len(issues_24h),
                "total_grievances": len(grievances_24h),
                "resolved_grievances": sum(1 for g in grievances_24h if g.status == GrievanceStatus.RESOLVED)
            },
            "trends": trends,
            "weight_updates": weight_updates
        }

        self._save_snapshot(snapshot)
        logger.info(f"Daily refinement complete. Index: {index_score}")

        return snapshot

    def _adjust_duplicate_threshold(self, issues: List[Issue]):
        """
        Dynamically adjusts duplicate detection threshold based on duplicate rate.
        """
        total = len(issues)
        if total < 10:
            return

        # Assuming 'duplicate' status indicates a duplicate issue
        duplicates = len([i for i in issues if i.status == 'duplicate'])
        rate = duplicates / total

        current_radius = adaptive_weights.duplicate_search_radius

        # Simple heuristic:
        # If too many duplicates (> 30%), we might be over-matching (radius too big).
        # If too few (< 5%), we might be under-matching (radius too small).
        # This is a naive control loop but satisfies the requirement.

        if rate > 0.3:
            new_radius = max(10.0, current_radius * 0.9)
            if new_radius != current_radius:
                adaptive_weights.duplicate_search_radius = new_radius
                logger.info(f"High duplicate rate ({rate:.2f}). Decreased duplicate search radius to {new_radius:.1f}m")
        elif rate < 0.05:
            new_radius = min(100.0, current_radius * 1.1)
            if new_radius != current_radius:
                adaptive_weights.duplicate_search_radius = new_radius
                logger.info(f"Low duplicate rate ({rate:.2f}). Increased duplicate search radius to {new_radius:.1f}m")

    def _optimize_weights(self, db: Session, grievances: List[Grievance]) -> List[str]:
        """
        Adjusts weights based on discrepancies between predicted and actual severity.
        """
        updates = []

        # Filter for critical grievances
        critical_grievances = [g for g in grievances if g.severity == SeverityLevel.CRITICAL]

        if not critical_grievances:
            return updates

        # Get linked issues to analyze text
        # Since we have issue_id on Grievance
        issue_ids = [g.issue_id for g in critical_grievances if g.issue_id]
        if not issue_ids:
            return updates

        critical_issues = db.query(Issue).filter(Issue.id.in_(issue_ids)).all()

        # Analyze text for common keywords in these critical issues
        # We can reuse TrendAnalyzer logic but specific to this subset
        top_keywords = trend_analyzer._extract_top_keywords(critical_issues, top_n=10)

        # Check if any top keyword is NOT in current critical keywords
        current_critical_keywords = set(adaptive_weights.severity_keywords.get("critical", []))

        for keyword, count in top_keywords:
            if count >= 3 and keyword not in current_critical_keywords:
                # Add to adaptive weights
                logger.info(f"Auto-learning: Adding '{keyword}' to critical severity keywords due to frequency in critical reports.")
                adaptive_weights.update_severity_keyword("critical", keyword, add=True)
                updates.append(f"Added '{keyword}' to Critical keywords")

        return updates

    def _calculate_index(self, issues: List[Issue], grievances: List[Grievance]) -> float:
        """
        Calculates the Civic Intelligence Index (0-100).
        High score = Good civic health (few critical issues, high resolution).
        """
        base_score = 70.0 # Start higher

        if not issues and not grievances:
            return base_score

        # Factor 1: Engagement (More issues is good? Or bad? Prompt says "Civic Intelligence Index"
        # usually implies the SYSTEM's intelligence or CITY's performance.
        # "Top Emerging Concern: Water Supply" implies monitoring.
        # Let's assume High Index = Healthy System/City.

        # High resolution rate -> +
        resolved_count = sum(1 for g in grievances if g.status == GrievanceStatus.RESOLVED)
        total_grievances = len(grievances)
        resolution_rate = (resolved_count / total_grievances) if total_grievances > 0 else 0
        resolution_score = resolution_rate * 30 # Max 30 points

        # High severity -> -
        severity_counts = {
            SeverityLevel.LOW: 0,
            SeverityLevel.MEDIUM: 0,
            SeverityLevel.HIGH: 0,
            SeverityLevel.CRITICAL: 0
        }
        for g in grievances:
            if g.severity in severity_counts:
                severity_counts[g.severity] += 1

        # Weighted penalty
        penalty = (severity_counts[SeverityLevel.CRITICAL] * 5) + \
                  (severity_counts[SeverityLevel.HIGH] * 2) + \
                  (severity_counts[SeverityLevel.MEDIUM] * 0.5)

        # Normalize penalty (don't go below 0 for this part)
        # Cap penalty at 40
        severity_penalty = min(40, penalty)

        final_score = base_score + resolution_score - severity_penalty
        return max(0, min(100, final_score))

    def _save_snapshot(self, snapshot: Dict[str, Any]):
        filename = f"{SNAPSHOT_DIR}/{snapshot['date']}.json"

        # Ensure directory exists (redundant if setup correctly but safe)
        if not os.path.exists(SNAPSHOT_DIR):
            os.makedirs(SNAPSHOT_DIR, exist_ok=True)

        try:
            with open(filename, 'w') as f:
                json.dump(snapshot, f, indent=4)
        except Exception as e:
            logger.error(f"Failed to save snapshot: {e}")

    def _load_last_snapshot(self) -> Dict[str, Any]:
        """Loads the most recent snapshot."""
        if not os.path.exists(SNAPSHOT_DIR):
            return {}

        files = sorted([f for f in os.listdir(SNAPSHOT_DIR) if f.endswith(".json")])
        if not files:
            return {}

        last_file = files[-1]
        try:
            with open(os.path.join(SNAPSHOT_DIR, last_file), 'r') as f:
                return json.load(f)
        except Exception:
            return {}

civic_intelligence_engine = CivicIntelligenceEngine()
