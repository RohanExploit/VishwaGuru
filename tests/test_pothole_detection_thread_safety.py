"""
Test suite for thread-safe model loading in pothole_detection module.

This module tests the thread-safe singleton pattern implementation for
the pothole detection model to ensure:
1. Only one model instance is created across concurrent requests
2. Race conditions are properly prevented
3. Error handling works correctly in multi-threaded scenarios
4. Reset functionality works as expected for testing purposes

Issue: #72 - Potential Race Conditions in Model Loading
Author: motalib-code
Date: 2026-01-07
"""

import pytest
import threading
import time
import unittest
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestThreadSafeModelLoading:
    """Test class for thread-safe model loading functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset the model state before and after each test."""
        # Import here to get fresh module state
        from pothole_detection import reset_model
        reset_model()
        yield
        reset_model()

    @patch('pothole_detection.load_model')
    def test_single_thread_model_loading(self, mock_load_model):
        """Test that model loads correctly in a single-threaded scenario."""
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        result = get_model()
        
        assert result == mock_model
        mock_load_model.assert_called_once()

    @patch('pothole_detection.load_model')
    def test_model_loaded_only_once_with_multiple_calls(self, mock_load_model):
        """Test that the model is only loaded once even with multiple get_model calls."""
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        # Call get_model multiple times
        results = [get_model() for _ in range(10)]
        
        # All results should be the same model instance
        assert all(r == mock_model for r in results)
        # load_model should have been called exactly once
        mock_load_model.assert_called_once()

    @patch('pothole_detection.load_model')
    def test_concurrent_access_single_load(self, mock_load_model):
        """
        Test that concurrent access from multiple threads only triggers
        a single model load operation (core race condition test).
        """
        load_count = 0
        load_lock = threading.Lock()
        
        def mock_load():
            nonlocal load_count
            with load_lock:
                load_count += 1
            # Simulate slow model loading to increase chance of race condition
            time.sleep(0.1)
            return MagicMock()
        
        mock_load_model.side_effect = mock_load
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        num_threads = 20
        results = []
        errors = []
        
        def worker():
            try:
                model = get_model()
                results.append(model)
            except Exception as e:
                errors.append(e)
        
        # Create and start all threads simultaneously
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Assertions
        assert len(errors) == 0, f"Unexpected errors: {errors}"
        assert len(results) == num_threads
        assert load_count == 1, f"Model was loaded {load_count} times instead of 1"
        # All threads should have received the same model instance
        assert all(r == results[0] for r in results)

    @patch('pothole_detection.load_model')
    def test_concurrent_access_with_thread_pool(self, mock_load_model):
        """Test concurrent access using ThreadPoolExecutor."""
        mock_model = MagicMock()
        load_event = threading.Event()
        load_count = [0]  # Use list to avoid nonlocal issues
        
        def slow_load():
            load_count[0] += 1
            time.sleep(0.05)  # Simulate loading time
            return mock_model
        
        mock_load_model.side_effect = slow_load
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(get_model) for _ in range(50)]
            results = [f.result() for f in as_completed(futures)]
        
        assert load_count[0] == 1, f"Expected 1 load, got {load_count[0]}"
        assert all(r == mock_model for r in results)

    @patch('pothole_detection.load_model')
    def test_error_handling_during_model_load(self, mock_load_model):
        """Test that errors during model loading are properly propagated."""
        mock_load_model.side_effect = RuntimeError("Model loading failed!")
        
        from pothole_detection import get_model, reset_model
        from backend.exceptions import ModelLoadException
        reset_model()
        
        # Expect ModelLoadException (wrapper) or RuntimeError depending on implementation
        with pytest.raises((RuntimeError, ModelLoadException)):
            get_model()

    @patch('pothole_detection.load_model')
    def test_error_cached_and_reraised(self, mock_load_model):
        """Test that loading errors are cached and re-raised on subsequent calls."""
        original_error = RuntimeError("Model loading failed!")
        mock_load_model.side_effect = original_error
        
        from pothole_detection import get_model, reset_model
        from backend.exceptions import ModelLoadException
        reset_model()
        
        # First call should raise the error
        with pytest.raises((RuntimeError, ModelLoadException)):
            get_model()
        
        # Subsequent calls should also raise an error (wrapped or original)
        # without triggering another load attempt
        mock_load_model.reset_mock()
        
        with pytest.raises((RuntimeError, ModelLoadException)):
            get_model()
        
        # load_model should NOT have been called again
        mock_load_model.assert_not_called()

    @patch('pothole_detection.load_model')
    def test_concurrent_error_handling(self, mock_load_model):
        """Test that errors are handled correctly in concurrent scenarios."""
        mock_load_model.side_effect = RuntimeError("Concurrent load failed!")
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        errors = []
        
        def worker():
            try:
                get_model()
            except Exception as e:
                errors.append(e)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # All threads should have received an error
        assert len(errors) == 10
        # load_model should have been called only once
        assert mock_load_model.call_count == 1

    @patch('pothole_detection.load_model')
    def test_reset_model_allows_reload(self, mock_load_model):
        """Test that reset_model allows the model to be reloaded."""
        mock_model_1 = MagicMock(name="model_1")
        mock_model_2 = MagicMock(name="model_2")
        mock_load_model.side_effect = [mock_model_1, mock_model_2]
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        # First load
        result_1 = get_model()
        assert result_1 == mock_model_1
        
        # Reset
        reset_model()
        
        # Second load should get a new model
        result_2 = get_model()
        assert result_2 == mock_model_2
        
        # load_model should have been called twice
        assert mock_load_model.call_count == 2

    @patch('pothole_detection.load_model')
    def test_reset_is_thread_safe(self, mock_load_model):
        """Test that reset_model is thread-safe."""
        mock_load_model.return_value = MagicMock()
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        errors = []
        
        def worker_get():
            try:
                for _ in range(10):
                    get_model()
                    time.sleep(0.001)
            except Exception as e:
                errors.append(e)
        
        def worker_reset():
            try:
                for _ in range(5):
                    reset_model()
                    time.sleep(0.002)
            except Exception as e:
                errors.append(e)
        
        threads = [
            threading.Thread(target=worker_get) for _ in range(5)
        ] + [
            threading.Thread(target=worker_reset) for _ in range(2)
        ]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # No errors should have occurred from the concurrent access
        assert len(errors) == 0, f"Unexpected errors: {errors}"


