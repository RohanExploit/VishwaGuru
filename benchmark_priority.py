import time
import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.priority_engine import priority_engine
from backend.adaptive_weights import adaptive_weights

def benchmark(iterations=1000):
    text = "Immediate help needed! There is a fire near the hospital and a child is trapped."

    # Warm up
    priority_engine.analyze(text)

    start = time.time()
    for _ in range(iterations):
        priority_engine.analyze(text)
    end = time.time()

    print(f"Iterations: {iterations}")
    print(f"Total time: {end - start:.4f} seconds")
    print(f"Average time per analysis: {(end - start) / iterations * 1000:.4f} ms")

if __name__ == "__main__":
    print("Running benchmark...")
    benchmark()
