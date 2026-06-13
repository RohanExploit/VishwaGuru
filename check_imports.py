import sys
import os
from pathlib import Path

# Mock dependencies that might be missing in a lightweight env but are used in routers
sys.modules['magic'] = None
sys.modules['indic'] = None

try:
    from backend.main import app
    print("✅ Successfully imported FastAPI app")
except ImportError as e:
    print(f"❌ ImportError: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
