"""
Test to verify thread-safe model loading in detection modules.
This test ensures that concurrent model loading doesn't create race conditions.
"""
import sys
import os
import threading
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

def test_garbage_detection_thread_safety():
    """Test that garbage detection model loading is thread-safe"""
    # Import the module
    import garbage_detection
    
    # Reset the model to None to simulate first-time loading
    garbage_detection._model = None
    
    # Track how many times the model was loaded and ensure sequential execution
    load_count = [0]
    load_order = []
    original_load = garbage_detection.load_model
    
    def wrapped_load():
        """Wrapper to count load calls and add delay to increase chance of race condition"""
        thread_id = threading.current_thread().name
        load_order.append(('start', thread_id, time.time()))
        load_count[0] += 1
        time.sleep(0.1)  # Small delay to simulate loading time
        result = "mock_model"  # Return a mock model instead of calling original (which needs dependencies)
        load_order.append(('end', thread_id, time.time()))
        return result
    
    # Replace load_model with wrapped version
    garbage_detection.load_model = wrapped_load
    
    # Create multiple threads that try to get the model
    threads = []
    results = []
    
    def get_model_thread():
        try:
            model = garbage_detection.get_model()
            results.append(model)
        except Exception as e:
            results.append(e)
    
    # Start 10 threads concurrently
    for i in range(10):
        t = threading.Thread(target=get_model_thread)
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Restore original function
    garbage_detection.load_model = original_load
    
    # Verify that model was loaded exactly once despite concurrent requests
    print(f"Model load count: {load_count[0]}")
    print(f"Load order: {load_order}")
    assert load_count[0] == 1, f"Model should be loaded exactly once, but was loaded {load_count[0]} times"
    
    # Verify all threads got the same result
    print(f"Thread results count: {len(results)}")
    assert len(results) == 10, f"Expected 10 results, got {len(results)}"
    assert all(r == "mock_model" for r in results), "All threads should get the same model instance"
    
    print("✓ Garbage detection model loading is thread-safe")

def test_pothole_detection_thread_safety():
    """Test that pothole detection model loading is thread-safe"""
    # Import the module
    import pothole_detection
    
    # Reset the model to None to simulate first-time loading
    pothole_detection._model = None
    
    # Track how many times the model was loaded and ensure sequential execution
    load_count = [0]
    load_order = []
    original_load = pothole_detection.load_model
    
    def wrapped_load():
        """Wrapper to count load calls and add delay to increase chance of race condition"""
        thread_id = threading.current_thread().name
        load_order.append(('start', thread_id, time.time()))
        load_count[0] += 1
        time.sleep(0.1)  # Small delay to simulate loading time
        result = "mock_model"  # Return a mock model instead of calling original (which needs dependencies)
        load_order.append(('end', thread_id, time.time()))
        return result
    
    # Replace load_model with wrapped version
    pothole_detection.load_model = wrapped_load
    
    # Create multiple threads that try to get the model
    threads = []
    results = []
    
    def get_model_thread():
        try:
            model = pothole_detection.get_model()
            results.append(model)
        except Exception as e:
            results.append(e)
    
    # Start 10 threads concurrently
    for i in range(10):
        t = threading.Thread(target=get_model_thread)
        threads.append(t)
        t.start()
    
    # Wait for all threads to complete
    for t in threads:
        t.join()
    
    # Restore original function
    pothole_detection.load_model = original_load
    
    # Verify that model was loaded exactly once despite concurrent requests
    print(f"Model load count: {load_count[0]}")
    print(f"Load order: {load_order}")
    assert load_count[0] == 1, f"Model should be loaded exactly once, but was loaded {load_count[0]} times"
    
    # Verify all threads got the same result
    print(f"Thread results count: {len(results)}")
    assert len(results) == 10, f"Expected 10 results, got {len(results)}"
    assert all(r == "mock_model" for r in results), "All threads should get the same model instance"
    
    print("✓ Pothole detection model loading is thread-safe")

if __name__ == "__main__":
    print("Testing thread-safe model loading...\n")
    
    print("Test 1: Garbage Detection Thread Safety")
    test_garbage_detection_thread_safety()
    
    print("\nTest 2: Pothole Detection Thread Safety")
    test_pothole_detection_thread_safety()
    
    print("\n✓ All thread safety tests passed!")
