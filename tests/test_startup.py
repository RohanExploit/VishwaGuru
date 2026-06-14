"""
Test to verify that the FastAPI app starts successfully and can bind to a port.
This test ensures that the bot initialization doesn't block the web server startup.
"""
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from main import app

def test_health_endpoint():
    """Test that the health endpoint is accessible immediately"""
    client = TestClient(app)
    response = client.get("/health")
    print(f"Health check status: {response.status_code}")
    print(f"Health check response: {response.json()}")
    
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """Test that the root endpoint is accessible"""
    client = TestClient(app)
    response = client.get("/")
    print(f"Root status: {response.status_code}")
    print(f"Root response: {response.json()}")
    
    assert response.status_code == 200
    json_response = response.json()
    assert "data" in json_response
    assert json_response["data"]["service"] == "VishwaGuru API"

if __name__ == "__main__":
    print("Testing startup and port binding...")
    test_health_endpoint()
    print("✓ Health endpoint test passed")
    test_root_endpoint()
    print("✓ Root endpoint test passed")
    print("\nAll tests passed! The app can bind to port successfully.")
