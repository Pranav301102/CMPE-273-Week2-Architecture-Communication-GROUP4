import os, time, statistics, requests, uuid

ORDER_URL = os.getenv("ORDER_URL", "http://order_service:8000")
N = 50

def do_orders(n: int):
    latencies = []
    for _ in range(n):
        order_id = str(uuid.uuid4())
        t0 = time.perf_counter()
        r = requests.post(f"{ORDER_URL}/order", json={
            "order_id": order_id,
            "item_id": "burrito",
            "qty": 1,
            "user_id": "u123"
        })
        dt = (time.perf_counter() - t0) * 1000
        latencies.append(dt)
        if r.status_code != 200:
            # still record latency; include failure detail
            pass
    return latencies

def summarize(name, arr):
    return {
        "case": name,
        "n": len(arr),
        "p50_ms": round(statistics.median(arr), 2),
        "p95_ms": round(sorted(arr)[int(0.95*len(arr))-1], 2),
        "avg_ms": round(statistics.mean(arr), 2),
    }

def main():
    base = do_orders(N)
    print("\nLATENCY TABLE (ms)")
    print("case,n,p50,p95,avg")
    s = summarize("baseline", base)
    print(f"{s['case']},{s['n']},{s['p50_ms']},{s['p95_ms']},{s['avg_ms']}")
    print("\nNOTE: Run delay/failure injection by changing Inventory env vars and re-running this container.\n")

if __name__ == "__main__":
    main()