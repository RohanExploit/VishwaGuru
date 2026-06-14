#!/usr/bin/env python3
"""
VishwaGuru Backend API Validation Script
Tests all API endpoints to ensure they are working correctly.
"""

import os
import sys
import requests
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_health_endpoint(base_url="http://localhost:8000"):
    """Test the health endpoint"""
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ Health endpoint working")
            return True
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health endpoint error: {e}")
        return False

def test_root_endpoint(base_url="http://localhost:8000"):
    """Test the root endpoint"""
    try:
        response = requests.get(f"{base_url}/")
        if response.status_code == 200:
            data = response.json()
            print("✅ Root endpoint working")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_stats_endpoint(base_url="http://localhost:8000"):
    """Test the stats endpoint"""
    try:
        response = requests.get(f"{base_url}/api/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ Stats endpoint working")
            return True
        else:
            print(f"❌ Stats endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Stats endpoint error: {e}")
        return False

def test_recent_issues_endpoint(base_url="http://localhost:8000"):
    """Test the recent issues endpoint"""
    try:
        response = requests.get(f"{base_url}/api/issues/recent")
        if response.status_code == 200:
            data = response.json()
            print("✅ Recent issues endpoint working")
            return True
        else:
            print(f"❌ Recent issues endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Recent issues endpoint error: {e}")
        return False

def test_maharashtra_rep_endpoint(base_url="http://localhost:8000"):
    """Test the Maharashtra representative endpoint"""
    try:
        response = requests.get(f"{base_url}/api/mh/rep-contacts?pincode=400001")
        if response.status_code == 200:
            data = response.json()
            print("✅ Maharashtra rep endpoint working")
            return True
        else:
            print(f"❌ Maharashtra rep endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Maharashtra rep endpoint error: {e}")
        return False

def main():
    """Run all API validation tests"""
    print("🧪 VishwaGuru Backend API Validation")
    print("=" * 40)

    base_url = os.getenv("API_BASE_URL", "http://localhost:8000")

    tests = [
        test_health_endpoint,
        test_root_endpoint,
        test_stats_endpoint,
        test_recent_issues_endpoint,
        test_maharashtra_rep_endpoint,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test(base_url):
            passed += 1

    print(f"\n📊 Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All API endpoints are working correctly!")
        return 0
    else:
        print("⚠️  Some API endpoints need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())