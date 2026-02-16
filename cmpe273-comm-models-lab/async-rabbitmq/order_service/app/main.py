import os
import json
import sqlite3
import pika
from contextlib import contextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
ORDER_STORE_PATH = os.getenv("ORDER_STORE_PATH", "./orders.db")

# Exchange and routing
EXCHANGE_ORDER_EVENTS = "order_events"
ROUTING_KEY_ORDER_PLACED = "order.placed"
QUEUE_ORDER_PLACED = "order_placed"

app = FastAPI(title="OrderService (Async RabbitMQ)")


class OrderIn(BaseModel):
    order_id: str
    item_id: str
    qty: int
    user_id: str


def get_connection_params():
    return pika.URLParameters(RABBITMQ_URL)


def ensure_exchange_and_queue(channel):
    channel.exchange_declare(exchange=EXCHANGE_ORDER_EVENTS, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE_ORDER_PLACED, durable=True)
    channel.queue_bind(queue=QUEUE_ORDER_PLACED, exchange=EXCHANGE_ORDER_EVENTS, routing_key=ROUTING_KEY_ORDER_PLACED)


def publish_order_placed(payload: dict) -> None:
    conn = pika.BlockingConnection(get_connection_params())
    try:
        ch = conn.channel()
        ensure_exchange_and_queue(ch)
        ch.basic_publish(
            exchange=EXCHANGE_ORDER_EVENTS,
            routing_key=ROUTING_KEY_ORDER_PLACED,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        conn.close()


@contextmanager
def get_db():
    conn = sqlite3.connect(ORDER_STORE_PATH)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                item_id TEXT NOT NULL,
                qty INTEGER NOT NULL,
                user_id TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        yield conn
    finally:
        conn.close()


@app.on_event("startup")
def startup():
    with get_db() as db:
        pass  # ensure table exists
    # Declare exchange/queue so they exist before consumers start (retry until RabbitMQ is ready)
    for attempt in range(30):
        try:
            conn = pika.BlockingConnection(get_connection_params())
            ch = conn.channel()
            ensure_exchange_and_queue(ch)
            conn.close()
            return
        except Exception:
            import time
            time.sleep(2)
    raise RuntimeError("RabbitMQ not available after 30 attempts")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/order")
def place_order(order: OrderIn):
    import time
    created_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with get_db() as db:
            db.execute(
                "INSERT INTO orders (order_id, item_id, qty, user_id, created_at) VALUES (?, ?, ?, ?, ?)",
                (order.order_id, order.item_id, order.qty, order.user_id, created_at),
            )
            db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Order ID already exists")

    payload = {
        "order_id": order.order_id,
        "item_id": order.item_id,
        "qty": order.qty,
        "user_id": order.user_id,
    }
    publish_order_placed(payload)

    return JSONResponse(content={"status": "accepted", "order_id": order.order_id}, status_code=202)