class TestModelLoadingPerformance:
    """Performance tests for the thread-safe model loading."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Reset the model state before and after each test."""
        from pothole_detection import reset_model
        reset_model()
        yield
        reset_model()

    @patch('pothole_detection.load_model')
    def test_fast_path_after_initialization(self, mock_load_model):
        """
        Test that after initialization, subsequent calls use the fast path
        and don't acquire the lock (performance optimization).
        """
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        # Initial load
        get_model()
        
        # Time subsequent calls (fast path)
        start = time.perf_counter()
        for _ in range(10000):
            get_model()
        elapsed = time.perf_counter() - start
        
        # Should be very fast (no lock acquisition)
        # This is a soft assertion - actual timing depends on system
        assert elapsed < 1.0, f"Fast path took too long: {elapsed}s"

    @patch('pothole_detection.load_model')
    def test_high_concurrency_stress_test(self, mock_load_model):
        """Stress test with high concurrency."""
        mock_load_model.return_value = MagicMock()
        
        from pothole_detection import get_model, reset_model
        reset_model()
        
        num_threads = 100
        calls_per_thread = 100
        results = []
        lock = threading.Lock()
        
        def worker():
            local_results = []
            for _ in range(calls_per_thread):
                model = get_model()
                local_results.append(id(model))
            with lock:
                results.extend(local_results)
        
        threads = [threading.Thread(target=worker) for _ in range(num_threads)]
        
        start = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - start
        
        # All results should be the same model instance
        assert len(set(results)) == 1
        assert len(results) == num_threads * calls_per_thread
        # load_model should have been called exactly once
        mock_load_model.assert_called_once()
        
        print(f"High concurrency stress test completed in {elapsed:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
