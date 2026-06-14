"""
Entry point for running the backend as a module.
This allows running: 
  - From root: python -m backend
  - From backend: python -m __main__

This will start the FastAPI application with uvicorn,
which includes the Telegram bot via the lifespan context manager.
"""
import os
import sys
import uvicorn

if __name__ == "__main__":
    # Get the port from environment variable (Render provides PORT)
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Determine the correct module path based on where we're running from
    # If we're in the backend directory, use "main:app"
    # If we're in the root directory, use "backend.main:app"
    cwd = os.getcwd()
    if cwd.endswith("/backend") or cwd.endswith("\\backend"):
        app_module = "main:app"
    else:
        app_module = "backend.main:app"
    
    # Run uvicorn
    uvicorn.run(
        app_module,
        host=host,
        port=port,
        log_level="info"
    )
