import json
import os
import logging
from typing import Dict, List, Any, Tuple
import datetime

logger = logging.getLogger(__name__)

class AdaptiveWeights:
    """
    Manages dynamic weights for severity scoring, urgency detection, and duplicate detection.
    Persists state to data/modelWeights.json.
    """

    DEFAULT_WEIGHTS = {
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
        "duplicate_search_radius": 50.0
    }

    def __init__(self, data_dir: str = "data"):
        # Resolve absolute path relative to this file to handle Render environment correctly
        # In Render, the app runs from repo root, but data might be mounted or just local
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # repo root
        if data_dir == "data":
             # If default 'data' is used, assume it's at repo root
             self.data_dir = os.path.join(base_dir, "data")
        else:
             self.data_dir = data_dir

        self.weights_file = os.path.join(self.data_dir, "modelWeights.json")
        self.last_mtime = 0
        self.weights = self._load_weights()

    def _load_weights(self) -> Dict[str, Any]:
        """Load weights from file or initialize with defaults."""
        # Always check mtime if file exists, regardless of result
        if os.path.exists(self.weights_file):
             self.last_mtime = os.path.getmtime(self.weights_file)

        # Check if data directory exists, create if not
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir, exist_ok=True)
            except OSError as e:
                # Log but continue with defaults, as read-only systems shouldn't crash
                logger.warning(f"Failed to create data directory {self.data_dir} (read-only FS?): {e}")
                return self.DEFAULT_WEIGHTS.copy()

        # Try loading file
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load weights from {self.weights_file}: {e}")
                # Don't overwrite if corrupted, just fallback to defaults for now
                return self.DEFAULT_WEIGHTS.copy()
        else:
            # Create file with defaults
            try:
                self._save_weights(self.DEFAULT_WEIGHTS)
            except Exception as e:
                logger.warning(f"Could not save default weights (read-only FS?): {e}")
            return self.DEFAULT_WEIGHTS.copy()

    def _save_weights(self, weights: Dict[str, Any]):
        """Save weights to file."""
        if not os.path.exists(self.data_dir):
            try:
                os.makedirs(self.data_dir, exist_ok=True)
            except OSError as e:
                logger.error(f"Failed to create data directory for saving weights: {e}")
                return

        try:
            with open(self.weights_file, 'w') as f:
                json.dump(weights, f, indent=4)
        except IOError as e:
            logger.error(f"Failed to save weights to {self.weights_file}: {e}")

    def get_weights(self) -> Dict[str, Any]:
        """Return current weights, reloading if file changed."""
        if os.path.exists(self.weights_file):
            try:
                mtime = os.path.getmtime(self.weights_file)
                if mtime > self.last_mtime:
                    logger.info("Weights file changed, reloading...")
                    self.weights = self._load_weights()
            except OSError:
                pass # Ignore file access errors, use cached weights
        return self.weights

    def update_weights(self, new_weights: Dict[str, Any]):
        """Update weights and save to file, archiving the previous version."""
        # Backup current weights
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        history_dir = os.path.join(self.data_dir, "weight_history")

        try:
            if not os.path.exists(history_dir):
                os.makedirs(history_dir, exist_ok=True)

            backup_file = os.path.join(history_dir, f"modelWeights_{timestamp}.json")
            try:
                with open(backup_file, 'w') as f:
                    json.dump(self.weights, f, indent=4)
            except IOError as e:
                logger.warning(f"Failed to backup weights to {backup_file}: {e}")
        except OSError:
            logger.warning("Failed to create backup directory, skipping backup.")

        # Update and save
        self.weights = new_weights
        self._save_weights(self.weights)
        logger.info(f"Weights updated and saved to {self.weights_file}")

    def get_duplicate_search_radius(self) -> float:
        return self.weights.get("duplicate_search_radius", 50.0)

# Singleton instance
adaptive_weights = AdaptiveWeights()
