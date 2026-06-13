import json
import os
import logging
from typing import Dict, List, Any, Tuple

logger = logging.getLogger(__name__)

class AdaptiveWeights:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdaptiveWeights, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # Determine the data directory relative to this file
        self.data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "../data")
        self.weights_file = os.path.join(self.data_dir, "modelWeights.json")
        self.ensure_data_dir()
        self.last_mtime = None

        # Default configuration (mirrors PriorityEngine defaults)
        self._severity_keywords = {
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

        self._urgency_patterns = [
            (r"\b(now|immediately|urgent|emergency|critical|danger|help)\b", 20),
            (r"\b(today|tonight|morning|evening|afternoon)\b", 10),
            (r"\b(yesterday|last night|week|month)\b", 5),
            (r"\b(blood|bleeding|injury|hurt|pain|dead)\b", 25),
            (r"\b(fire|smoke|flame|burn|gas|leak|explosion)\b", 30),
            (r"\b(blocked|stuck|trapped|jam)\b", 15),
            (r"\b(school|hospital|clinic)\b", 15),
            (r"\b(child|kid|baby|elderly|senior)\b", 10)
        ]

        self._categories = {
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

        self._duplicate_search_radius = 50.0 # meters
        self.last_updated = None

        self.load_weights()
        self._initialized = True

    def ensure_data_dir(self):
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _check_reload(self):
        """Check if weights file has changed and reload if necessary."""
        if not os.path.exists(self.weights_file):
            return

        try:
            current_mtime = os.path.getmtime(self.weights_file)
            if self.last_mtime is None or current_mtime > self.last_mtime:
                self.load_weights()
                self.last_mtime = current_mtime
                # logger.debug(f"Reloaded weights from {self.weights_file}")
        except OSError:
            pass

    @property
    def severity_keywords(self):
        self._check_reload()
        return self._severity_keywords

    @property
    def urgency_patterns(self):
        self._check_reload()
        return self._urgency_patterns

    @property
    def categories(self):
        self._check_reload()
        return self._categories

    @property
    def duplicate_search_radius(self):
        self._check_reload()
        return self._duplicate_search_radius

    def load_weights(self):
        if os.path.exists(self.weights_file):
            try:
                with open(self.weights_file, 'r') as f:
                    data = json.load(f)
                    self._severity_keywords = data.get("severity_keywords", self._severity_keywords)
                    # Convert list of lists back to list of tuples for regex
                    urgency_data = data.get("urgency_patterns", [])
                    if urgency_data:
                        self._urgency_patterns = [tuple(item) for item in urgency_data]

                    self._categories = data.get("categories", self._categories)
                    self._duplicate_search_radius = data.get("duplicate_search_radius", self._duplicate_search_radius)
                    self.last_updated = data.get("last_updated")
                logger.info(f"Loaded weights from {self.weights_file}")
            except Exception as e:
                logger.error(f"Error loading weights: {e}")

    def save_weights(self):
        data = {
            "severity_keywords": self._severity_keywords,
            "urgency_patterns": self._urgency_patterns, # JSON handles tuples as lists
            "categories": self._categories,
            "duplicate_search_radius": self._duplicate_search_radius,
            "last_updated": self.last_updated
        }
        try:
            with open(self.weights_file, 'w') as f:
                json.dump(data, f, indent=4)
            logger.info(f"Saved weights to {self.weights_file}")

            # Update mtime so we don't reload our own write unnecessarily (or do, it's fine)
            try:
                self.last_mtime = os.path.getmtime(self.weights_file)
            except OSError:
                pass

        except Exception as e:
            logger.error(f"Error saving weights: {e}")

    def update_duplicate_radius(self, new_radius: float):
        self._duplicate_search_radius = new_radius
        self.save_weights()
