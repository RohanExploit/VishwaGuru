import os
import sys

# Set environment variables
os.environ["FRONTEND_URL"] = "http://localhost:5173"
os.environ["GEMINI_API_KEY"] = "dummy_key"
os.environ["TELEGRAM_BOT_TOKEN"] = "dummy_token"

# Add backend to path
sys.path.insert(0, "backend")

# Mock missing dependencies
class MockMagic:
    @staticmethod
    def from_buffer(data, mime=False):
        return "image/jpeg"

sys.modules['magic'] = MockMagic()

# Mock other dependencies that might be missing
class MockModule:
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

for module in ['httpx', 'sqlalchemy', 'pydantic', 'PIL']:
    if module not in sys.modules:
        sys.modules[module] = MockModule()

try:
    # Check the main.py file for duplicate route definitions
    with open("backend/main.py", "r") as f:
        content = f.read()
    
    print("Route Analysis:")
    print("=" * 50)
    
    # Find all @app.post and @app.get decorators
    import re
    route_pattern = r'@app\.(get|post|put|delete)\("([^"]+)"'
    routes = re.findall(route_pattern, content)
    
    print(f"Total routes found: {len(routes)}")
    print()
    
    # Group by path
    route_paths = {}
    for method, path in routes:
        if path not in route_paths:
            route_paths[path] = []
        route_paths[path].append(method.upper())
    
    # Display all routes
    for path in sorted(route_paths.keys()):
        methods = route_paths[path]
        print(f"  {methods} {path}")
    
    print()
    print("Duplicate Route Check:")
    print("=" * 30)
    
    # Check for duplicates
    duplicates = {path: methods for path, methods in route_paths.items() if len(methods) > 1}
    
    if duplicates:
        print("DUPLICATE ROUTES FOUND:")
        for path, methods in duplicates.items():
            print(f"  {path}: {methods}")
    else:
        print("No duplicate routes found!")
    
    # Specific check for flooding endpoint
    flooding_routes = [path for path in route_paths.keys() if 'detect-flooding' in path]
    print(f"\nFlooding detection routes: {len(flooding_routes)}")
    for path in flooding_routes:
        print(f"  {route_paths[path]} {path}")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()