import requests
import json

base_url = "http://localhost:8000"

try:
    print(f"Checking health: {requests.get(f'{base_url}/health').json()}")
except Exception as e:
    print(f"Error checking health: {e}")
try:
    recent = requests.get(f"{base_url}/api/issues/recent")
    print(f"Recent issues status: {recent.status_code}")
    print(f"Recent issues count: {len(recent.json())}")
    if len(recent.json()) > 0:
        print(f"First issue: {json.dumps(recent.json()[0], indent=2)}")
except Exception as e:
    print(f"Error fetching: {e}")

try:
    stats = requests.get(f"{base_url}/api/stats")
    print(f"Stats: {json.dumps(stats.json(), indent=2)}")
except Exception as e:
    print(f"Error fetching stats: {e}")
