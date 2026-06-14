import json
import os
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class AdaptiveWeights:
    """
    Singleton class to manage adaptive weights for the Priority Engine.
    Loads and saves weights to a JSON file.
    """
    _instance = None

    # Default path relative to the project root
    DATA_FILE = "data/modelWeights.json"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdaptiveWeights, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.weights = {}
        self._load_weights()
        self._initialized = True

    def _load_weights(self):
        """Loads weights from JSON file or initializes defaults."""
        if os.path.exists(self.DATA_FILE):
            try:
                with open(self.DATA_FILE, 'r') as f:
                    self.weights = json.load(f)
                logger.info(f"Loaded adaptive weights from {self.DATA_FILE}")
            except Exception as e:
                logger.error(f"Error loading weights from {self.DATA_FILE}: {e}")
                self._set_defaults()
        else:
            logger.info("Weights file not found. Using defaults.")
            self._set_defaults()
            # We don't save immediately, only when explicitly updated or requested.

    def _set_defaults(self):
        """Sets default weights based on initial PriorityEngine logic."""
        self.weights = {
            "severity_keywords": {
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
            },
            "urgency_patterns": [
                [r"\b(now|immediately|urgent|emergency|critical|danger|help)\b", 20],
                [r"\b(today|tonight|morning|evening|afternoon)\b", 10],
                [r"\b(yesterday|last night|week|month)\b", 5],
                [r"\b(blood|bleeding|injury|hurt|pain|dead)\b", 25],
                [r"\b(fire|smoke|flame|burn|gas|leak|explosion)\b", 30],
                [r"\b(blocked|stuck|trapped|jam)\b", 15],
                [r"\b(school|hospital|clinic)\b", 15],
                [r"\b(child|kid|baby|elderly|senior)\b", 10]
            ],
            "categories": {
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
            },
            "duplicate_search_radius": 50.0,
            "category_weights": {} # To boost specific categories regardless of keywords
        }

    def save_weights(self):
        """Saves current weights to JSON file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.DATA_FILE), exist_ok=True)

            with open(self.DATA_FILE, 'w') as f:
                json.dump(self.weights, f, indent=4)
            logger.info(f"Saved adaptive weights to {self.DATA_FILE}")
        except Exception as e:
            logger.error(f"Error saving weights to {self.DATA_FILE}: {e}")

    # Accessors
    @property
    def severity_keywords(self) -> Dict[str, List[str]]:
        return self.weights.get("severity_keywords", {})

    @property
    def urgency_patterns(self) -> List[Any]:
        return self.weights.get("urgency_patterns", [])

    @property
    def categories(self) -> Dict[str, List[str]]:
        return self.weights.get("categories", {})

    @property
    def duplicate_search_radius(self) -> float:
        return self.weights.get("duplicate_search_radius", 50.0)

    @property
    def category_weights(self) -> Dict[str, float]:
        return self.weights.get("category_weights", {})

    # Mutators
    def update_duplicate_search_radius(self, new_radius: float):
        """Updates the search radius for duplicate detection."""
        self.weights["duplicate_search_radius"] = new_radius
        self.save_weights()

    def add_severity_keyword(self, level: str, keyword: str):
        """Adds a keyword to a severity level."""
        if level in self.weights["severity_keywords"]:
            if keyword not in self.weights["severity_keywords"][level]:
                self.weights["severity_keywords"][level].append(keyword)
                self.save_weights()

    def update_category_weight(self, category: str, delta: float):
        """Increases or decreases the base weight for a category."""
        current = self.weights.get("category_weights", {}).get(category, 0.0)
        if "category_weights" not in self.weights:
            self.weights["category_weights"] = {}

        self.weights["category_weights"][category] = current + delta
        self.save_weights()

# Global instance
adaptive_weights = AdaptiveWeights()
