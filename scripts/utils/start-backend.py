#!/usr/bin/env python3
"""
VishwaGuru Backend Startup Script
Handles environment validation and application startup.
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add project root to Python path to ensure 'backend.*' imports work
repo_root = Path(__file__).parent.absolute()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

def validate_environment():
    """Validate required environment variables"""
    required_vars = ["GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "FRONTEND_URL"]
    missing_vars = []

    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables or create a .env file.")
        print("See backend/.env.example for reference.")
        return False

    # Set defaults for optional variables
    if not os.getenv("DATABASE_URL"):
        os.environ["DATABASE_URL"] = "sqlite:///./data/issues.db"

    if not os.getenv("ENVIRONMENT"):
        os.environ["ENVIRONMENT"] = "production"

    if not os.getenv("DEBUG"):
        os.environ["DEBUG"] = "false"

    # Check for optional HF_TOKEN
    if not os.getenv("HF_TOKEN"):
        print("⚠️  HF_TOKEN is missing. AI features using Hugging Face will be disabled.")
    else:
        print("✅ HF_TOKEN found")

    print("✅ Environment validation passed")
    return True

def create_data_directory():
    """Create data directory for SQLite database"""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print("✅ Data directory ready")

def main():
    """Main startup function"""
    print("🚀 Starting VishwaGuru Backend")

    if not validate_environment():
        sys.exit(1)

    create_data_directory()

    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"📡 Starting server on {host}:{port}")

    # Start the server
    # We use the full module path 'backend.main:app' because we added repo_root to sys.path
    uvicorn.run(
        "backend.main:app",
        host=host,
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )

if __name__ == "__main__":
    main()