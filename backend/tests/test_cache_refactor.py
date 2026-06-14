import time
import threading
import pytest
from unittest.mock import patch
from backend.cache import ThreadSafeCache

def test_cache_lru_eviction():
    cache = ThreadSafeCache(ttl=60, max_size=3)

    # set(data, key)
    cache.set("A", "a")
    cache.set("B", "b")
    cache.set("C", "c")

    # Access 'a' to make it MRU
    cache.get("a")

    # Add 'd', should evict 'b' (LRU)
    # Queue before: [b, c, a] (b is LRU)
    # Queue after: [c, a, d]
    cache.set("D", "d")

    assert cache.get("a") == "A"
    assert cache.get("b") is None
    assert cache.get("c") == "C"
    assert cache.get("d") == "D"

def test_cache_ttl_expiration():
    with patch('backend.cache.time.time') as mock_time:
        mock_time.return_value = 1000
        cache = ThreadSafeCache(ttl=10, max_size=10)

        # set(data, key)
        cache.set("A", "a")
        assert cache.get("a") == "A"

        # Advance time beyond TTL
        mock_time.return_value = 1011

        assert cache.get("a") is None

def test_cache_update_refresh():
    cache = ThreadSafeCache(ttl=60, max_size=2)

    cache.set("A1", "a")
    cache.set("B1", "b")

    # Update 'a', making it MRU
    cache.set("A2", "a")

    # Add 'c', should evict 'b' (LRU)
    # Queue before: [b, a]
    # Queue after: [a, c]
    cache.set("C1", "c")

    assert cache.get("a") == "A2"
    assert cache.get("b") is None
    assert cache.get("c") == "C1"

def test_thread_safety_concurrent_writes():
    """Verify thread safety under concurrent load."""
    cache = ThreadSafeCache(ttl=60, max_size=50)

    def worker():
        for i in range(100):
            # set(data, key)
            cache.set(i, f"key-{i}")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert cache.get_stats()["total_entries"] <= 50
