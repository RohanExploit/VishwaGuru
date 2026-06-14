import os
import sys

# Set environment variables
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["GEMINI_API_KEY"] = "dummy_key"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"

# Add backend to path
sys.path.insert(0, "backend")

try:
    from backend.main import app
    print("✅ FastAPI app imported successfully")
    print("📋 Available routes:")
    
    routes = []
    for route in app.routes:
        methods = getattr(route, 'methods', {'GET'})
        path = route.path
        routes.append(f"{methods} {path}")
    
    # Sort and display routes
    for route in sorted(routes):
        print(f"  {route}")
    
    # Check for duplicate /api/detect-flooding routes
    flooding_routes = [r for r in routes if '/api/detect-flooding' in r]
    print(f"\n🔍 Flooding detection routes found: {len(flooding_routes)}")
    for route in flooding_routes:
        print(f"  {route}")
    
    if len(flooding_routes) > 1:
        print("❌ DUPLICATE ROUTES DETECTED!")
    else:
        print("✅ No duplicate routes found")
        
except Exception as e:
    print(f"❌ Error importing app: {e}")
    import traceback
    traceback.print_exc()