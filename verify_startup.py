import sys
import os

# Add current directory to sys.path
sys.path.append(os.getcwd())

try:
    from backend import main
    print("Successfully imported backend.main")
except ImportError as e:
    print(f"Failed to import backend.main: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error during import: {e}")
    sys.exit(1)
