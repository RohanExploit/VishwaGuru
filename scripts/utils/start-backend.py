import os
import sys
import uvicorn

# Ensure the backend directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Get port from environment variable, default to 10000
    port = int(os.environ.get("PORT", 10000))

    print(f"Starting server on port {port}")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, log_level="info")
