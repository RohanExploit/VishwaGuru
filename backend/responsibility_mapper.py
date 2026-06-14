import json
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def _load_responsibility_map():
    file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "responsibility_map.json")
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def get_responsible_authority():
    """
    Returns the responsibility map data.
    """
    return _load_responsibility_map()
