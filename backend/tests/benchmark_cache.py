import time
import collections
import threading
import sys
import os

# Add parent directory to path to import backend.cache
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.cache import ThreadSafeCache

def benchmark_cache(cache_size, num_ops):
    cache = ThreadSafeCache(ttl=300, max_size=cache_size)

    # Fill cache
    for i in range(cache_size):
        cache.set(data=i, key=f"key{i}")

    start_time = time.time()
    for i in range(num_ops):
        # Update existing keys to keep the cache full and trigger cleanup
        cache.set(data=i, key=f"key{i % cache_size}")
    end_time = time.time()

    return end_time - start_time

if __name__ == "__main__":
    size = 1000
    ops = 5000
    print(f"Benchmarking ThreadSafeCache with size={size}, ops={ops}...")
    duration = benchmark_cache(size, ops)
    print(f"Duration: {duration:.4f} seconds")
    print(f"Ops/sec: {ops / duration:.2f}")
