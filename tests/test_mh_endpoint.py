"""
Test script to verify the Maharashtra representative endpoint works correctly
"""
import sys
import os
from fastapi.testclient import TestClient

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Import the app without starting the bot
os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
os.environ['GEMINI_API_KEY'] = ''  # Test without Gemini

from main import app

client = TestClient(app, raise_server_exceptions=False)


def test_maharashtra_endpoint():
    """Test the Maharashtra representative endpoint"""
    print("Testing Maharashtra representative endpoint...")
    
    # Test valid pincode - Pune
    print("\n1. Testing valid pincode (411001 - Pune)...")
    response = client.get("/api/mh/rep-contacts?pincode=411001")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Success!")
        print(f"   District: {data.get('district')}")
        print(f"   Constituency: {data.get('assembly_constituency')}")
        print(f"   MLA: {data['mla'].get('name')}")
        print(f"   Party: {data['mla'].get('party')}")
        assert data['pincode'] == '411001'
        assert data['district'] == 'Pune'
        assert data['mla']['name'] == 'Ravindra Dhangekar'
    else:
        print(f"   ✗ Failed: {response.json()}")
        return False
    
    # Test valid pincode - Mumbai
    print("\n2. Testing valid pincode (400001 - Mumbai)...")
    response = client.get("/api/mh/rep-contacts?pincode=400001")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✓ Success!")
        print(f"   District: {data.get('district')}")
        print(f"   Constituency: {data.get('assembly_constituency')}")
        print(f"   MLA: {data['mla'].get('name')}")
        assert data['pincode'] == '400001'
        assert data['district'] == 'Mumbai City'
        assert data['mla']['name'] == 'Rahul Narwekar'
    else:
        print(f"   ✗ Failed: {response.json()}")
        return False
    
    # Test invalid pincode
    print("\n3. Testing invalid pincode (999999)...")
    response = client.get("/api/mh/rep-contacts?pincode=999999")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 404:
        print(f"   ✓ Correctly returns 404 for unknown pincode")
        print(f"   Error: {response.json().get('detail')}")
    else:
        print(f"   ✗ Expected 404, got {response.status_code}")
        return False
    
    # Test invalid format
    print("\n4. Testing invalid format (12345)...")
    response = client.get("/api/mh/rep-contacts?pincode=12345")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 422:
        print(f"   ✓ Correctly returns 422 for invalid format")
    else:
        print(f"   ✗ Expected 422, got {response.status_code}")
        return False
    
    # Test missing pincode
    print("\n5. Testing missing pincode parameter...")
    response = client.get("/api/mh/rep-contacts")
    print(f"   Status Code: {response.status_code}")
    
    if response.status_code == 422:
        print(f"   ✓ Correctly returns 422 for missing parameter")
    else:
        print(f"   ✗ Expected 422, got {response.status_code}")
        return False
    
    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)


if __name__ == "__main__":
    try:
        success = test_maharashtra_endpoint()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
