import requests
import time
import os
import hashlib

BASE_URL = "http://localhost:8000/api"

def test_blockchain():
    # 1. Create first issue
    print("Creating first issue...")
    resp1 = requests.post(f"{BASE_URL}/issues", data={
        "description": "First issue for blockchain test",
        "category": "Road",
        "latitude": 10.0,
        "longitude": 10.0
    })
    print(f"Resp 1: {resp1.json()}")
    id1 = resp1.json()["id"]

    # 2. Create second issue (nearby, so it should be a duplicate)
    print("\nCreating second issue (duplicate)...")
    resp2 = requests.post(f"{BASE_URL}/issues", data={
        "description": "Second issue - duplicate of first",
        "category": "Road",
        "latitude": 10.0001,
        "longitude": 10.0001
    })
    print(f"Resp 2: {resp2.json()}")

    # 3. Create third issue (unique)
    print("\nCreating third issue (unique)...")
    resp3 = requests.post(f"{BASE_URL}/issues", data={
        "description": "Third issue - unique location",
        "category": "Water",
        "latitude": 20.0,
        "longitude": 20.0
    })
    print(f"Resp 3: {resp3.json()}")
    id3 = resp3.json()["id"]

    # 4. Verify blockchain integrity
    print("\nVerifying blockchain integrity...")

    for i in range(id1, id3 + 1):
        v_resp = requests.get(f"{BASE_URL}/issues/{i}/blockchain-verify")
        data = v_resp.json()
        print(f"Issue {i} Verification: {data.get('is_valid')} - {data.get('message')}")
        if not data.get('is_valid'):
            print(f"FAIL: Issue {i} is invalid!")
            print(f"Stored Hash: {data.get('current_hash')}")
            print(f"Computed Hash: {data.get('computed_hash')}")

if __name__ == "__main__":
    test_blockchain()
