import sys
import os

# Add the current directory to sys.path
sys.path.append(os.getcwd())

try:
    from backend.routers.detection import (
        detect_public_facilities_endpoint,
        detect_construction_safety_endpoint
    )
    print("Successfully imported new endpoints from backend.routers.detection")
except ImportError as e:
    print(f"Failed to import new endpoints: {e}")
    sys.exit(1)
except Exception as e:
    print(f"An error occurred during import: {e}")
    sys.exit(1)

try:
    from backend.hf_api_service import (
        detect_public_facilities_clip,
        detect_construction_safety_clip
    )
    print("Successfully imported new service functions from backend.hf_api_service")
except ImportError as e:
    print(f"Failed to import new service functions: {e}")
    sys.exit(1)
