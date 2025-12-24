"""
Unit tests for Maharashtra Locator Service

Tests the pincode and MLA lookup functions.
"""
import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from maharashtra_locator import (
    find_constituency_by_pincode,
    find_mla_by_constituency,
    load_maharashtra_pincode_data,
    load_maharashtra_mla_data
)


class TestMaharashtraLocator:
    """Test cases for Maharashtra locator functions"""
    
    def test_load_pincode_data(self):
        """Test loading pincode data"""
        data = load_maharashtra_pincode_data()
        assert isinstance(data, dict)
        assert len(data) > 0
        
    def test_load_mla_data(self):
        """Test loading MLA data"""
        data = load_maharashtra_mla_data()
        assert isinstance(data, dict)
        assert len(data) > 0
    
    def test_find_constituency_valid_pincode(self):
        """Test finding constituency with valid pincode"""
        result = find_constituency_by_pincode("411001")
        assert result is not None
        assert result["district"] == "Pune"
        assert result["state"] == "Maharashtra"
        assert result["assembly_constituency"] == "Kasba Peth"
    
    def test_find_constituency_invalid_pincode(self):
        """Test finding constituency with invalid pincode"""
        # Test with non-existent pincode
        result = find_constituency_by_pincode("999999")
        assert result is None
        
        # Test with invalid format
        result = find_constituency_by_pincode("12345")
        assert result is None
        
        # Test with non-numeric
        result = find_constituency_by_pincode("abcdef")
        assert result is None
        
        # Test with empty string
        result = find_constituency_by_pincode("")
        assert result is None
    
    def test_find_constituency_mumbai(self):
        """Test finding constituency for Mumbai pincode"""
        result = find_constituency_by_pincode("400001")
        assert result is not None
        assert result["district"] == "Mumbai City"
        assert result["assembly_constituency"] == "Colaba"
    
    def test_find_mla_valid_constituency(self):
        """Test finding MLA with valid constituency"""
        result = find_mla_by_constituency("Kasba Peth")
        assert result is not None
        # Validating with real data (Ravindra Dhangekar is the current MLA based on 2024 Assembly Election results)
        assert result["mla_name"] == "Ravindra Dhangekar"
        assert "Indian National Congress" in result["party"]
        assert "phone" in result
        assert "email" in result
    
    def test_find_mla_invalid_constituency(self):
        """Test finding MLA with invalid constituency"""
        result = find_mla_by_constituency("Non Existent Constituency")
        assert result is None
        
        result = find_mla_by_constituency("")
        assert result is None
        
        result = find_mla_by_constituency(None)
        assert result is None
    
    def test_find_mla_colaba(self):
        """Test finding MLA for Colaba constituency"""
        result = find_mla_by_constituency("Colaba")
        assert result is not None
        # Validating with real data (Rahul Narwekar is the current MLA based on 2024 Assembly Election results)
        assert result["mla_name"] == "Rahul Narwekar"
    
    def test_full_lookup_flow(self):
        """Test complete lookup flow from pincode to MLA"""
        # Test Pune pincode
        constituency = find_constituency_by_pincode("411001")
        assert constituency is not None
        
        mla = find_mla_by_constituency(constituency["assembly_constituency"])
        assert mla is not None
        assert mla["mla_name"] == "Ravindra Dhangekar"
        
        # Test Mumbai pincode
        constituency = find_constituency_by_pincode("400001")
        assert constituency is not None
        
        mla = find_mla_by_constituency(constituency["assembly_constituency"])
        assert mla is not None
        assert mla["mla_name"] == "Rahul Narwekar"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
