#!/usr/bin/env python3
"""
VishwaGuru Deployment Validation Script
Validates the deployment configuration and environment setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 9:
        print("Python version compatible")
        return True
    else:
        print(f"Python {version.major}.{version.minor} not compatible. Need Python 3.9+")
        return False

def check_dependencies():
    """Check if required packages can be installed"""
    try:
        result = subprocess.run([
            sys.executable, "-c",
            "import fastapi, uvicorn, sqlalchemy, pydantic; print('Core dependencies available')"
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print("Core dependencies available")
            return True
        else:
            print("Core dependencies missing")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"Error checking dependencies: {e}")
        return False

def check_environment_variables():
    """Check environment variable configuration"""
    required_vars = ["GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "FRONTEND_URL"]
    optional_vars = ["DATABASE_URL", "ENVIRONMENT", "DEBUG"]

    missing_required = []
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)

    if missing_required:
        print("Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        return False

    print("Required environment variables present")

    # Check optional variables
    for var in optional_vars:
        if os.getenv(var):
            print(f"{var} configured")
        else:
            print(f"{var} not set (will use defaults)")

    return True

def check_file_structure():
    """Check project file structure"""
    required_files = [
        "backend/main.py",
        "backend/requirements.txt",
        "render.yaml",
        "start-backend.py"
    ]

    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if missing_files:
        print("Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False

    print("Project structure correct")
    return True

def check_database_connectivity():
    """Test database connection"""
    try:
        from sqlalchemy import text
        from backend.database import engine
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful")
        return True
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False

def check_api_import():
    """Test backend API import"""
    try:
        # Set minimal environment for testing
        os.environ.setdefault("FRONTEND_URL", "http://localhost:5173")
        os.environ.setdefault("GEMINI_API_KEY", "test")
        os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")

        sys.path.insert(0, str(Path("backend").absolute()))
        import backend.main
        app = backend.main.app
        print("Backend API imports successfully")
        return True
    except Exception as e:
        print(f"Backend API import failed: {e}")
        return False

def main():
    """Run all validation checks"""
    print("🔍 VishwaGuru Deployment Validation")
    print("=" * 40)

    checks = [
        ("Python Version", check_python_version),
        ("File Structure", check_file_structure),
        ("Dependencies", check_dependencies),
        ("Environment Variables", check_environment_variables),
        ("API Import", check_api_import),
        ("Database Connectivity", check_database_connectivity),
    ]

    passed = 0
    total = len(checks)

    for name, check_func in checks:
        print(f"\n📋 Checking {name}...")
        if check_func():
            passed += 1

    print(f"\n📊 Validation Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 All validation checks passed! Ready for deployment.")
        print("\n🚀 Next steps:")
        print("1. Set environment variables in Render dashboard")
        print("2. Deploy to Render using render.yaml")
        print("3. Test API endpoints")
        print("4. Update frontend with backend URL")
        return 0
    else:
        print("⚠️  Some validation checks failed. Please fix issues before deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())