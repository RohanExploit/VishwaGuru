import time
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.priority_engine import priority_engine

def benchmark():
    test_cases = [
        ("There is a massive fire in the building near the school!", ["fire", "smoke"]),
        ("Pothole on the main road is causing accidents.", ["road", "pothole"]),
        ("Street light is flickering and it's very dark here.", None),
        ("Garbage is piling up near the park entrance, it smells bad.", ["garbage"]),
        ("Water leak from a burst pipe is flooding the street.", ["water"]),
        ("A stray dog bit a child near the playground.", ["dog"]),
        ("Construction debris is blocking the sidewalk.", ["debris"]),
        ("Illegal parking is blocking the ambulance entrance.", ["car", "ambulance"]),
        ("Graffiti on the historical monument.", None),
        ("Broken manhole cover on the pavement.", ["manhole"]),
    ]

    print("Starting warmup...")
    for _ in range(100):
        for text, labels in test_cases:
            priority_engine.analyze(text, labels)

    print("Starting benchmark (1000 iterations)...")
    start_time = time.time()
    iterations = 1000
    for _ in range(iterations):
        for text, labels in test_cases:
            priority_engine.analyze(text, labels)
    end_time = time.time()

    total_time = end_time - start_time
    total_analyses = iterations * len(test_cases)
    avg_time = (total_time / total_analyses) * 1000 # in ms

    print(f"Total analyses: {total_analyses}")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per analysis: {avg_time:.4f} ms")

if __name__ == "__main__":
    benchmark()
