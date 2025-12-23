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
def load_maharashtra_pincode_data() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache Maharashtra pincode to constituency mapping data.
    
    Returns:
        dict: Dictionary of pincode mapping keyed by pincode
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_pincode_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
        # Convert list to dict for O(1) lookup
        return {item.get("pincode"): item for item in data_list if item.get("pincode")}


@lru_cache(maxsize=1)
def load_maharashtra_mla_data() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache Maharashtra MLA information data.
    
    Returns:
        dict: Dictionary of MLA information keyed by assembly_constituency
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_mla_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
        # Convert list to dict for O(1) lookup
        return {item.get("assembly_constituency"): item for item in data_list if item.get("assembly_constituency")}


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
    
    pincode_map = load_maharashtra_pincode_data()
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
    
    mla_map = load_maharashtra_mla_data()
    entry = mla_map.get(constituency_name)
    
    if entry:
        return {
            "mla_name": entry.get("mla_name"),
            "party": entry.get("party"),
            "phone": entry.get("phone"),
            "email": entry.get("email")
        }
    
    return None
