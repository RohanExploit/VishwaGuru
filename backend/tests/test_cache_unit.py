import time
import collections
from backend.cache import ThreadSafeCache


def test_cache_set_get():
    cache = ThreadSafeCache(ttl=60, max_size=10)
    cache.set("value1", "key1")
    assert cache.get("key1") == "value1"
    assert cache.get("key2") is None


def test_cache_expiration():
    # Cache with 0 TTL should expire immediately
    cache = ThreadSafeCache(ttl=0, max_size=10)
    cache.set("value1", "key1")
    # Small sleep to ensure time.time() might move a bit if resolution allows,
    # but with ttl=0 it should expire if we call get() even slightly after set()
    # Actually _cleanup_expired uses >= ttl
    assert cache.get("key1") is None


def test_cache_lru_eviction():
    cache = ThreadSafeCache(ttl=60, max_size=2)
    cache.set("v1", "k1")
    cache.set("v2", "k2")
    cache.set("v3", "k3")  # Should evict k1

    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"
    assert cache.get("k3") == "v3"


def test_cache_cleanup_logic():
    cache = ThreadSafeCache(ttl=1, max_size=10)
    cache.set("v1", "k1")
    time.sleep(1.1)
    cache.set("v2", "k2")  # Should trigger cleanup of k1

    stats = cache.get_stats()
    # total_entries might still be 1 if cleanup worked
    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"


def test_cache_ordered_cleanup():
    cache = ThreadSafeCache(ttl=1, max_size=10)
    cache.set("v1", "k1")
    time.sleep(0.5)
    cache.set("v2", "k2")
    time.sleep(0.6)
    # k1 is now > 1.1s old (expired)
    # k2 is now 0.6s old (not expired)

    # Trigger cleanup
    cache._cleanup_expired()

    assert cache.get("k1") is None
    assert cache.get("k2") == "v2"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__])
