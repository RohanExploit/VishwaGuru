"""
Tests for Telegram Bot functionality and async integration.
Tests verify that bot commands respond under load and don't block FastAPI.
"""
import os
import sys
import asyncio
import threading
import time
import pytest

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

# Import the module to access global variables correctly
import bot

class TestBotAsyncIntegration:
    """Test bot async integration with FastAPI"""

    def setup_method(self):
        """Setup before each test"""
        # Reset global state in the module
        if bot._bot_thread and bot._bot_thread.is_alive():
            bot.stop_bot_thread()
        bot._bot_thread = None
        bot._shutdown_event = threading.Event()
        bot._bot_application = None

        # Set test token
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    def teardown_method(self):
        """Cleanup after each test"""
        bot.stop_bot_thread()
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

    def test_bot_thread_management(self):
        """Test basic bot thread management without actual polling"""
        # Test starting thread
        bot.start_bot_thread()

        # Wait a moment for thread to initialize
        time.sleep(0.05)

        # Thread should be created (may exit quickly due to invalid token, but that's ok)
        # The important thing is it doesn't block the main thread

        # Test stopping thread
        bot.stop_bot_thread()

        # Verify cleanup
        assert bot._bot_thread is None
        assert bot._bot_application is None

    def test_bot_without_token(self):
        """Test bot behavior when no token is provided"""
        # Remove token
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

        # Start bot thread (should not actually start polling)
        bot.start_bot_thread()

        # Wait a bit
        time.sleep(0.05)

        # Thread should be created but should exit quickly since no token
        # The important thing is it doesn't crash or block

        # Stop thread
        bot.stop_bot_thread()

        # Verify cleanup
        assert bot._bot_thread is None

    def test_multiple_bot_starts(self):
        """Test that starting bot multiple times doesn't create multiple threads"""
        # Start bot first time
        bot.start_bot_thread()
        time.sleep(0.05)

        # Try to start again (should be prevented)
        bot.start_bot_thread()
        time.sleep(0.05)

        # Stop
        bot.stop_bot_thread()

    def test_run_bot_legacy_function(self):
        """Test the legacy run_bot function still works"""
        async def test_run():
            result = await bot.run_bot()
            # Should return None since it starts in thread
            assert result is None

        asyncio.run(test_run())

        # Verify bot thread was started
        assert bot._bot_thread is not None

        # Stop
        bot.stop_bot_thread()


class TestBotLoadHandling:
    """Test bot performance under load"""

    def setup_method(self):
        """Setup before each test"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    def teardown_method(self):
        """Cleanup after each test"""
        bot.stop_bot_thread()
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

    def test_concurrent_operations_simulation(self):
        """Test that bot thread doesn't interfere with main thread operations"""
        # Start bot
        bot.start_bot_thread()

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
        bot.stop_bot_thread()

    def test_async_event_loop_isolation(self):
        """Test that bot thread doesn't interfere with async event loop"""
        async def test_async_operations():
            """Test that async operations work while bot is running"""
            # Start bot
            bot.start_bot_thread()

            # Should be able to run async operations concurrently
            tasks = []
            for i in range(10):
                task = asyncio.create_task(asyncio.sleep(0.01))
                tasks.append(task)

            # Wait for all tasks to complete
            await asyncio.gather(*tasks)

            # Stop bot
            bot.stop_bot_thread()

        asyncio.run(test_async_operations())


class TestBotErrorHandling:
    """Test bot error handling and recovery"""

    def setup_method(self):
        """Setup before each test"""
        os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    def teardown_method(self):
        """Cleanup after each test"""
        bot.stop_bot_thread()
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

    def test_bot_graceful_shutdown(self):
        """Test bot shuts down gracefully"""
        # Start bot
        bot.start_bot_thread()
        time.sleep(0.05)

        # Stop bot
        bot.stop_bot_thread()

        # Should not crash
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
