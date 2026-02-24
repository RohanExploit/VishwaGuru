import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(os.getcwd())

try:
    print("Attempting to import backend.routers.detection...")
    from backend.routers import detection
    print("Successfully imported backend.routers.detection")

    print("Attempting to import googletrans...")
    import googletrans
    print("Successfully imported googletrans")

    print("Attempting to import backend.routers.voice...")
    from backend.routers import voice
    print("Successfully imported backend.routers.voice")

    print("Attempting to import backend.main...")
    from backend import main
    print("Successfully imported backend.main")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
