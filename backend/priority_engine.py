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
        # We now access weights dynamically from adaptive_weights
        pass

    @property
    def severity_keywords(self) -> Dict[str, List[str]]:
        return adaptive_weights.severity_keywords

    @property
    def urgency_patterns(self) -> List[Any]:
        return adaptive_weights.urgency_patterns

    @property
    def categories(self) -> Dict[str, List[str]]:
        return adaptive_weights.categories

    def analyze(self, text: str, image_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyzes the issue text and optional image labels to determine priority.
        """
        text = text.lower()

        # Merge image labels into text for analysis if provided
        combined_text = text
        if image_labels:
            combined_text += " " + " ".join([l.lower() for l in image_labels])

        severity_score, severity_label, severity_reasons = self._calculate_severity(combined_text)
        categories = self._detect_categories(combined_text)

        # Apply adaptive category weights
        for cat in categories:
            boost = adaptive_weights.category_weights.get(cat, 0.0)
            if boost != 0:
                # Add boost but clamp to 100
                old_score = severity_score
                severity_score = min(100, severity_score + int(boost))
                severity_reasons.append(f"Adaptive boost for category '{cat}': +{boost} (Base: {old_score})")

                # Recalculate label if score increased
                if severity_score >= 90:
                    severity_label = "Critical"
                elif severity_score >= 70:
                    severity_label = "High"
                elif severity_score >= 40:
                    severity_label = "Medium"
                else:
                    severity_label = "Low"

        urgency_score, urgency_reasons = self._calculate_urgency(combined_text, severity_score)

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
        for pattern_data in self.urgency_patterns:
            # Handle potential variation in storage (list or tuple)
            if len(pattern_data) >= 2:
                pattern = pattern_data[0]
                weight = pattern_data[1]
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
