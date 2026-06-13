
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

try:
    print("Testing imports...")
    from backend.main import app
    print("Successfully imported FastAPI app.")

    from backend.models import Base
    print("Successfully imported models.")

    from backend.database import engine
    print("Successfully imported database engine.")

    from backend.routers import issues, field_officer, voice
    print("Successfully imported routers.")

    print("All critical imports successful.")
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
