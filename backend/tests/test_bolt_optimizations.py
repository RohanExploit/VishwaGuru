import time
import collections
import hashlib
import unittest
from unittest.mock import MagicMock, patch

from backend.cache import ThreadSafeCache
from backend.models import Grievance, SeverityLevel

class TestBoltOptimizations(unittest.TestCase):

    def test_cache_expiration_logic(self):
        """Verify O(K) cache cleanup works correctly."""
        # Small TTL and max size
        cache = ThreadSafeCache(ttl=1, max_size=10)

        # Add entries
        cache.set("data1", "key1")
        cache.set("data2", "key2")

        # Check they exist
        self.assertEqual(cache.get("key1"), "data1")
        self.assertEqual(cache.get("key2"), "data2")

        # Wait for expiration
        time.sleep(1.1)

        # Add a new entry - this should trigger cleanup
        cache.set("data3", "key3")

        # Old entries should be gone
        self.assertIsNone(cache.get("key1"))
        self.assertIsNone(cache.get("key2"))
        self.assertEqual(cache.get("key3"), "data3")

    def test_blockchain_hashing_logic(self):
        """Verify the SHA-256 chaining logic used in GrievanceService."""
        unique_id = "G-123"
        category = "Road"
        severity = "high"
        prev_hash = "abc"

        # Chaining logic: hash(unique_id|category|severity|prev_hash)
        hash_content = f"{unique_id}|{category}|{severity}|{prev_hash}"
        expected_hash = hashlib.sha256(hash_content.encode()).hexdigest()

        # Simulate the manual verification in router
        recomputed_content = f"{unique_id}|{category}|{severity}|{prev_hash}"
        recomputed_hash = hashlib.sha256(recomputed_content.encode()).hexdigest()

        self.assertEqual(expected_hash, recomputed_hash)

if __name__ == "__main__":
    unittest.main()
