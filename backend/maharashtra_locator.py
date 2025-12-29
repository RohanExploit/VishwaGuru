"""
Maharashtra Locator Service

Provides functions to lookup constituency and MLA information
based on pincode for Maharashtra state.
"""
import json
import os
from functools import lru_cache
from typing import Optional, Dict, Any
import bisect

# District Pincode Ranges (Fallback data)
# Format: (start, end, district)
# Sorted by start pincode for binary search
DISTRICT_RANGES = [
    (400001, 400104, "Mumbai City"),
    (400601, 421605, "Thane"),
    (401501, 401610, "Palghar"),
    (402201, 402308, "Raigad"),
    (411001, 411062, "Pune"),
    (413001, 413409, "Solapur"),
    (413501, 413613, "Osmanabad"),
    (413512, 413531, "Latur"),
    (414001, 414505, "Ahmednagar"),
    (415001, 415539, "Satara"),
    (415612, 415804, "Ratnagiri"),
    (416001, 416220, "Kolhapur"),
    (416416, 416436, "Sangli"),
    (416601, 416810, "Sindhudurg"),
    (422001, 422403, "Nashik"),
    (424001, 424319, "Dhule"),
    (425001, 425504, "Jalgaon"),
    (425412, 425524, "Nandurbar"),
    (431001, 431210, "Aurangabad"),
    (431122, 431540, "Beed"),
    (431203, 431513, "Jalna"),
    (431401, 431540, "Parbhani"),
    (431513, 431701, "Hingoli"),
    (431601, 431805, "Nanded"),
    (440001, 441204, "Nagpur"),
    (441601, 441911, "Gondia"),
    (441904, 441914, "Bhandara"),
    (442001, 442506, "Wardha"),
    (442401, 442908, "Chandrapur"),
    (442605, 442709, "Gadchiroli"),
    (443001, 443403, "Buldhana"),
    (444001, 444808, "Akola"),
    (444105, 444512, "Washim"),
    (444601, 444912, "Amravati"),
    (445001, 445304, "Yavatmal")
]

# Pre-calculate start points for binary search
RANGE_STARTS = [r[0] for r in DISTRICT_RANGES]

@lru_cache(maxsize=1)
def load_maharashtra_pincode_data() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache Maharashtra pincode to constituency mapping data.
    
    Returns:
        dict: Dictionary mapping pincode to data
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_pincode_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
        # Convert list to dictionary for O(1) lookup
        return {item["pincode"]: item for item in data_list}


@lru_cache(maxsize=1)
def load_maharashtra_mla_data() -> Dict[str, Dict[str, Any]]:
    """
    Load and cache Maharashtra MLA information data.
    
    Returns:
        dict: Dictionary mapping constituency to MLA data
    """
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_mla_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
        # Convert list to dictionary for O(1) lookup
        return {item["assembly_constituency"]: item for item in data_list}


def get_district_by_pincode_range(pincode: int) -> Optional[str]:
    """
    Find district by checking pincode ranges using binary search.
    This is an O(log N) fallback where N is number of ranges (~35).
    """
    idx = bisect.bisect_right(RANGE_STARTS, pincode) - 1

    if idx >= 0:
        start, end, district = DISTRICT_RANGES[idx]
        if start <= pincode <= end:
            return district

    return None


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
    
    # 1. Exact Lookup
    pincode_map = load_maharashtra_pincode_data()
    entry = pincode_map.get(pincode)
    
    if entry:
        return {
            "district": entry.get("district"),
            "state": entry.get("state"),
            "assembly_constituency": entry.get("assembly_constituency")
        }
    
    # 2. Range Fallback
    try:
        pincode_int = int(pincode)
        district = get_district_by_pincode_range(pincode_int)
        if district:
            return {
                "district": district,
                "state": "Maharashtra",
                "assembly_constituency": None # Unknown constituency, but we know the district
            }
    except ValueError:
        pass

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
            "email": entry.get("email"),
            "twitter": entry.get("twitter")
        }
    
    return None
