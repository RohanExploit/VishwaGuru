import json
import os
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class AdaptiveWeights:
    """
    Manages dynamic weights for the Civic Intelligence Engine.
    Loads and saves weights from data/modelWeights.json.
    """

    DEFAULT_WEIGHTS_FILE = "data/modelWeights.json"

    # Default values from PriorityEngine
    DEFAULT_SEVERITY_KEYWORDS = {
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

    DEFAULT_URGENCY_PATTERNS = [
        [r"\b(now|immediately|urgent|emergency|critical|danger|help)\b", 20],
        [r"\b(today|tonight|morning|evening|afternoon)\b", 10],
        [r"\b(yesterday|last night|week|month)\b", 5],
        [r"\b(blood|bleeding|injury|hurt|pain|dead)\b", 25],
        [r"\b(fire|smoke|flame|burn|gas|leak|explosion)\b", 30],
        [r"\b(blocked|stuck|trapped|jam)\b", 15],
        [r"\b(school|hospital|clinic)\b", 15],
        [r"\b(child|kid|baby|elderly|senior)\b", 10]
    ]

    DEFAULT_CATEGORIES = {
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
    }

    # Severity mapping for Grievance creation
    DEFAULT_SEVERITY_MAPPING = {
        'pothole': 'high',
        'garbage': 'medium',
        'streetlight': 'medium',
        'flood': 'critical',
        'infrastructure': 'high',
        'parking': 'low',
        'fire': 'critical',
        'animal': 'medium',
        'blocked': 'high',
        'tree': 'medium',
        'pest': 'low',
        'vandalism': 'medium'
    }

    DEFAULT_DUPLICATE_RADIUS = 50.0

    def __init__(self, weights_file: str = DEFAULT_WEIGHTS_FILE):
        self.weights_file = weights_file
        self.severity_keywords = self.DEFAULT_SEVERITY_KEYWORDS.copy()
        self.urgency_patterns = list(self.DEFAULT_URGENCY_PATTERNS)
        self.categories = self.DEFAULT_CATEGORIES.copy()
        self.severity_mapping = self.DEFAULT_SEVERITY_MAPPING.copy()
        self.duplicate_search_radius = self.DEFAULT_DUPLICATE_RADIUS

        self.load_weights()

    def load_weights(self):
        """Loads weights from JSON file if it exists."""
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    data = json.load(f)
                    self.severity_keywords = data.get("severity_keywords", self.severity_keywords)
                    self.urgency_patterns = data.get("urgency_patterns", self.urgency_patterns)
                    self.categories = data.get("categories", self.categories)
                    self.severity_mapping = data.get("severity_mapping", self.severity_mapping)
                    self.duplicate_search_radius = data.get("duplicate_search_radius", self.duplicate_search_radius)
                    logger.info(f"Loaded weights from {self.weights_file}")
            except Exception as e:
                logger.error(f"Failed to load weights from {self.weights_file}: {e}")
        else:
            logger.info("Weights file not found, using defaults.")
            self.save_weights() # Create the file with defaults

    def save_weights(self):
        """Saves current weights to JSON file."""
        data = {
            "severity_keywords": self.severity_keywords,
            "urgency_patterns": self.urgency_patterns,
            "categories": self.categories,
            "severity_mapping": self.severity_mapping,
            "duplicate_search_radius": self.duplicate_search_radius
        }

        # Ensure directory exists
        os.makedirs(os.path.dirname(self.weights_file), exist_ok=True)

        try:
            with open(self.weights_file, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved weights to {self.weights_file}")
        except Exception as e:
            logger.error(f"Failed to save weights to {self.weights_file}: {e}")

    def get_weights(self) -> Dict[str, Any]:
        """Returns all current weights."""
        return {
            "severity_keywords": self.severity_keywords,
            "urgency_patterns": self.urgency_patterns,
            "categories": self.categories,
            "severity_mapping": self.severity_mapping,
            "duplicate_search_radius": self.duplicate_search_radius
        }

    def update_category_weight(self, category: str, multiplier: float):
        """
        Updates the importance of a category (conceptual placeholder).
        In this simplified model, we might just ensure the category exists or add keywords.
        """
        pass

    def add_keyword_to_category(self, category: str, keyword: str):
        if category in self.categories:
            if keyword not in self.categories[category]:
                self.categories[category].append(keyword)
                self.save_weights()

    def update_severity_mapping(self, category: str, severity: str):
        self.severity_mapping[category.lower()] = severity.lower()
        self.save_weights()
