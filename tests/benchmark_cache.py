
import time
import random
import string
from backend.cache import ThreadSafeCache

def benchmark_cache():
    max_size = 1000
    cache = ThreadSafeCache(ttl=300, max_size=max_size)

    # Fill cache
    print(f"Filling cache with {max_size} items...")
    for i in range(max_size):
        cache.set(f"value_{i}", f"key_{i}")

    # Benchmark O(1) eviction
    print("Benchmarking eviction speed (should be O(1))...")
    start_time = time.time()
    for i in range(max_size, max_size + 1000):
        cache.set(f"value_{i}", f"key_{i}")
    end_time = time.time()
    print(f"Time to add 1000 items with eviction: {end_time - start_time:.4f}s")

    # Verify LRU behavior
    cache = ThreadSafeCache(ttl=300, max_size=3)
    cache.set("v1", "k1")
    cache.set("v2", "k2")
    cache.set("v3", "k3")

    # Access k1 to move it to end
    cache.get("k1")

    # Set k4, should evict k2 (oldest non-accessed)
    cache.set("v4", "k4")

    assert cache.get("k2") is None
    assert cache.get("k1") == "v1"
    assert cache.get("k3") == "v3"
    assert cache.get("k4") == "v4"
    print("LRU behavior verified.")

if __name__ == "__main__":
    benchmark_cache()
