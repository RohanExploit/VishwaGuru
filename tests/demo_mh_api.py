"""
Visual demonstration of the Maharashtra MLA lookup API response
"""
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient

os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token'
os.environ['GEMINI_API_KEY'] = ''

from main import app

client = TestClient(app, raise_server_exceptions=False)


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_json(data, indent=2):
    """Print formatted JSON"""
    print(json.dumps(data, indent=indent))


def demonstrate_api():
    """Demonstrate the Maharashtra MLA API with sample requests"""
    
    print("\n" + "█"*70)
    print("█" + " "*68 + "█")
    print("█" + "  Maharashtra MLA Lookup API - Visual Demonstration".center(68) + "█")
    print("█" + " "*68 + "█")
    print("█"*70)
    
    # Test Case 1: Pune
    print_section("Test Case 1: Pune Pincode (411001)")
    print("\nRequest: GET /api/mh/rep-contacts?pincode=411001\n")
    response = client.get("/api/mh/rep-contacts?pincode=411001")
    print(f"Status: {response.status_code} OK\n")
    print("Response:")
    print_json(response.json())
    
    # Test Case 2: Mumbai
    print_section("Test Case 2: Mumbai Pincode (400001)")
    print("\nRequest: GET /api/mh/rep-contacts?pincode=400001\n")
    response = client.get("/api/mh/rep-contacts?pincode=400001")
    print(f"Status: {response.status_code} OK\n")
    print("Response:")
    print_json(response.json())
    
    # Test Case 3: Nagpur
    print_section("Test Case 3: Nagpur Pincode (440001)")
    print("\nRequest: GET /api/mh/rep-contacts?pincode=440001\n")
    response = client.get("/api/mh/rep-contacts?pincode=440001")
    print(f"Status: {response.status_code} OK\n")
    print("Response:")
    print_json(response.json())
    
    # Test Case 4: Invalid Pincode
    print_section("Test Case 4: Invalid Pincode (999999)")
    print("\nRequest: GET /api/mh/rep-contacts?pincode=999999\n")
    response = client.get("/api/mh/rep-contacts?pincode=999999")
    print(f"Status: {response.status_code} Not Found\n")
    print("Response:")
    print_json(response.json())
    
    # Summary
    print_section("Summary")
    print("""
✓ Feature: Maharashtra MLA Lookup by Pincode
✓ Endpoint: GET /api/mh/rep-contacts?pincode=XXXXXX
✓ Sample Pincodes Available:
  - 411001, 411002 (Pune)
  - 400001, 400020 (Mumbai)
  - 440001 (Nagpur)

✓ Response includes:
  - Location details (pincode, district, constituency)
  - MLA information (name, party, contact details)
  - Grievance portal links (CPGRAMS, Maharashtra Aaple Sarkar)
  - Optional AI-generated description (when Gemini API is available)

✓ Error handling:
  - 400: Invalid pincode format
  - 404: Pincode not found
  - 422: Missing or invalid parameters
    """)
    
    print("="*70)
    print("\n")


if __name__ == "__main__":
    demonstrate_api()
