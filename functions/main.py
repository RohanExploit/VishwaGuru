import sys
import os

# Add backend directory to sys.path so that absolute imports within backend work.
# When deployed, 'backend' and 'data' are copied into 'functions/' via predeploy script.
# Structure in Cloud Functions:
# /workspace/
#   main.py
#   backend/
#     main.py
#     database.py
#     ...
#   data/
#     responsibility_map.json
#     ...

# We add 'backend' to sys.path so 'import database' works from inside backend/main.py
backend_path = os.path.join(os.path.dirname(__file__), "backend")
sys.path.append(backend_path)

from firebase_functions import https_fn
from firebase_admin import initialize_app
from a2wsgi import ASGIMiddleware

# Initialize Firebase Admin
initialize_app()

# Import the FastAPI app
# We import from backend.main. Since 'backend' is a package in the root of source (after copy),
# 'from backend.main import app' works.
# However, backend/main.py uses absolute imports (e.g. 'from database import ...').
# By adding backend_path to sys.path, those imports resolve correctly.
try:
    from backend.main import app as fastapi_app
except ImportError as e:
    # Fallback for local testing if not copied yet or path issues
    print(f"Error importing backend: {e}")
    raise e

# Convert ASGI app to WSGI for Cloud Functions
wsgi_app = ASGIMiddleware(fastapi_app)

@https_fn.on_request(min_instances=0, max_instances=10)
def api(req: https_fn.Request) -> https_fn.Response:
    return https_fn.Response.from_app(wsgi_app, req.environ)
