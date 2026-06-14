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
        # Keyword dictionaries for Severity Classification
        self.severity_keywords = {
            "critical": [
                "fire", "explosion", "blood", "death", "collapse", "gas leak",
                "electric shock", "spark", "electrocution", "drowning",
                "flood", "landslide", "earthquake", "cyclone", "hurricane",
                "attack", "assault", "rabid", "deadly", "fatal", "emergency",
                "blocked road", "ambulance", "hospital", "school", "child",
                "exposed wire", "transformer", "chemical", "toxic", "poison",
                "weapon", "gun", "bomb", "terror", "riot", "stampede",
                "structural failure", "pillar", "bridge", "flyover",
                "open manhole", "live wire", "gas smell", "open electrical box",
                "burning", "flame", "smoke", "crack", "fissure"
            ],
            "high": [
                "accident", "injury", "broken", "bleeding", "hazard", "risk",
                "dangerous", "unsafe", "threat", "pollution", "smoke",
                "sewage", "overflow", "contamination", "infection", "disease",
                "mosquito", "dengue", "malaria", "typhoid", "cholera",
                "rat", "snake", "stray dog", "bite", "attack", "cattle",
                "theft", "robbery", "burglary", "harassment", "abuse",
                "illegal", "crime", "violation", "bribe", "corruption",
                "traffic jam", "congestion", "gridlock", "delay",
                "no water", "power cut", "blackout", "load shedding",
                "pothole", "manhole", "open drain", "water logging",
                "dead", "animal", "fish", "stuck",
                "not working", "signal", "traffic light", "fallen tree",
                "water leakage", "leakage", "burst", "pipe burst", "damage",
                "leaning", "tilted", "unstable", "waterlogging"
            ],
            "medium": [
                "garbage", "trash", "waste", "litter", "rubbish", "dustbin",
                "smell", "odor", "stink", "foul", "dirty", "unclean",
                "messy", "ugly", "eyesore", "bad", "poor",
                "leak", "drip", "seepage", "moisture", "damp",
                "noise", "loud", "sound", "music", "party", "barking",
                "encroachment", "hawker", "vendor", "stall", "shop",
                "parking", "parked", "vehicle", "car", "bike", "scooter",
                "construction", "debris", "material", "sand", "cement",
                "graffiti", "poster", "banner", "hoarding", "advertisement",
                "slippery", "muddy", "path", "pavement", "sidewalk",
                "crowd", "gathering", "tap", "wasting", "running water",
                "speed breaker", "hump", "bump"
            ],
            "low": [
                "light", "lamp", "bulb", "flicker", "dim", "dark",
                "sign", "board", "paint", "color", "faded",
                "bench", "chair", "seat", "grass", "plant", "tree",
                "leaf", "branch", "garden", "park", "playground",
                "cosmetic", "look", "appearance", "aesthetic",
                "old", "rusty", "dirty", "leaning"
            ]
        }

        # Regex patterns for Urgency Scoring
        self.urgency_patterns = [
            (r"\b(now|immediately|urgent|emergency|critical|danger|help)\b", 20),
            (r"\b(today|tonight|morning|evening|afternoon)\b", 10),
            (r"\b(yesterday|last night|week|month)\b", 5),
            (r"\b(blood|bleeding|injury|hurt|pain|dead)\b", 25),
            (r"\b(fire|smoke|flame|burn|gas|leak|explosion)\b", 30),
            (r"\b(blocked|stuck|trapped|jam)\b", 15),
            (r"\b(school|hospital|clinic)\b", 15),  # Sensitive locations
            (r"\b(child|kid|baby|elderly|senior)\b", 10) # Vulnerable groups
        ]

        # Category mapping
        self.categories = {
            "Fire": ["fire", "smoke", "flame", "burn", "explosion", "burning"],
            "Pothole": ["pothole", "hole", "crater", "road damage", "broken road"],
            "Street Light": ["light", "lamp", "bulb", "dark", "street light", "flicker"],
            "Garbage": ["garbage", "trash", "waste", "litter", "rubbish", "dump", "dustbin"],
            "Water Leak": ["water", "leak", "pipe", "burst", "flood", "seepage", "drip", "leakage", "tap", "running"],
            "Stray Animal": ["dog", "cat", "cow", "cattle", "monkey", "bite", "stray", "animal", "rabid", "dead animal"],
            "Construction Safety": ["construction", "debris", "material", "cement", "sand", "building"],
            "Illegal Parking": ["parking", "parked", "blocking", "vehicle", "car", "bike"],
            "Vandalism": ["graffiti", "paint", "broken", "destroy", "damage", "poster"],
            "Infrastructure": ["bridge", "flyover", "pillar", "crack", "collapse", "structure", "manhole", "drain", "wire", "cable", "pole", "electrical box", "electric box", "transformer", "sidewalk", "pavement", "tile", "speed breaker", "road"],
            "Traffic Sign": ["sign", "signal", "light", "traffic", "board", "direction", "stop sign"],
            "Abandoned Vehicle": ["abandoned", "vehicle", "car", "parked", "rust", "rusting", "scooter", "bike"],
            "Public Facilities": ["toilet", "washroom", "bench", "seat", "park", "garden", "playground", "slide", "swing"],
            "Tree Hazard": ["tree", "branch", "fallen", "root", "leaf"],
            "Accessibility": ["ramp", "wheelchair", "step", "stair", "access", "disability"],
            "Noise Pollution": ["noise", "loud", "sound", "music", "speaker"],
            "Air Pollution": ["smoke", "dust", "fume", "smell", "pollution", "air"],
            "Water Pollution": ["river", "lake", "pond", "chemical", "oil", "poison", "fish"],
            "Health Hazard": ["mosquito", "dengue", "malaria", "rat", "disease", "health"],
            "Crowd": ["crowd", "gathering", "mob", "people", "protest"],
            "Gas Leak": ["gas", "leak", "smell", "cylinder", "pipeline"],
            "Environment": ["tree", "cutting", "deforestation", "forest", "nature"],
            "Flooding": ["flood", "waterlogging", "water logged", "rain", "drainage"]
        }

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

    def _calculate_urgency(self, text: str, severity_score: int):
        # Base urgency follows severity
        urgency = severity_score
        reasons = []

        urgency_patterns = adaptive_weights.get_urgency_patterns()

        # Apply regex modifiers
        for pattern, weight in urgency_patterns:
            if re.search(pattern, text):
                urgency += weight
                reasons.append(f"Urgency increased by context matching pattern: '{pattern}'")

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
