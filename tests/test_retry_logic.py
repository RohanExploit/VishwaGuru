"""
Tests for retry logic with exponential backoff in AI services.

This test suite verifies that AI services properly handle transient failures
with retry logic and exponential backoff.
"""
import pytest
import asyncio
import time
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from retry_utils import exponential_backoff_retry, sync_exponential_backoff_retry


class TestExponentialBackoffRetry:
    """Test the exponential backoff retry decorator for async functions."""
    
    @pytest.mark.asyncio
    async def test_successful_first_attempt(self):
        """Test that a function succeeding on first attempt returns immediately."""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=3, base_delay=0.1)
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = await successful_function()
        assert result == "success"
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_retry_after_failures(self):
        """Test that function retries after failures and eventually succeeds."""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=3, base_delay=0.1)
        async def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return "success"
        
        result = await failing_then_success()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_max_retries_exhausted(self):
        """Test that function raises exception after max retries exhausted."""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=2, base_delay=0.1)
        async def always_fails():
            nonlocal call_count
            call_count += 1
            raise ValueError("Persistent failure")
        
        with pytest.raises(ValueError, match="Persistent failure"):
            await always_fails()
        
        assert call_count == 3  # Initial attempt + 2 retries
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_timing(self):
        """Test that exponential backoff delays increase properly."""
        call_times = []
        
        @exponential_backoff_retry(max_retries=3, base_delay=0.1, exponential_base=2.0)
        async def timing_test():
            call_times.append(time.time())
            if len(call_times) < 4:
                raise Exception("Testing timing")
            return "success"
        
        await timing_test()
        
        # Verify we made 4 calls
        assert len(call_times) == 4
        
        # Verify delays (approximately)
        # First delay should be ~0.1s, second ~0.2s, third ~0.4s
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        delay3 = call_times[3] - call_times[2]
        
        # Allow some tolerance for timing
        assert 0.08 < delay1 < 0.15
        assert 0.18 < delay2 < 0.25
        assert 0.38 < delay3 < 0.45
    
    @pytest.mark.asyncio
    async def test_max_delay_cap(self):
        """Test that delays are capped at max_delay."""
        call_times = []
        
        @exponential_backoff_retry(
            max_retries=4,
            base_delay=1.0,
            max_delay=2.0,
            exponential_base=2.0
        )
        async def max_delay_test():
            call_times.append(time.time())
            if len(call_times) < 5:
                raise Exception("Testing max delay")
            return "success"
        
        await max_delay_test()
        
        # Verify delays are capped
        # After base*2^2 = 4s, but capped at 2s
        delay3 = call_times[3] - call_times[2]
        delay4 = call_times[4] - call_times[3]
        
        # Should both be capped at max_delay
        assert 1.9 < delay3 < 2.1
        assert 1.9 < delay4 < 2.1
    
    @pytest.mark.asyncio
    async def test_specific_exception_types(self):
        """Test that only specified exception types trigger retries."""
        call_count = 0
        
        @exponential_backoff_retry(
            max_retries=3,
            base_delay=0.1,
            exceptions=(ValueError,)
        )
        async def specific_exception_test():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("This should be retried")
            elif call_count == 2:
                raise RuntimeError("This should not be retried")
            return "success"
        
        with pytest.raises(RuntimeError, match="This should not be retried"):
            await specific_exception_test()
        
        # Should only be called twice (initial + 1 retry for ValueError)
        assert call_count == 2


class TestSyncExponentialBackoffRetry:
    """Test the exponential backoff retry decorator for sync functions."""
    
    def test_sync_successful_first_attempt(self):
        """Test that a sync function succeeding on first attempt returns immediately."""
        call_count = 0
        
        @sync_exponential_backoff_retry(max_retries=3, base_delay=0.1)
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_function()
        assert result == "success"
        assert call_count == 1
    
    def test_sync_retry_after_failures(self):
        """Test that sync function retries after failures."""
        call_count = 0
        
        @sync_exponential_backoff_retry(max_retries=3, base_delay=0.1)
        def failing_then_success():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Temporary failure")
            return "success"
        
        result = failing_then_success()
        assert result == "success"
        assert call_count == 2


class TestAIServiceRetryIntegration:
    """Test retry logic integration in AI services - simplified without full dependencies."""
    
    @pytest.mark.asyncio
    async def test_retry_decorator_with_mock_function(self):
        """Test that retry decorator works with async functions that simulate API calls."""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=3, base_delay=0.1)
        async def mock_api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API rate limit")
            return {"success": True, "data": "response"}
        
        result = await mock_api_call()
        
        # Should have retried and succeeded
        assert call_count == 3
        assert result["success"] is True
        assert "data" in result
    
    @pytest.mark.asyncio
    async def test_fallback_pattern_with_retry(self):
        """Test the fallback pattern used in AI services."""
        call_count = 0
        
        @exponential_backoff_retry(max_retries=2, base_delay=0.1)
        async def api_with_fallback_inner():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent API failure")
        
        async def api_with_fallback():
            try:
                return await api_with_fallback_inner()
            except Exception:
                # Return fallback after all retries exhausted
                return {"fallback": True, "message": "Using default response"}
        
        result = await api_with_fallback()
        
        # Should have tried 3 times (initial + 2 retries) then returned fallback
        assert call_count == 3
        assert result["fallback"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
