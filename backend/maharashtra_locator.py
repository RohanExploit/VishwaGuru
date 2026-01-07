"""
Maharashtra Location Services

Lookup constituency and MLA information by pincode.
Uses JSON data files with fallback to pincode ranges.
"""
import json
import os
from functools import lru_cache
from typing import Optional, Dict, Any

# Pincode range to district mapping (fallback lookup)
DISTRICT_RANGES = [
    (400001, 400104, "Mumbai City"),
    (411001, 411062, "Pune"),
    (440001, 441204, "Nagpur"),
    (400601, 421605, "Thane"),
    (422001, 422403, "Nashik"),
    (431001, 431210, "Aurangabad"),
    (413001, 413409, "Solapur"),
    (416001, 416220, "Kolhapur"),
    (444601, 444912, "Amravati"),
    (425001, 425504, "Jalgaon"),
    (414001, 414505, "Ahmednagar"),
    (416416, 416436, "Sangli"),
    (413512, 413531, "Latur"),
    (415001, 415539, "Satara"),
    (442401, 442908, "Chandrapur"),
    (441904, 441914, "Bhandara"),
    (442001, 442506, "Wardha"),
    (445001, 445304, "Yavatmal"),
    (431601, 431805, "Nanded"),
    (413501, 413613, "Osmanabad"),
    (431122, 431540, "Beed"),
    (444001, 444808, "Akola"),
    (424001, 424319, "Dhule"),
    (431203, 431513, "Jalna"),
    (431401, 431540, "Parbhani"),
    (425412, 425524, "Nandurbar"),
    (431513, 431701, "Hingoli"),
    (415612, 415804, "Ratnagiri"),
    (416601, 416810, "Sindhudurg"),
    (401501, 401610, "Palghar"),
    (402201, 402308, "Raigad"),
    (441601, 441911, "Gondia"),
    (442605, 442709, "Gadchiroli"),
    (444105, 444512, "Washim"),
    (443001, 443403, "Buldhana")
]

@lru_cache(maxsize=1)
def load_maharashtra_pincode_data() -> Dict[str, Dict[str, Any]]:
    """Load pincode-to-constituency map from JSON. Cached once."""
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_pincode_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
        # Convert to dict for O(1) lookup
        return {item["pincode"]: item for item in data_list}


@lru_cache(maxsize=1)
def load_maharashtra_mla_data() -> Dict[str, Dict[str, Any]]:
    """Load MLA information from JSON. Cached once."""
    file_path = os.path.join(
        os.path.dirname(__file__),
        "data",
        "mh_mla_sample.json"
    )
    
    with open(file_path, "r", encoding="utf-8") as f:
        data_list = json.load(f)
        # Convert to dict for O(1) lookup
        return {item["assembly_constituency"]: item for item in data_list}


def get_district_by_pincode_range(pincode: int) -> Optional[str]:
    """Find district using pincode ranges. Fallback O(N) lookup."""
    for start, end, district in DISTRICT_RANGES:
        if start <= pincode <= end:
            return district
    return None


def find_constituency_by_pincode(pincode: str) -> Optional[Dict[str, Any]]:
    """Find constituency by pincode. Falls back to range lookup."""
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return None
    
    # Try exact lookup first
    pincode_map = load_maharashtra_pincode_data()
    entry = pincode_map.get(pincode)
    
    if entry:
        return {
            "district": entry.get("district"),
            "state": entry.get("state"),
            "assembly_constituency": entry.get("assembly_constituency")
        }
    
    # Fallback: pincode range lookup
    try:
        pincode_int = int(pincode)
        district = get_district_by_pincode_range(pincode_int)
        if district:
            return {
                "district": district,
                "state": "Maharashtra",
                "assembly_constituency": None
            }
    except ValueError:
        pass

    return None


def find_mla_by_constituency(constituency_name: str) -> Optional[Dict[str, Any]]:
    """Find MLA by assembly constituency name."""
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
