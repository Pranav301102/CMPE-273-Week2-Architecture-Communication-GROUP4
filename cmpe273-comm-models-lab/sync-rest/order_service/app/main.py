import os
import time
import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

INVENTORY_URL = os.getenv("INVENTORY_URL", "http://inventory_service:8000")
NOTIFICATION_URL = os.getenv("NOTIFICATION_URL", "http://notification_service:8000")
INVENTORY_TIMEOUT_SEC = float(os.getenv("INVENTORY_TIMEOUT_SEC", "1.0"))

app = FastAPI(title="OrderService (Sync REST)")

class OrderIn(BaseModel):
    order_id: str
    item_id: str
    qty: int
    user_id: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/order")
def place_order(order: OrderIn):
    start = time.perf_counter()

    # 1) Reserve inventory (sync)
    try:
        r = requests.post(
            f"{INVENTORY_URL}/reserve",
            json={"order_id": order.order_id, "item_id": order.item_id, "qty": order.qty},
            timeout=INVENTORY_TIMEOUT_SEC,
        )
    except requests.Timeout:
        raise HTTPException(status_code=503, detail="Inventory timeout")
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Inventory unreachable: {e}")

    if r.status_code != 200:
        raise HTTPException(status_code=409, detail=f"Inventory rejected: {r.text}")

    # 2) Send notification (sync)
    try:
        n = requests.post(
            f"{NOTIFICATION_URL}/send",
            json={"order_id": order.order_id, "user_id": order.user_id, "message": "Order confirmed"},
            timeout=1.0,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Notification error: {e}")

    if n.status_code != 200:
        raise HTTPException(status_code=503, detail=f"Notification failed: {n.text}")

    latency_ms = (time.perf_counter() - start) * 1000
    return {"status": "accepted", "order_id": order.order_id, "latency_ms": round(latency_ms, 2)}