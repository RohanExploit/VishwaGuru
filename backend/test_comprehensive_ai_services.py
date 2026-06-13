"""
Comprehensive test for AI service dependency injection including detection services.
"""
import asyncio
import os
from ai_interfaces import initialize_ai_services, get_ai_services
from ai_factory import create_all_ai_services
from PIL import Image


async def test_all_services():
    """Test that all AI services (including detection) can be initialized and used."""
    print("Testing comprehensive AI service dependency injection...\n")

    # Set to mock mode for testing
    os.environ["AI_SERVICE_TYPE"] = "mock"
    
    # Test service creation
    print("1. Creating all services...")
    services = create_all_ai_services()
    print(f"   ✓ Created {len(services)} services")
    
    # Test initialization
    print("\n2. Initializing services...")
    initialize_ai_services(*services)
    ai_services = get_ai_services()
    print("   ✓ Services initialized")
    
    # Test action plan generation
    print("\n3. Testing action plan service...")
    action_plan = await ai_services.action_plan_service.generate_action_plan(
        "Pothole on main road", "pothole"
    )
    assert "whatsapp" in action_plan
    assert "email_subject" in action_plan
    assert "email_body" in action_plan
    print("   ✓ Action plan service works")
    
    # Test chat service
    print("\n4. Testing chat service...")
    response = await ai_services.chat_service.chat("Hello, how are you?")
    assert isinstance(response, str)
    assert len(response) > 0
    print("   ✓ Chat service works")
    
    # Test MLA summary service
    print("\n5. Testing MLA summary service...")
    summary = await ai_services.mla_summary_service.generate_mla_summary(
        "Mumbai", "Dadar", "John Doe"
    )
    assert isinstance(summary, str)
    assert len(summary) > 0
    print("   ✓ MLA summary service works")
    
    # Create a dummy test image
    test_image = Image.new('RGB', (100, 100), color='red')
    
    # Test vandalism detection service
    print("\n6. Testing vandalism detection service...")
    if ai_services.vandalism_detection_service:
        detections = await ai_services.vandalism_detection_service.detect(test_image)
        assert isinstance(detections, list)
        print("   ✓ Vandalism detection service works")
    else:
        print("   ⚠ Vandalism detection service not initialized")
    
    # Test infrastructure detection service
    print("\n7. Testing infrastructure detection service...")
    if ai_services.infrastructure_detection_service:
        detections = await ai_services.infrastructure_detection_service.detect(test_image)
        assert isinstance(detections, list)
        print("   ✓ Infrastructure detection service works")
    else:
        print("   ⚠ Infrastructure detection service not initialized")
    
    # Test flooding detection service
    print("\n8. Testing flooding detection service...")
    if ai_services.flooding_detection_service:
        detections = await ai_services.flooding_detection_service.detect(test_image)
        assert isinstance(detections, list)
        print("   ✓ Flooding detection service works")
    else:
        print("   ⚠ Flooding detection service not initialized")
    
    # Test pothole detection service
    print("\n9. Testing pothole detection service...")
    if ai_services.pothole_detection_service:
        detections = await ai_services.pothole_detection_service.detect(test_image)
        assert isinstance(detections, list)
        print("   ✓ Pothole detection service works")
    else:
        print("   ⚠ Pothole detection service not initialized")
    
    # Test garbage detection service
    print("\n10. Testing garbage detection service...")
    if ai_services.garbage_detection_service:
        detections = await ai_services.garbage_detection_service.detect(test_image)
        assert isinstance(detections, list)
        print("   ✓ Garbage detection service works")
    else:
        print("   ⚠ Garbage detection service not initialized")
    
    print("\n" + "="*60)
    print("✅ All comprehensive AI service tests passed!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(test_all_services())
