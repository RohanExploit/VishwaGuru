import time
import logging
import threading
from typing import Any, Optional
from collections import OrderedDict

logger = logging.getLogger(__name__)

class ThreadSafeCache:
    """
    Thread-safe cache implementation with TTL and memory management.
    Fixes race conditions and implements proper cache expiration.
    Uses OrderedDict for O(1) LRU eviction.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 100):
        self._data = OrderedDict()  # Key -> (value, timestamp)
        self._ttl = ttl  # Time to live in seconds
        self._max_size = max_size  # Maximum number of cache entries
        self._lock = threading.RLock()  # Reentrant lock for thread safety
        
    def get(self, key: str = "default") -> Optional[Any]:
        """
        Thread-safe get operation with automatic cleanup.
        O(1) complexity.
        """
        with self._lock:
            current_time = time.time()
            
            # Check if key exists
            if key in self._data:
                value, timestamp = self._data[key]

                # Check expiration
                if current_time - timestamp < self._ttl:
                    # Move to end (MRU)
                    self._data.move_to_end(key)
                    # print(f"DEBUG: get({key}) hit. Order: {list(self._data.keys())}")
                    return value
                else:
                    # Expired entry - remove it
                    del self._data[key]
                    # print(f"DEBUG: get({key}) expired. Order: {list(self._data.keys())}")
            
            # print(f"DEBUG: get({key}) miss. Order: {list(self._data.keys())}")
            return None
    
    def set(self, data: Any, key: str = "default") -> None:
        """
        Thread-safe set operation with memory management.
        O(1) complexity.
        """
        with self._lock:
            current_time = time.time()
            expiry = current_time + self._ttl
            
            # If key already exists, update and move to end
            if key in self._data:
                self._data.move_to_end(key)
            
            # Set new data
            self._data[key] = (data, current_time)
            
            # Evict if over capacity
            if len(self._data) > self._max_size:
                # Remove first item (LRU)
                popped = self._data.popitem(last=False)
                # print(f"DEBUG: Evicted {popped[0]}. Order: {list(self._data.keys())}")

            # print(f"DEBUG: set({key}). Order: {list(self._data.keys())}")
            
    
    def invalidate(self, key: str = "default") -> None:
        """
        Thread-safe invalidation of specific key.
        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                logger.debug(f"Cache invalidated: key={key}")
    
    def clear(self) -> None:
        """
        Thread-safe clear all cache entries.
        """
        with self._lock:
            self._data.clear()
            logger.debug("Cache cleared")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics for monitoring.
        """
        with self._lock:
            current_time = time.time()
            expired_count = sum(
                1 for _, timestamp in self._data.values()
                if current_time - timestamp >= self._ttl
            )
            
            return {
                "total_entries": len(self._data),
                "expired_entries": expired_count,
                "max_size": self._max_size,
                "ttl_seconds": self._ttl
            }

class SimpleCache:
    """
    Backward compatibility wrapper for existing code.
    """
    
    def __init__(self, ttl: int = 60):
        self._cache = ThreadSafeCache(ttl=ttl, max_size=50)
    
    def get(self):
        return self._cache.get("default")
    
    def set(self, data):
        self._cache.set(data, "default")
    
    def invalidate(self):
        self._cache.invalidate("default")

# Global instances with improved configuration
recent_issues_cache = ThreadSafeCache(ttl=300, max_size=20)  # 5 minutes TTL, max 20 entries
nearby_issues_cache = ThreadSafeCache(ttl=60, max_size=100)  # 1 minute TTL, max 100 entries
user_upload_cache = ThreadSafeCache(ttl=3600, max_size=1000)  # 1 hour TTL for upload limits
