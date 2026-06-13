import re
import math
from typing import List, Dict, Any, Optional
from backend.adaptive_weights import adaptive_weights

class PriorityEngine:
    """
    A rule-based AI engine for prioritizing civic issues.
    Analyzes text descriptions to determine severity, urgency, and category.
    """

    def __init__(self):
        # Load weights from adaptive engine
        weights = adaptive_weights.get_weights()

        self.severity_keywords = weights.get("severity_keywords", {})
        self.urgency_patterns = weights.get("urgency_patterns", [])
        self.categories = weights.get("categories", {})

    def reload_weights(self):
        """Reloads weights from the adaptive engine."""
        weights = adaptive_weights.get_weights()
        self.severity_keywords = weights.get("severity_keywords", {})
        self.urgency_patterns = weights.get("urgency_patterns", [])
        self.categories = weights.get("categories", {})

    def analyze(self, text: str, image_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyzes the issue text and optional image labels to determine priority.
        """
        # Ensure we have the latest weights if they might change at runtime (optional optimization)
        # self.reload_weights()

        text = text.lower()

        # Merge image labels into text for analysis if provided
        combined_text = text
        if image_labels:
            combined_text += " " + " ".join([l.lower() for l in image_labels])

        severity_score, severity_label, severity_reasons = self._calculate_severity(combined_text)
        urgency_score, urgency_reasons = self._calculate_urgency(combined_text, severity_score)
        categories = self._detect_categories(combined_text)

        # Explainability
        reasoning = severity_reasons + urgency_reasons
        if not reasoning:
            reasoning = ["Standard priority based on general keywords."]

        return {
            "severity": severity_label,
            "severity_score": severity_score, # 0-100 normalized
            "urgency_score": urgency_score, # 0-100
            "suggested_categories": categories,
            "reasoning": reasoning
        }

    def _calculate_severity(self, text: str):
        score = 0
        reasons = []
        label = "Low"

        # Check for critical keywords (highest priority)
        found_critical = [word for word in self.severity_keywords.get("critical", []) if word in text]
        if found_critical:
            score = 90
            label = "Critical"
            reasons.append(f"Flagged as Critical due to keywords: {', '.join(found_critical[:3])}")

        # Check for high keywords
        if score < 70:
            found_high = [word for word in self.severity_keywords.get("high", []) if word in text]
            if found_high:
                score = max(score, 70)
                label = "High" if score == 70 else label
                reasons.append(f"Flagged as High Severity due to keywords: {', '.join(found_high[:3])}")

        # Check for medium keywords
        if score < 40:
            found_medium = [word for word in self.severity_keywords.get("medium", []) if word in text]
            if found_medium:
                score = max(score, 40)
                label = "Medium" if score == 40 else label
                reasons.append(f"Flagged as Medium Severity due to keywords: {', '.join(found_medium[:3])}")

        # Default to low
        if score == 0:
            score = 10
            label = "Low"
            reasons.append("Classified as Low Severity (maintenance/cosmetic issue)")

        return score, label, reasons

    def _calculate_urgency(self, text: str, severity_score: int):
        # Base urgency follows severity
        urgency = severity_score
        reasons = []

        # Apply regex modifiers
        for pattern, weight in self.urgency_patterns:
            if re.search(pattern, text):
                urgency += weight
                reasons.append(f"Urgency increased by context matching pattern: '{pattern}'")

        # Cap at 100
        urgency = min(100, urgency)

        return urgency, reasons

    def _detect_categories(self, text: str) -> List[str]:
        # Sort categories by length of match to prioritize specific over general?
        # Or just count matches.

        scored_categories = []
        for category, keywords in self.categories.items():
            count = 0
            for k in keywords:
                if k in text:
                    count += 1

            if count > 0:
                scored_categories.append((category, count))

        # Sort by count desc
        scored_categories.sort(key=lambda x: x[1], reverse=True)

        return [c[0] for c in scored_categories[:3]]

# Singleton instance
priority_engine = PriorityEngine()
