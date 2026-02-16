#!/usr/bin/env python3
"""
Part B test: Backlog and recovery.
Usage: docker compose run --rm tests python run_backlog_recovery.py

Instructions for full demo:
1. Start stack: docker compose up -d
2. In one terminal, run this script (it will POST orders every second for 90s).
3. After ~10 orders, kill inventory: docker compose stop inventory_service
4. Let orders accumulate for 60s (script keeps posting).
5. Restart inventory: docker compose start inventory_service
6. Watch logs: docker compose logs -f inventory_service
   You should see the backlog drain (all OrderPlaced messages processed).
"""
import os
import time
import uuid
import requests

ORDER_URL = os.getenv("ORDER_URL", "http://order_service:8000")
INTERVAL = 1.0
DURATION = 90


def main():
    print("Posting orders to OrderService every", INTERVAL, "s for", DURATION, "s")
    print("For backlog demo: stop inventory_service for 60s, then start it and watch logs.")
    start = time.monotonic()
    count = 0
    while time.monotonic() - start < DURATION:
        order_id = str(uuid.uuid4())
        try:
            r = requests.post(
                f"{ORDER_URL}/order",
                json={"order_id": order_id, "item_id": "widget", "qty": 1, "user_id": "u1"},
                timeout=5,
            )
            if r.status_code in (202, 200):
                count += 1
                print(f"  [{count}] order_id={order_id[:8]}... -> {r.status_code}")
            else:
                print(f"  order_id={order_id[:8]}... -> {r.status_code} {r.text}")
        except requests.RequestException as e:
            print("  Error:", e)
        time.sleep(INTERVAL)
    print("Done. Total orders posted:", count)


if __name__ == "__main__":
    main()
