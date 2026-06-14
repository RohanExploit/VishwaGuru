import time
from backend.priority_engine import priority_engine
import cProfile
import pstats
import io

# We create a sample text that does not contain any of the urgency keywords
# but is long enough to simulate a real-world scenario.
sample_text = (
    "There is a small pothole on the corner of 5th and Main. "
    "It has been there for a few days and is causing some inconvenience to the drivers. "
    "Please send someone to look at it when possible. "
    "The road condition is generally poor in this area and needs attention. "
    "We have noticed an increase in traffic recently, which might be contributing to the wear and tear. "
    "No one has been injured, but we would like to avoid any accidents."
) * 10  # Make it reasonably long

def benchmark(iterations=10000):
    start_time = time.perf_counter()
    for _ in range(iterations):
        # We only benchmark _calculate_urgency. We give it a base severity of 10.
        priority_engine._calculate_urgency(sample_text, 10)
    end_time = time.perf_counter()

    total_time = end_time - start_time
    avg_time_ms = (total_time / iterations) * 1000

    print(f"Benchmark: _calculate_urgency")
    print(f"Iterations: {iterations}")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per call: {avg_time_ms:.4f} ms")
    return avg_time_ms

if __name__ == "__main__":
    # Warm up
    priority_engine._calculate_urgency(sample_text, 10)

    print("--- Running Benchmark ---")
    benchmark()

    # Profile to show where time is spent
    print("\n--- Running Profiler ---")
    pr = cProfile.Profile()
    pr.enable()
    for _ in range(20000):
        priority_engine._calculate_urgency(sample_text, 10)
    pr.disable()
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(15)
    print(s.getvalue())
