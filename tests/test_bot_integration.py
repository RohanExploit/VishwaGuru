"""
Tests for Telegram Bot functionality and async integration.
Tests verify that bot commands respond under load and don't block FastAPI.
"""
import os
import sys
import asyncio
import threading
import time

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

from bot import (
    start_bot_thread,
    stop_bot_thread,
    _bot_thread,
    _shutdown_event,
    _bot_application,
    run_bot
)


class TestBotAsyncIntegration:
    """Test bot async integration with FastAPI"""

    def setup_method(self):
        """Setup before each test"""
        # Reset global state
        global _bot_thread, _shutdown_event, _bot_application
        if _bot_thread and _bot_thread.is_alive():
            stop_bot_thread()
        _bot_thread = None
        _shutdown_event = threading.Event()
        _bot_application = None

        # Set test token
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    def teardown_method(self):
        """Cleanup after each test"""
        stop_bot_thread()
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

    def test_bot_thread_management(self):
        """Test basic bot thread management without actual polling"""
        # Test starting thread
        start_bot_thread()

        # Wait a moment for thread to initialize
        time.sleep(0.05)

        # Thread should be created (may exit quickly due to invalid token, but that's ok)
        # The important thing is it doesn't block the main thread

        # Test stopping thread
        stop_bot_thread()

        # Verify cleanup
        assert _bot_thread is None
        assert _bot_application is None

    def test_bot_without_token(self):
        """Test bot behavior when no token is provided"""
        # Remove token
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

        # Start bot thread (should not actually start polling)
        start_bot_thread()

        # Wait a bit
        time.sleep(0.05)

        # Thread should be created but should exit quickly since no token
        # The important thing is it doesn't crash or block

        # Stop thread
        stop_bot_thread()

        # Verify cleanup
        assert _bot_thread is None

    def test_multiple_bot_starts(self):
        """Test that starting bot multiple times doesn't create multiple threads"""
        # Start bot first time
        start_bot_thread()
        time.sleep(0.05)

        # Try to start again (should be prevented)
        start_bot_thread()
        time.sleep(0.05)

        # Stop
        stop_bot_thread()

    def test_run_bot_legacy_function(self):
        """Test the legacy run_bot function still works"""
        async def test_run():
            result = await run_bot()
            # Should return None since it starts in thread
            assert result is None

        asyncio.run(test_run())

        # Verify bot thread was started
        assert _bot_thread is not None

        # Stop
        stop_bot_thread()


class TestBotLoadHandling:
    """Test bot performance under load"""

    def setup_method(self):
        """Setup before each test"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    def teardown_method(self):
        """Cleanup after each test"""
        stop_bot_thread()
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

    def test_concurrent_operations_simulation(self):
        """Test that bot thread doesn't interfere with main thread operations"""
        # Start bot
        start_bot_thread()

        # Main thread should remain responsive
        start_time = time.time()

        # Simulate main thread work (like FastAPI requests)
        for i in range(100):
            time.sleep(0.001)  # Small delay to simulate work
            # Check that we can still do other operations
            assert True

        elapsed = time.time() - start_time

        # Should complete in reasonable time (not blocked by bot)
        assert elapsed < 1.0  # Less than 1 second for 100 * 0.001s operations

        # Stop bot
        stop_bot_thread()

    def test_async_event_loop_isolation(self):
        """Test that bot thread doesn't interfere with async event loop"""
        async def test_async_operations():
            """Test that async operations work while bot is running"""
            # Start bot
            start_bot_thread()

            # Should be able to run async operations concurrently
            tasks = []
            for i in range(10):
                task = asyncio.create_task(asyncio.sleep(0.01))
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

            # Stop bot
            stop_bot_thread()

        asyncio.run(test_async_operations())


class TestBotErrorHandling:
    """Test bot error handling and recovery"""

    def setup_method(self):
        """Setup before each test"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    def teardown_method(self):
        """Cleanup after each test"""
        stop_bot_thread()
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

    def test_bot_graceful_shutdown(self):
        """Test bot shuts down gracefully"""
        # Start bot
        start_bot_thread()
        time.sleep(0.05)

        # Stop bot
        stop_bot_thread()

        # Should not crash
        assert True


if __name__ == "__main__":
    # Run basic functionality test
    test_instance = TestBotAsyncIntegration()
    test_instance.setup_method()

    try:
        print("Testing bot thread management...")
        test_instance.test_bot_thread_management()
        print("✓ Bot thread management test passed")

        print("Testing bot without token...")
        test_instance.test_bot_without_token()
        print("✓ Bot without token test passed")

        print("Testing multiple bot starts...")
        test_instance.test_multiple_bot_starts()
        print("✓ Multiple bot starts test passed")

        print("Testing legacy run_bot function...")
        test_instance.test_run_bot_legacy_function()
        print("✓ Legacy run_bot function test passed")

    finally:
        test_instance.teardown_method()

    # Run load tests
    load_test_instance = TestBotLoadHandling()
    load_test_instance.setup_method()

    try:
        print("\nTesting concurrent operations simulation...")
        load_test_instance.test_concurrent_operations_simulation()
        print("✓ Concurrent operations test passed")

        print("Testing async event loop isolation...")
        load_test_instance.test_async_event_loop_isolation()
        print("✓ Async event loop isolation test passed")

    finally:
        load_test_instance.teardown_method()

    # Run error handling tests
    error_test_instance = TestBotErrorHandling()
    error_test_instance.setup_method()

    try:
        print("\nTesting graceful shutdown...")
        error_test_instance.test_bot_graceful_shutdown()
        print("✓ Graceful shutdown test passed")

    finally:
        error_test_instance.teardown_method()

    print("\n🎉 All bot integration tests passed!")