import time
import json
import statistics
import sys
import os

# Add root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.api_logic import process_request

def benchmark():
    payload = {
        "lat": 13.3409,
        "lon": 74.7421,
        "crop": "Paddy",
        "sowing_date": "2026-06-15"
    }

    # Warmup
    for _ in range(100):
        process_request(payload)

    times = []
    print("🚀 Benchmarking 10,000 requests...")
    
    start_global = time.time()
    for _ in range(10000):
        t0 = time.perf_counter()
        process_request(payload)
        t1 = time.perf_counter()
        times.append((t1 - t0) * 1000) # ms
    end_global = time.time()

    avg = statistics.mean(times)
    median = statistics.median(times)
    p99 = statistics.quantiles(times, n=100)[98]
    
    print(f"✅ Total Time: {end_global - start_global:.2f}s")
    print(f"⚡ Avg Latency: {avg:.4f} ms")
    print(f"⚡ P50 Latency: {median:.4f} ms")
    print(f"⚡ P99 Latency: {p99:.4f} ms")
    
    if avg < 1.0:
        print("RESULT: 🟢 EXTREMELY FAST (<1ms)")
    elif avg < 10.0:
        print("RESULT: 🟢 FAST (<10ms)")
    else:
        print("RESULT: 🔴 SLOW (>10ms)")

if __name__ == "__main__":
    benchmark()
