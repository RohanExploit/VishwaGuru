import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

try:
    print("Importing backend.main...")
    from backend.main import app
    print("Successfully imported backend.main")
except Exception as e:
    print(f"FAILED to import backend.main: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Importing backend.routers.issues...")
    from backend.routers import issues
    print("Successfully imported backend.routers.issues")
except Exception as e:
    print(f"FAILED to import backend.routers.issues: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

try:
    print("Importing backend.routers.detection...")
    from backend.routers import detection
    print("Successfully imported backend.routers.detection")
except Exception as e:
    print(f"FAILED to import backend.routers.detection: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
