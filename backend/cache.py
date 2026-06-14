import time
import logging
import threading
import collections
from typing import Any, Optional

logger = logging.getLogger(__name__)

class ThreadSafeCache:
    """
    Thread-safe cache implementation with TTL and LRU eviction.
    Uses collections.OrderedDict for O(1) LRU operations.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 100):
        self._cache = collections.OrderedDict()  # Maps key -> (value, timestamp)
        self._ttl = ttl
        self._max_size = max_size
        self._lock = threading.RLock()
        
    def get(self, key: str = "default") -> Optional[Any]:
        """
        Thread-safe get operation.
        Removes item if expired. Updates LRU position if valid.
        """
        with self._lock:
            if key not in self._cache:
                return None

            value, timestamp = self._cache[key]
            
            # Check expiration
            if time.time() - timestamp > self._ttl:
                del self._cache[key]
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            return value
    
    def set(self, data: Any, key: str = "default") -> None:
        """
        Thread-safe set operation.
        Evicts least recently used item if cache is full.
        """
        with self._lock:
            current_time = time.time()
            expiry = current_time + self._ttl
            
            # If updating existing key, move to end
            if key in self._cache:
                self._cache.move_to_end(key)
            
            self._cache[key] = (data, current_time)
            
            # Check size and evict if needed
            # We first try to remove expired items if we are over limit
            if len(self._cache) > self._max_size:
                self._cleanup_expired()

                # If still over limit, evict LRU (first item)
                while len(self._cache) > self._max_size:
                    self._cache.popitem(last=False)
                    logger.debug(f"Evicted LRU cache entry due to size limit")

    def invalidate(self, key: str = "default") -> None:
        """
        Thread-safe invalidation of specific key.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache invalidated: key={key}")
    
    def clear(self) -> None:
        """
        Thread-safe clear all cache entries.
        """
        with self._lock:
            self._cache.clear()
            logger.debug("Cache cleared")
    
    def get_stats(self) -> dict:
        """
        Get cache statistics for monitoring.
        """
        with self._lock:
            current_time = time.time()
            # Count expired items without removing them (read-only scan)
            expired_count = sum(
                1 for _, timestamp in self._cache.values()
                if current_time - timestamp >= self._ttl
            )
            
            return {
                "total_entries": len(self._cache),
                "expired_entries": expired_count,
                "max_size": self._max_size,
                "ttl_seconds": self._ttl
            }

    def _cleanup_expired(self) -> None:
        """
        Internal method to clean up expired entries.
        Must be called within lock context.
        """
        current_time = time.time()
        # Create a list of keys to remove to avoid modifying dict while iterating
        keys_to_remove = [
            k for k, (_, timestamp) in self._cache.items()
            if current_time - timestamp >= self._ttl
        ]
        
        for k in keys_to_remove:
            del self._cache[k]
        
        if keys_to_remove:
            logger.debug(f"Cleaned up {len(keys_to_remove)} expired cache entries")

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
