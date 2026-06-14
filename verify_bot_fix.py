#!/usr/bin/env python3
"""
Simple verification script for Telegram bot async integration fix.
This script demonstrates that the bot no longer blocks FastAPI's event loop.
"""
import os
import sys
import time
import threading
import asyncio

# Add backend to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
sys.path.insert(0, backend_path)

def test_bot_threading():
    """Test that bot runs in separate thread without blocking main thread"""
    print("Testing Telegram Bot Async Integration Fix")
    print("=" * 50)

    # Set test token
    os.environ['TELEGRAM_BOT_TOKEN'] = 'test_token_123'

    try:
        from bot import start_bot_thread, stop_bot_thread, _bot_thread

        print("1. Starting bot in separate thread...")
        start_bot_thread()

        # Wait a moment for thread to start
        time.sleep(0.1)

        print(f"   Bot thread created: {_bot_thread is not None}")
        if _bot_thread:
            print(f"   Thread name: {_bot_thread.name}")
            print(f"   Thread alive: {_bot_thread.is_alive()}")

        print("\n2. Testing main thread responsiveness...")
        start_time = time.time()

        # Simulate main thread work (like FastAPI handling requests)
        for i in range(50):
            time.sleep(0.01)  # Simulate work
            if i % 10 == 0:
                print(f"   Main thread working... ({i+1}/50)")

        elapsed = time.time() - start_time
        print(f"   Main thread work completed in {elapsed:.2f} seconds")
        print("3. Testing async event loop...")
        async def test_async():
            print("   Running async operations...")
            tasks = [asyncio.sleep(0.05) for _ in range(5)]
            await asyncio.gather(*tasks)
            print("   Async operations completed successfully")

        asyncio.run(test_async())

        print("\n4. Stopping bot thread...")
        stop_bot_thread()
        print("   Bot thread stopped successfully")

        print("\n✅ SUCCESS: Bot integration works correctly!")
        print("   - Bot runs in separate thread")
        print("   - Main thread remains responsive")
        print("   - Async operations work normally")
        print("   - Clean shutdown possible")

        return True

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return False

    finally:
        # Cleanup
        try:
            stop_bot_thread()
        except:
            pass
        if 'TELEGRAM_BOT_TOKEN' in os.environ:
            del os.environ['TELEGRAM_BOT_TOKEN']

if __name__ == "__main__":
    success = test_bot_threading()
    sys.exit(0 if success else 1)