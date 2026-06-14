from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

from backend.models import Issue

class IntelligenceIndex:
    """
    Calculates the Daily Civic Intelligence Index.
    A composite score reflecting civic engagement, resolution efficiency, and system health.
    """

    def __init__(self):
        pass

    def calculate_score(self, db: Session, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates the daily index score and highlights.
        """
        now = datetime.now(timezone.utc)
        one_day_ago = now - timedelta(hours=24)

        # 1. Metrics Calculation
        # Total issues in last 24h
        total_issues = trend_data.get("total_issues", 0)

        # Resolution Rate (Issues resolved in last 24h / Total active issues or created issues)
        # Let's use: Issues resolved in last 24h
        resolved_count = db.query(func.count(Issue.id)).filter(
            Issue.resolved_at >= one_day_ago
        ).scalar() or 0

        # Verified Count (Issues verified in last 24h)
        verified_count = db.query(func.count(Issue.id)).filter(
            Issue.verified_at >= one_day_ago
        ).scalar() or 0

        # Engagement: Total upvotes in last 24h (approximate, since we don't track upvote time,
        # but we can look at upvotes on issues created in last 24h)
        engagement_score = 0
        if total_issues > 0:
             engagement_score = db.query(func.sum(Issue.upvotes)).filter(
                Issue.created_at >= one_day_ago
            ).scalar() or 0

        # 2. Score Formula (0-100)
        # Base: 50
        # + Resolution Activity (2 points per resolved issue, max 30)
        # + Verification Activity (1 point per verified issue, max 20)
        # + Engagement (0.5 points per upvote, max 20)
        # - High Critical Load (if any critical spikes) - handled via trend_data

        score = 50.0
        score += min(resolved_count * 2.0, 30.0)
        score += min(verified_count * 1.0, 20.0)
        score += min(engagement_score * 0.5, 20.0)

        # Penalize for unaddressed critical spikes (simplified logic)
        spikes = trend_data.get("category_spikes", [])
        if spikes:
            score -= len(spikes) * 2.0

        # Clamp
        score = max(0.0, min(100.0, score))

        # 3. Insights
        top_concern = "None"
        category_distribution = trend_data.get("category_distribution", {})
        if category_distribution:
            top_concern = max(category_distribution, key=category_distribution.get)

        highest_severity_region = "Unknown"
        hotspots = trend_data.get("hotspots", [])
        if hotspots:
            # Just take the top hotspot
            top_hotspot = hotspots[0]
            highest_severity_region = f"Lat {top_hotspot['latitude']}, Lon {top_hotspot['longitude']}"

        return {
            "score": round(score, 1),
            "metrics": {
                "resolved_last_24h": resolved_count,
                "verified_last_24h": verified_count,
                "new_issues_24h": total_issues,
                "engagement_score": engagement_score
            },
            "top_emerging_concern": top_concern,
            "highest_severity_region": highest_severity_region
        }
