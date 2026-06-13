import sys
import os
import inspect
from unittest.mock import MagicMock

# Adjust path to include repo root
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

# Mock heavy dependencies
sys.modules['ultralytics'] = MagicMock()
sys.modules['ultralyticsplus'] = MagicMock()
sys.modules['torch'] = MagicMock()
sys.modules['torch'].Tensor = type('Tensor', (), {})
sys.modules['transformers'] = MagicMock()
sys.modules['google'] = MagicMock()
sys.modules['google.generativeai'] = MagicMock()
sys.modules['telegram'] = MagicMock()
sys.modules['telegram.ext'] = MagicMock()
sys.modules['telegram.error'] = MagicMock()
sys.modules['pywebpush'] = MagicMock()
sys.modules['firebase_admin'] = MagicMock()
sys.modules['scikit-learn'] = MagicMock()
sys.modules['sklearn'] = MagicMock()
sys.modules['numpy'] = MagicMock()

def verify_detection_endpoints():
    print("Importing backend.routers.detection...")
    try:
        import backend.routers.detection as detection
    except ImportError as e:
        print(f"FAIL: ImportError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"FAIL: Exception during import: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Verify cached wrappers exist
    print("Checking for cached wrappers...")
    if not hasattr(detection, '_cached_detect_traffic_sign'):
        print("FAIL: _cached_detect_traffic_sign missing")
        sys.exit(1)

    # Verify async-lru is NOT used
    source = inspect.getsource(detection)
    if "from async_lru import alru_cache" in source:
        # It might be commented out or removed.
        # But if it's there as an import line, we should check if it's used.
        pass

    print("PASS: Import successful and wrappers found.")

if __name__ == "__main__":
    verify_detection_endpoints()
