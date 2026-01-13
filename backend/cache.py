import time
import logging

logger = logging.getLogger(__name__)

class SimpleCache:
    def __init__(self, ttl: int = 60):
        self.data = None
        self.timestamp = 0
        self.ttl = ttl

    def get(self):
        current_time = time.time()
        if self.data and (current_time - self.timestamp < self.ttl):
            return self.data
        return None

    def set(self, data):
        self.data = data
        self.timestamp = time.time()

    def invalidate(self):
        self.data = None
        self.timestamp = 0

# Global instance
recent_issues_cache = SimpleCache(ttl=60)
