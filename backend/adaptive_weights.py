import json
import os
import logging
import time
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

# Constants
# Get the repository root directory (assuming this file is in backend/adaptive_weights.py)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DEFAULT_WEIGHTS_PATH = os.path.join(DATA_DIR, "modelWeights.json")

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

class AdaptiveWeights:
    """
    Manages dynamic weights for the PriorityEngine.
    Loads from/saves to a JSON file.
    Automatically reloads if the file changes.
    """

    def __init__(self, data_path: str = DEFAULT_WEIGHTS_PATH):
        self.data_path = data_path
        self._severity_keywords = DEFAULT_SEVERITY_KEYWORDS.copy()
        self._urgency_patterns = DEFAULT_URGENCY_PATTERNS.copy()
        self._categories = DEFAULT_CATEGORIES.copy()
        self._duplicate_search_radius = 50.0

        self.last_modified = 0.0
        self.last_check_time = 0.0
        self.check_interval = 5.0 # Check every 5 seconds at most

        self.load_weights()

    def _check_reload(self):
        """Checks if file modified and reloads if needed."""
        now = time.time()
        if now - self.last_check_time < self.check_interval:
            return

        self.last_check_time = now
        if os.path.exists(self.data_path):
            try:
                mtime = os.path.getmtime(self.data_path)
                if mtime > self.last_modified:
                    logger.info(f"Weights file changed. Reloading from {self.data_path}")
                    self.load_weights()
            except Exception as e:
                logger.error(f"Error checking weights file modification: {e}")

    def load_weights(self):
        """Loads weights from the JSON file if it exists."""
        if os.path.exists(self.data_path):
            try:
                with open(self.data_path, 'r') as f:
                    data = json.load(f)
                    self._severity_keywords = data.get("severity_keywords", self._severity_keywords)
                    self._urgency_patterns = data.get("urgency_patterns", self._urgency_patterns)
                    self._categories = data.get("categories", self._categories)
                    self._duplicate_search_radius = data.get("duplicate_search_radius", self._duplicate_search_radius)

                self.last_modified = os.path.getmtime(self.data_path)
                logger.info(f"Loaded weights from {self.data_path}")
            except Exception as e:
                logger.error(f"Failed to load weights from {self.data_path}: {e}")
        else:
            logger.info(f"No existing weights file found at {self.data_path}. Using defaults.")
            self.save_weights()

    def save_weights(self):
        """Saves current weights to the JSON file."""
        data = {
            "severity_keywords": self._severity_keywords,
            "urgency_patterns": self._urgency_patterns,
            "categories": self._categories,
            "duplicate_search_radius": self._duplicate_search_radius
        }
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.data_path), exist_ok=True)

            with open(self.data_path, 'w') as f:
                json.dump(data, f, indent=4)

            # Update last_modified so we don't reload our own write immediately (or we do, which is fine)
            self.last_modified = os.path.getmtime(self.data_path)
            logger.info(f"Saved weights to {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to save weights to {self.data_path}: {e}")

    @property
    def severity_keywords(self) -> Dict[str, List[str]]:
        self._check_reload()
        return self._severity_keywords

    @property
    def urgency_patterns(self) -> List[List[Any]]:
        self._check_reload()
        return self._urgency_patterns

    @property
    def categories(self) -> Dict[str, List[str]]:
        self._check_reload()
        return self._categories

    @property
    def duplicate_search_radius(self) -> float:
        self._check_reload()
        return self._duplicate_search_radius

    @duplicate_search_radius.setter
    def duplicate_search_radius(self, value: float):
        self._duplicate_search_radius = value
        self.save_weights()

    def update_severity_keyword(self, severity_level: str, keyword: str, add: bool = True):
        self._check_reload() # Ensure we have latest before updating
        if severity_level not in self._severity_keywords:
            return

        keywords = self._severity_keywords[severity_level]
        if add:
            if keyword not in keywords:
                keywords.append(keyword)
        else:
            if keyword in keywords:
                keywords.remove(keyword)

        self.save_weights()

    def update_category_keyword(self, category: str, keyword: str, add: bool = True):
        self._check_reload()
        if category not in self._categories:
            if add:
                self._categories[category] = [keyword]
            else:
                return
        else:
            keywords = self._categories[category]
            if add:
                if keyword not in keywords:
                    keywords.append(keyword)
            else:
                if keyword in keywords:
                    keywords.remove(keyword)

        self.save_weights()

    def get_urgency_patterns_tuples(self) -> List[Tuple[str, int]]:
        """Returns urgency patterns as tuples (required by PriorityEngine)."""
        # Call property to trigger reload check
        patterns = self.urgency_patterns
        return [(p[0], p[1]) for p in patterns]

# Singleton instance
adaptive_weights = AdaptiveWeights()
