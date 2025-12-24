"""
Maharashtra Locator Service

Provides functions to lookup constituency and MLA information
based on pincode for Maharashtra state.
"""
import json
import os
from functools import lru_cache
from typing import Optional, Dict, Any


@lru_cache(maxsize=1)
def load_maharashtra_pincode_data() -> list:
    """
    Load and cache Maharashtra pincode to constituency mapping data.
    
    Returns:
        list: List of pincode mapping dictionaries
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_pincode_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_maharashtra_mla_data() -> list:
    """
    Load and cache Maharashtra MLA information data.
    
    Returns:
        list: List of MLA information dictionaries
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_mla_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _load_maharashtra_pincode_map() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache Maharashtra pincode to constituency mapping as a dict for O(1) lookup.
    """
    pincode_data = load_maharashtra_pincode_data()
    return {entry["pincode"]: entry for entry in pincode_data if "pincode" in entry}


@lru_cache(maxsize=1)
def _load_maharashtra_mla_map() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache Maharashtra MLA information as a dict for O(1) lookup.
    """
    mla_data = load_maharashtra_mla_data()
    return {entry["assembly_constituency"]: entry for entry in mla_data if "assembly_constituency" in entry}


def find_constituency_by_pincode(pincode: str) -> Optional[Dict[str, Any]]:
    """
    Find constituency information by pincode.
    
    Args:
        pincode: 6-digit pincode string
        
    Returns:
        Dictionary with district, state, and assembly_constituency or None if not found
    """
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return None
    
    # Use O(1) map lookup instead of O(n) list iteration
    pincode_map = _load_maharashtra_pincode_map()
    entry = pincode_map.get(pincode)
    
    if entry:
        return {
            "district": entry.get("district"),
            "state": entry.get("state"),
            "assembly_constituency": entry.get("assembly_constituency")
        }
    
    return None


def find_mla_by_constituency(constituency_name: str) -> Optional[Dict[str, Any]]:
    """
    Find MLA information by assembly constituency name.
    
    Args:
        constituency_name: Name of the assembly constituency
        
    Returns:
        Dictionary with mla_name, party, phone, email or None if not found
    """
    if not constituency_name:
        return None
    
    # Use O(1) map lookup instead of O(n) list iteration
    mla_map = _load_maharashtra_mla_map()
    entry = mla_map.get(constituency_name)
    
    if entry:
        return {
            "mla_name": entry.get("mla_name"),
            "party": entry.get("party"),
            "phone": entry.get("phone"),
            "email": entry.get("email"),
            "twitter": entry.get("twitter")
        }
    
    return None
