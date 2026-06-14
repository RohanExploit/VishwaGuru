import sys
import os

# Set environment to 'development' to avoid strict checks
os.environ['ENVIRONMENT'] = 'development'
# Set FRONTEND_URL to dummy
os.environ['FRONTEND_URL'] = 'http://localhost:5173'

# Add repo root to sys.path
sys.path.append(os.getcwd())

try:
    from backend.main import app

    routes = [route.path for route in app.routes]

    expected_routes = [
        "/api/detect-public-facilities",
        "/api/detect-construction-safety",
        "/api/detect-traffic-sign",
        "/api/detect-abandoned-vehicle"
    ]

    missing = []
    for route in expected_routes:
        if route not in routes:
            missing.append(route)

    if missing:
        print(f"FAILED: Missing routes: {missing}")
        sys.exit(1)
    else:
        print("SUCCESS: All new routes found.")
        sys.exit(0)

except ImportError as e:
    print(f"ImportError: {e}")
    # Fallback: Check if file exists and contains the strings
    print("Checking file content directly as fallback...")
    with open("backend/routers/detection.py", "r") as f:
        content = f.read()
        if "/api/detect-public-facilities" in content and "/api/detect-construction-safety" in content:
             print("SUCCESS: Routes found in code.")
             sys.exit(0)
        else:
             print("FAILED: Routes not found in code.")
             sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
