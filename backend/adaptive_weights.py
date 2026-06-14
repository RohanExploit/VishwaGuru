import json
import os
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'modelWeights.json')

class AdaptiveWeights:
    _instance = None
    _weights = None
    _last_loaded = 0

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AdaptiveWeights, cls).__new__(cls)
            cls._instance._load_weights()
        return cls._instance

    def _load_weights(self):
        try:
            if not os.path.exists(DATA_FILE):
                logger.error(f"Weights file not found at {DATA_FILE}")
                # Initialize with empty dict to prevent AttributeError, though file should exist
                if self._weights is None:
                    self._weights = {}
                return

            mtime = os.path.getmtime(DATA_FILE)
            if self._weights is None or mtime > self._last_loaded:
                with open(DATA_FILE, 'r') as f:
                    self._weights = json.load(f)
                self._last_loaded = mtime
                logger.info("Adaptive weights loaded/reloaded.")
        except Exception as e:
            logger.error(f"Error loading adaptive weights: {e}")
            if self._weights is None:
                self._weights = {}

    def _check_reload(self):
        # Optimization: Checking mtime is fast (stat call).
        self._load_weights()

    def _save_weights(self):
        try:
            with open(DATA_FILE, 'w') as f:
                json.dump(self._weights, f, indent=2)
            # Update last loaded to avoid immediate reload
            self._last_loaded = os.path.getmtime(DATA_FILE)
        except Exception as e:
            logger.error(f"Error saving adaptive weights: {e}")

    def get_severity_keywords(self) -> Dict[str, List[str]]:
        self._check_reload()
        return self._weights.get('severity_keywords', {})

    def get_urgency_patterns(self) -> List[List[Any]]:
        self._check_reload()
        return self._weights.get('urgency_patterns', [])

    def get_category_keywords(self) -> Dict[str, List[str]]:
        self._check_reload()
        return self._weights.get('category_keywords', {})

    def get_category_multipliers(self) -> Dict[str, float]:
        self._check_reload()
        return self._weights.get('category_multipliers', {})

    def get_duplicate_search_radius(self) -> float:
        self._check_reload()
        return self._weights.get('duplicate_search_radius', 50.0)

    def update_category_weight(self, category: str, factor: float):
        """
        Updates the multiplier for a category.
        Factor should be slightly > 1.0 to increase severity, or < 1.0 to decrease.
        """
        self._check_reload() # Ensure we have latest
        multipliers = self._weights.get('category_multipliers', {})
        current = multipliers.get(category, 1.0)

        # Apply factor
        new_weight = current * factor

        # Clamp to reasonable limits (e.g., 0.5 to 3.0)
        new_weight = max(0.5, min(3.0, new_weight))

        multipliers[category] = new_weight
        self._weights['category_multipliers'] = multipliers

        self._weights['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self._save_weights()
        logger.info(f"Updated weight for {category} to {new_weight:.2f}")

    def update_duplicate_radius(self, factor: float):
        self._check_reload()
        current = self._weights.get('duplicate_search_radius', 50.0)
        new_radius = current * factor
        # Clamp (10m to 200m)
        new_radius = max(10.0, min(200.0, new_radius))

        self._weights['duplicate_search_radius'] = new_radius
        self._weights['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        self._save_weights()
        logger.info(f"Updated duplicate search radius to {new_radius:.1f}m")

adaptive_weights = AdaptiveWeights()
