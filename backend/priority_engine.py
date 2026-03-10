import re
import math
from typing import List, Dict, Any, Optional
from backend.adaptive_weights import adaptive_weights

import logging

logger = logging.getLogger(__name__)

class PriorityEngine:
    """
    A rule-based AI engine for prioritizing civic issues.
    Analyzes text descriptions to determine severity, urgency, and category.
    Now powered by AdaptiveWeights for self-improving intelligence.
    """

    def __init__(self):
        self._regex_cache = {}
        self._recompile_cache()

    def _recompile_cache(self):
        """
        Pre-compiles regular expressions for high-performance matching.
        Consolidates keywords into single regex patterns to avoid iterative checks.
        """
        # 1. Severity Keywords Cache (Consolidated patterns for each level)
        severity_keywords = adaptive_weights.get_severity_keywords()
        self._regex_cache['severity'] = {}
        for level, keywords in severity_keywords.items():
            if keywords:
                # Escape and join keywords. Word boundaries are tricky with multi-word keywords.
                # We'll use a simple alternation and rely on re.IGNORECASE if needed (already lowercased).
                pattern = '(' + '|'.join([re.escape(k) for k in keywords]) + ')'
                self._regex_cache['severity'][level] = re.compile(pattern)

        # 2. Urgency Patterns Cache
        urgency_patterns = adaptive_weights.get_urgency_patterns()
        self._regex_cache['urgency'] = []
        for pattern, weight in urgency_patterns:
            try:
                self._regex_cache['urgency'].append((re.compile(pattern), weight))
            except re.error as e:
                logger.error(f"Invalid urgency pattern '{pattern}': {e}")

        logger.info("PriorityEngine regex cache recompiled.")

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
        urgency_score, urgency_reasons = self._calculate_urgency(combined_text, severity_score)
        categories = self._detect_categories(combined_text)

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

        # Check if cache needs update (AdaptiveWeights handles the throttle)
        if adaptive_weights._check_reload():
            self._recompile_cache()

        severity_cache = self._regex_cache.get('severity', {})

        # Check for critical keywords (highest priority)
        critical_regex = severity_cache.get('critical')
        if critical_regex:
            matches = critical_regex.findall(text)
            if matches:
                score = 90
                label = "Critical"
                reasons.append(f"Flagged as Critical due to keywords: {', '.join(list(dict.fromkeys(matches))[:3])}")

        # Check for high keywords
        if score < 70:
            high_regex = severity_cache.get('high')
            if high_regex:
                matches = high_regex.findall(text)
                if matches:
                    score = max(score, 70)
                    label = "High" if score == 70 else label
                    reasons.append(f"Flagged as High Severity due to keywords: {', '.join(list(dict.fromkeys(matches))[:3])}")

        # Check for medium keywords
        if score < 40:
            medium_regex = severity_cache.get('medium')
            if medium_regex:
                matches = medium_regex.findall(text)
                if matches:
                    score = max(score, 40)
                    label = "Medium" if score == 40 else label
                    reasons.append(f"Flagged as Medium Severity due to keywords: {', '.join(list(dict.fromkeys(matches))[:3])}")

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

        urgency_cache = self._regex_cache.get('urgency', [])

        # Apply pre-compiled regex modifiers
        for pattern_re, weight in urgency_cache:
            if pattern_re.search(text):
                urgency += weight
                reasons.append(f"Urgency increased by context matching pattern: '{pattern_re.pattern}'")

        # Cap at 100
        urgency = min(100, urgency)

        return urgency, reasons

    def _detect_categories(self, text: str) -> List[str]:
        categories_map = adaptive_weights.get_category_keywords()

        scored_categories = []
        for category, keywords in categories_map.items():
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
