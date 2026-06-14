#!/usr/bin/env python3
"""
Manual integration test for AI service retry logic.
This script tests the retry behavior with mock failures.
"""
import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from retry_utils import exponential_backoff_retry


async def test_retry_with_transient_failure():
    """Test that retry works with transient failures."""
    print("\n=== Test 1: Retry with Transient Failure ===")
    
    call_count = 0
    
    @exponential_backoff_retry(max_retries=3, base_delay=0.5)
    async def simulated_api_call():
        nonlocal call_count
        call_count += 1
        print(f"  Attempt {call_count}...")
        
        if call_count < 3:
            raise Exception(f"Simulated network error (attempt {call_count})")
        
        return {"status": "success", "data": "API response"}
    
    try:
        result = await simulated_api_call()
        print(f"✓ Success after {call_count} attempts: {result}")
        assert call_count == 3, "Should have succeeded on 3rd attempt"
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False
    
    return True


async def test_retry_exhaustion():
    """Test that retry stops after max attempts."""
    print("\n=== Test 2: Retry Exhaustion ===")
    
    call_count = 0
    
    @exponential_backoff_retry(max_retries=2, base_delay=0.2)
    async def always_failing_api():
        nonlocal call_count
        call_count += 1
        print(f"  Attempt {call_count}...")
        raise Exception("Persistent API failure")
    
    try:
        await always_failing_api()
        print("✗ Should have raised exception")
        return False
    except Exception as e:
        print(f"✓ Failed after {call_count} attempts as expected: {e}")
        assert call_count == 3, "Should have tried 3 times (initial + 2 retries)"
        return True


async def test_immediate_success():
    """Test that no retry happens on immediate success."""
    print("\n=== Test 3: Immediate Success (No Retry) ===")
    
    call_count = 0
    
    @exponential_backoff_retry(max_retries=3, base_delay=0.5)
    async def successful_api():
        nonlocal call_count
        call_count += 1
        print(f"  Attempt {call_count}...")
        return {"status": "success"}
    
    try:
        result = await successful_api()
        print(f"✓ Success on first attempt: {result}")
        assert call_count == 1, "Should have succeeded on 1st attempt"
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


async def test_fallback_pattern():
    """Test the fallback pattern used in AI services."""
    print("\n=== Test 4: Fallback Pattern ===")
    
    call_count = 0
    
    @exponential_backoff_retry(max_retries=2, base_delay=0.2)
    async def api_with_retries():
        nonlocal call_count
        call_count += 1
        print(f"  Attempt {call_count}...")
        raise Exception("API unavailable")
    
    async def api_with_fallback():
        try:
            return await api_with_retries()
        except Exception as e:
            print(f"  All retries exhausted, using fallback...")
            return {"fallback": True, "message": "Default response"}
    
    result = await api_with_fallback()
    print(f"✓ Fallback activated after {call_count} attempts: {result}")
    assert result["fallback"] is True
    assert call_count == 3, "Should have tried 3 times before fallback"
    
    return True


async def main():
    """Run all integration tests."""
    print("=" * 60)
    print("AI Service Retry Logic Integration Tests")
    print("=" * 60)
    
    tests = [
        test_retry_with_transient_failure,
        test_retry_exhaustion,
        test_immediate_success,
        test_fallback_pattern
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
