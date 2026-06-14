import os
import sys
import unittest

# Ensure backend is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.rag_service import CivicRAG

class TestCivicRAG(unittest.TestCase):
    def setUp(self):
        # Point to the data file we created
        # Assuming run from root: backend/data/civic_policies.json
        # If run from backend/tests/: ../../backend/data/civic_policies.json
        # The service tries to find it.
        self.rag = CivicRAG()

    def test_pothole_retrieval(self):
        query = "There is a deep pothole on the road causing traffic."
        result = self.rag.retrieve(query)
        self.assertIsNotNone(result)
        self.assertIn("Pothole Repair SLA", result)
        print(f"\nQuery: {query}\nResult: {result}")

    def test_garbage_retrieval(self):
        query = "Trash and garbage are piling up in the corner."
        result = self.rag.retrieve(query)
        self.assertIsNotNone(result)
        self.assertIn("Garbage Collection Rules", result)
        print(f"\nQuery: {query}\nResult: {result}")

    def test_noise_retrieval(self):
        query = "Loud music and noise from the neighbor all night."
        result = self.rag.retrieve(query)
        self.assertIsNotNone(result)
        self.assertIn("Noise Pollution Limits", result)
        print(f"\nQuery: {query}\nResult: {result}")

    def test_no_match(self):
        query = "xzy qwe asd 123"
        result = self.rag.retrieve(query)
        self.assertIsNone(result)

if __name__ == "__main__":
    unittest.main()
