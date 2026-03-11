import re
import math
import logging
from typing import List, Dict, Any, Optional
from backend.adaptive_weights import adaptive_weights

logger = logging.getLogger(__name__)

class PriorityEngine:
    """
    A rule-based AI engine for prioritizing civic issues.
    Analyzes text descriptions to determine severity, urgency, and category.
    Now powered by AdaptiveWeights for self-improving intelligence.
    """

    def __init__(self):
        # Cache for compiled regexes to avoid redundant compilation
        self._regex_cache = {
            "urgency": [],
            "categories": {},
            "last_loaded": 0
        }

    def _get_compiled_regexes(self):
        """
        Retrieves or compiles regex patterns, synchronizing with AdaptiveWeights.
        """
        # Trigger reload check in adaptive_weights
        adaptive_weights._check_reload()

        # If weights were reloaded, we need to recompile our regex cache
        if adaptive_weights._last_loaded > self._regex_cache["last_loaded"]:
            logger.info("Recompiling PriorityEngine regex cache due to weights update.")

            # 1. Compile Urgency Patterns
            urgency_patterns = adaptive_weights.get_urgency_patterns()
            compiled_urgency = []
            for pattern, weight in urgency_patterns:
                try:
                    compiled_urgency.append((re.compile(pattern, re.IGNORECASE), weight))
                except re.error as e:
                    logger.error(f"Error compiling urgency pattern '{pattern}': {e}")

            # 2. Categories still use substring matching for semantic correctness
            # (Counting unique keyword matches, not total occurrences)

            self._regex_cache["urgency"] = compiled_urgency
            self._regex_cache["last_loaded"] = adaptive_weights._last_loaded

        return self._regex_cache

    def analyze(self, text: str, image_labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Analyzes the issue text and optional image labels to determine priority.
        """
        text = text.lower()

        # Merge image labels into text for analysis if provided
        combined_text = text
        if image_labels:
            combined_text += " " + " ".join([l.lower() for l in image_labels])

        # Get compiled regexes once for the whole analysis
        regex_cache = self._get_compiled_regexes()

        severity_score, severity_label, severity_reasons = self._calculate_severity(combined_text)
        urgency_score, urgency_reasons = self._calculate_urgency(combined_text, severity_score, regex_cache)
        categories = self._detect_categories(combined_text, regex_cache)

        # Apply Adaptive Category Weights
        multipliers = adaptive_weights.get_category_multipliers()
        max_multiplier = 1.0
        for cat in categories:
            mult = multipliers.get(cat, 1.0)
            if mult > max_multiplier:
                max_multiplier = mult

        if max_multiplier > 1.05: # Threshold to report boost
            # Boost score
            old_score = severity_score
            severity_score = int(severity_score * max_multiplier)
            severity_score = min(100, severity_score)

            # Add reasoning
            if severity_score > old_score:
                severity_reasons.append(f"Severity score boosted by x{max_multiplier:.2f} based on historical trends for this category.")

            # Re-evaluate label based on boosted score
            if severity_score >= 90:
                severity_label = "Critical"
            elif severity_score >= 70:
                severity_label = "High"
            elif severity_score >= 40:
                severity_label = "Medium"
            else:
                # If score boosted from Low to something else, update label
                if severity_score < 40:
                    severity_label = "Low"

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

        severity_keywords = adaptive_weights.get_severity_keywords()

        # Check for critical keywords (highest priority)
        found_critical = [word for word in severity_keywords.get("critical", []) if word in text]
        if found_critical:
            score = 90
            label = "Critical"
            reasons.append(f"Flagged as Critical due to keywords: {', '.join(found_critical[:3])}")

        # Check for high keywords
        if score < 70:
            found_high = [word for word in severity_keywords.get("high", []) if word in text]
            if found_high:
                score = max(score, 70)
                label = "High" if score == 70 else label
                reasons.append(f"Flagged as High Severity due to keywords: {', '.join(found_high[:3])}")

        # Check for medium keywords
        if score < 40:
            found_medium = [word for word in severity_keywords.get("medium", []) if word in text]
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

    def _calculate_urgency(self, text: str, severity_score: int, regex_cache: Dict[str, Any]):
        # Base urgency follows severity
        urgency = severity_score
        reasons = []

        # Apply pre-compiled regex modifiers
        for regex, weight in regex_cache["urgency"]:
            if regex.search(text):
                urgency += weight
                reasons.append(f"Urgency increased by context matching pattern: '{regex.pattern}'")

        # Cap at 100
        urgency = min(100, urgency)

        return urgency, reasons

    def _detect_categories(self, text: str, regex_cache: Dict[str, Any]) -> List[str]:
        scored_categories = []
        # Reverting to original logic for correctness and performance on short strings
        # Counting unique keywords per category as in original implementation
        category_keywords = adaptive_weights.get_category_keywords()

        for category, keywords in category_keywords.items():
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
