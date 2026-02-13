import os
import time
import random
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DELAY_SEC = float(os.getenv("DELAY_SEC", "0"))
FAIL_MODE = os.getenv("FAIL_MODE", "none")  # none|always|prob
FAIL_PROB = float(os.getenv("FAIL_PROB", "0.0"))

app = FastAPI(title="InventoryService (Sync REST)")

class ReserveIn(BaseModel):
    order_id: str
    item_id: str
    qty: int

@app.get("/health")
def health():
    return {"status": "ok", "delay_sec": DELAY_SEC, "fail_mode": FAIL_MODE, "fail_prob": FAIL_PROB}

@app.post("/reserve")
def reserve(req: ReserveIn):
    if DELAY_SEC > 0:
        time.sleep(DELAY_SEC)

    if FAIL_MODE == "always":
        raise HTTPException(status_code=500, detail="Injected failure (always)")
    if FAIL_MODE == "prob" and random.random() < FAIL_PROB:
        raise HTTPException(status_code=500, detail="Injected failure (prob)")

    # Minimal reserve logic (accept always)
    return {"status": "reserved", "order_id": req.order_id}