import re
import math
from typing import List, Dict, Any, Optional
from backend.adaptive_weights import adaptive_weights


class PriorityEngine:
    """
    A rule-based AI engine for prioritizing civic issues.
    Analyzes text descriptions to determine severity, urgency, and category.
    Now powered by AdaptiveWeights for self-improving intelligence.
    """

    def __init__(self):
        # Cache for pre-compiled regex patterns and configuration weights
        self._regex_cache = []
        self._severity_keywords = {}
        self._category_keywords = {}
        self._category_multipliers = {}
        self._last_reload_count = -1

    def _ensure_weights_cache(self):
        """
        Synchronizes the local cache with adaptive_weights configuration.
        Throttled by reload_count to avoid redundant dictionary access.
        """
        current_reload_count = adaptive_weights.reload_count
        if self._last_reload_count != current_reload_count:
            # Cache literal keywords and multipliers
            self._severity_keywords = adaptive_weights.get_severity_keywords()
            self._category_keywords = adaptive_weights.get_category_keywords()
            self._category_multipliers = adaptive_weights.get_category_multipliers()

            # Cache regex patterns for urgency
            urgency_patterns = adaptive_weights.get_urgency_patterns()
            self._regex_cache = []
            for pattern, weight in urgency_patterns:
                # Optimization: Extract literal keywords from simple regex strings like "\b(word1|word2)\b"
                # This allows us to use a fast substring check (`in text`) before executing the regex engine.
                keywords = []
                if re.fullmatch(r"\\b\([a-zA-Z0-9\s|]+\)\\b", pattern):
                    clean_pattern = (
                        pattern.replace("\\b", "").replace("(", "").replace(")", "")
                    )
                    keywords = [
                        k.strip() for k in clean_pattern.split("|") if k.strip()
                    ]

                self._regex_cache.append(
                    (re.compile(pattern), weight, pattern, keywords)
                )

            self._last_reload_count = current_reload_count

    def analyze(
        self, text: str, image_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyzes the issue text and optional image labels to determine priority.
        """
        text = text.lower()
        self._ensure_weights_cache()

        # Merge image labels into text for analysis if provided
        combined_text = text
        if image_labels:
            combined_text += " " + " ".join([l.lower() for l in image_labels])

        severity_score, severity_label, severity_reasons = self._calculate_severity(
            combined_text
        )
        urgency_score, urgency_reasons = self.calculate_urgency(
            combined_text, severity_score
        )
        categories = self._detect_categories(combined_text)

        # Apply Adaptive Category Weights from local cache
        max_multiplier = 1.0
        for cat in categories:
            mult = self._category_multipliers.get(cat, 1.0)
            if mult > max_multiplier:
                max_multiplier = mult

        if max_multiplier > 1.05:  # Threshold to report boost
            # Boost score
            old_score = severity_score
            severity_score = int(severity_score * max_multiplier)
            severity_score = min(100, severity_score)

            # Add reasoning
            if severity_score > old_score:
                severity_reasons.append(
                    f"Severity score boosted by x{max_multiplier:.2f} based on historical trends for this category."
                )

            # Re-evaluate label based on boosted score
            if severity_score >= 90:
                severity_label = "Critical"
            elif severity_score >= 70:
                severity_label = "High"
            elif severity_score >= 40:
                severity_label = "Medium"
            else:
                if severity_score < 40:
                    severity_label = "Low"

        # Explainability
        reasoning = severity_reasons + urgency_reasons
        if not reasoning:
            reasoning = ["Standard priority based on general keywords."]

        return {
            "severity": severity_label,
            "severity_score": severity_score,  # 0-100 normalized
            "urgency_score": urgency_score,  # 0-100
            "suggested_categories": categories,
            "reasoning": reasoning,
        }

    def _calculate_severity(self, text: str):
        score = 0
        reasons = []
        label = "Low"

        # Check for critical keywords (highest priority)
        # Optimization: Manual loop with early break after 3 matches reduces O(N) to O(1) for long keyword lists.
        found_critical = []
        for word in self._severity_keywords.get("critical", []):
            if word in text:
                found_critical.append(word)
                if len(found_critical) >= 3:
                    break

        if found_critical:
            score = 90
            label = "Critical"
            reasons.append(
                f"Flagged as Critical due to keywords: {', '.join(found_critical)}"
            )

        # Check for high keywords
        if score < 70:
            found_high = []
            for word in self._severity_keywords.get("high", []):
                if word in text:
                    found_high.append(word)
                    if len(found_high) >= 3:
                        break

            if found_high:
                score = max(score, 70)
                label = "High" if score == 70 else label
                reasons.append(
                    f"Flagged as High Severity due to keywords: {', '.join(found_high)}"
                )

        # Check for medium keywords
        if score < 40:
            found_medium = []
            for word in self._severity_keywords.get("medium", []):
                if word in text:
                    found_medium.append(word)
                    if len(found_medium) >= 3:
                        break

            if found_medium:
                score = max(score, 40)
                label = "Medium" if score == 40 else label
                reasons.append(
                    f"Flagged as Medium Severity due to keywords: {', '.join(found_medium)}"
                )

        # Default to low
        if score == 0:
            score = 10
            label = "Low"
            reasons.append("Classified as Low Severity (maintenance/cosmetic issue)")

        return score, label, reasons

    def calculate_urgency(self, text: str, severity_score: int):
        # Base urgency follows severity
        urgency = severity_score
        reasons = []

        # Apply regex modifiers using compiled patterns from cache
        for regex, weight, original_pattern, keywords in self._regex_cache:
            # Substring pre-filter: skip expensive regex search if no keywords match.
            if not keywords:
                if regex.search(text):
                    urgency += weight
                    reasons.append(
                        f"Urgency increased by context matching pattern: '{original_pattern}'"
                    )
            else:
                if any(k in text for k in keywords):
                    if regex.search(text):
                        urgency += weight
                        reasons.append(
                            f"Urgency increased by context matching pattern: '{original_pattern}'"
                        )

        # Cap at 100
        urgency = min(100, urgency)

        return urgency, reasons

    def _detect_categories(self, text: str) -> List[str]:
        # Optimization: Use cached category keywords
        scored_categories = []
        for category, keywords in self._category_keywords.items():
            count = 0
            for k in keywords:
                if k in text:
                    count += 1

            if count > 0:
                scored_categories.append((category, count))

        # Sort by count desc
        if len(scored_categories) > 1:
            scored_categories.sort(key=lambda x: x[1], reverse=True)

        return [c[0] for c in scored_categories[:3]]


# Singleton instance
priority_engine = PriorityEngine()
