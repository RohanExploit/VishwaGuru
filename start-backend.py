import os
import sys

# Fix for googletrans compatibility with newer httpcore (Issue #290)
# This monkeypatch must happen before any imports of googletrans or httpx
try:
    import httpcore
    if not hasattr(httpcore, "SyncHTTPTransport"):
        httpcore.SyncHTTPTransport = object
except ImportError:
    pass

import uvicorn

# Ensure the backend directory is in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Get port from environment variable, default to 10000
    port = int(os.environ.get("PORT", 10000))

    print(f"Starting server on port {port}")
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, log_level="info")
