import time
import collections


def run_bench():
    N = 1000
    ops = 10000
    timestamps = {f"key{i}": time.time() for i in range(N)}
    current_time = time.time()
    ttl = 300

    start = time.time()
    for _ in range(ops):
        expired_keys = [
            key
            for key, timestamp in timestamps.items()
            if current_time - timestamp >= ttl
        ]
    print(f"Current O(N) cleanup time for {ops} ops: {time.time() - start:.4f}s")

    # Optimized version
    timestamps_od = collections.OrderedDict(timestamps)
    start = time.time()
    for _ in range(ops):
        # Simulated optimized cleanup
        # In real code we use next(iter(self._timestamps.items()))
        for key, ts in timestamps_od.items():
            if current_time - ts >= ttl:
                pass
            else:
                break
    print(
        f"Optimized O(K) cleanup time (K=0) for {ops} ops: {time.time() - start:.4f}s"
    )


if __name__ == "__main__":
    run_bench()
