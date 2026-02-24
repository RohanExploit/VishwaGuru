import time
import logging
import threading
from typing import Any, Optional
from datetime import datetime, timedelta
from collections import OrderedDict

logger = logging.getLogger(__name__)

class ThreadSafeCache:
    """
    Thread-safe cache implementation with TTL and memory management.
    Optimized: Uses OrderedDict for O(1) LRU eviction.
    """
    
    def __init__(self, ttl: int = 300, max_size: int = 100):
        self._data = OrderedDict() # Stores (data, expiry_timestamp)
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
            
            if key in self._data:
                data, expiry = self._data[key]
                if current_time < expiry:
                    # Move to end (mark as most recently used)
                    self._data.move_to_end(key)
                    return data
                else:
                    # Expired entry - remove it
                    del self._data[key]
            
            return None
    
    def set(self, data: Any, key: str = "default") -> None:
        """
        Thread-safe set operation with memory management.
        O(1) complexity.
        """
        with self._lock:
            current_time = time.time()
            expiry = current_time + self._ttl
            
            if key in self._data:
                # Update existing entry
                self._data[key] = (data, expiry)
                self._data.move_to_end(key)
            else:
                # Add new entry
                if len(self._data) >= self._max_size:
                    # Evict oldest entry (LRU) - O(1)
                    self._data.popitem(last=False)

                self._data[key] = (data, expiry)
            
            logger.debug(f"Cache set: key={key}, size={len(self._data)}")
    
    def invalidate(self, key: str = "default") -> None:
        """
        Thread-safe invalidation of specific key.
        """
        with self._lock:
            self._data.pop(key, None)
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
                1 for data, expiry in self._data.values()
                if current_time >= expiry
            )
            
            return {
                "total_entries": len(self._data),
                "expired_entries": expired_count,
                "max_size": self._max_size,
                "ttl_seconds": self._ttl
            }
    
    def _cleanup_expired(self) -> None:
        """
        Internal method to clean up all expired entries.
        Must be called within lock context.
        """
        current_time = time.time()
        expired_keys = [
            key for key, (data, expiry) in self._data.items()
            if current_time >= expiry
        ]
        
        for key in expired_keys:
            del self._data[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")

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
