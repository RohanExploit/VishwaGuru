import sys
from unittest.mock import MagicMock

# Mock heavy dependencies
mock_pothole = MagicMock()
mock_pothole.detect_potholes = MagicMock()
mock_pothole.validate_image_for_processing = MagicMock()
sys.modules['backend.pothole_detection'] = mock_pothole

mock_garbage = MagicMock()
mock_garbage.detect_garbage = MagicMock()
sys.modules['backend.garbage_detection'] = mock_garbage

mock_local_ml = MagicMock()
mock_local_ml.detect_infrastructure_local = MagicMock()
mock_local_ml.detect_flooding_local = MagicMock()
mock_local_ml.detect_vandalism_local = MagicMock()
mock_local_ml.get_detection_status = MagicMock()
sys.modules['backend.local_ml_service'] = mock_local_ml

mock_hf = MagicMock()
# We need to mock everything imported from hf_api_service in main.py
hf_funcs = [
    'detect_illegal_parking_clip',
    'detect_street_light_clip',
    'detect_fire_clip',
    'detect_stray_animal_clip',
    'detect_blocked_road_clip',
    'detect_tree_hazard_clip',
    'detect_pest_clip',
    'detect_severity_clip',
    'detect_smart_scan_clip',
    'generate_image_caption',
    'analyze_urgency_text',
    'verify_resolution_vqa'
]
for func in hf_funcs:
    setattr(mock_hf, func, MagicMock())
sys.modules['backend.hf_api_service'] = mock_hf

mock_ai_factory = MagicMock()
mock_ai_factory.create_all_ai_services = MagicMock()
sys.modules['backend.ai_factory'] = mock_ai_factory

mock_ai_service = MagicMock()
mock_ai_service.generate_action_plan = MagicMock()
mock_ai_service.chat_with_civic_assistant = MagicMock()
sys.modules['backend.ai_service'] = mock_ai_service

mock_bot = MagicMock()
mock_bot.start_bot_thread = MagicMock()
mock_bot.stop_bot_thread = MagicMock()
sys.modules['backend.bot'] = mock_bot

mock_locator = MagicMock()
mock_locator.load_maharashtra_pincode_data = MagicMock()
mock_locator.load_maharashtra_mla_data = MagicMock()
mock_locator.find_constituency_by_pincode = MagicMock()
mock_locator.find_mla_by_constituency = MagicMock()
sys.modules['backend.maharashtra_locator'] = mock_locator

mock_gemini = MagicMock()
mock_gemini.get_ai_services = MagicMock()
mock_gemini.initialize_ai_services = MagicMock()
sys.modules['backend.gemini_services'] = mock_gemini

mock_init_db = MagicMock()
mock_init_db.migrate_db = MagicMock()
sys.modules['backend.init_db'] = mock_init_db

# Mock magic
sys.modules['magic'] = MagicMock()

import inspect
# Now try import
try:
    from backend.main import send_status_notification, app
    from backend.schemas import StatsResponse
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

def verify_backend():
    print("Verifying backend changes...")

    # Check if send_status_notification is sync
    if inspect.iscoroutinefunction(send_status_notification):
        print("FAIL: send_status_notification is async")
    else:
        print("PASS: send_status_notification is sync")

    # Check if /api/stats endpoint exists
    found_stats = False
    for route in app.routes:
        if route.path == "/api/stats":
            found_stats = True
            print("PASS: /api/stats endpoint found")
            break

    if not found_stats:
        print("FAIL: /api/stats endpoint not found")

    # Check StatsResponse schema
    try:
        fields = StatsResponse.model_fields
        required = ['total_issues', 'resolved_issues', 'pending_issues', 'issues_by_category']
        if all(field in fields for field in required):
            print("PASS: StatsResponse schema correct")
        else:
            print(f"FAIL: StatsResponse schema missing fields. Found: {list(fields.keys())}")
    except Exception as e:
        print(f"FAIL: StatsResponse check failed: {e}")

if __name__ == "__main__":
    verify_backend()
