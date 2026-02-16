#!/usr/bin/env python3
"""
Part B test: Idempotency.
Publish the same OrderPlaced message twice (same order_id); inventory should
process it only once (no double reserve). Check logs for "Idempotent skip" on second delivery.

Usage: docker compose run --rm tests python run_idempotency_check.py
"""
import os
import json
import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE_ORDER_EVENTS = "order_events"
ROUTING_KEY_ORDER_PLACED = "order.placed"
QUEUE_ORDER_PLACED = "order_placed"

# Use a fixed order_id so we can re-publish the same message
ORDER_ID = "idempotency-test-order-1"
PAYLOAD = {"order_id": ORDER_ID, "item_id": "item1", "qty": 2, "user_id": "u99"}


def main():
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE_ORDER_EVENTS, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE_ORDER_PLACED, durable=True)
    ch.queue_bind(queue=QUEUE_ORDER_PLACED, exchange=EXCHANGE_ORDER_EVENTS, routing_key=ROUTING_KEY_ORDER_PLACED)

    body = json.dumps(PAYLOAD)
    ch.basic_publish(
        exchange=EXCHANGE_ORDER_EVENTS,
        routing_key=ROUTING_KEY_ORDER_PLACED,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print("Published OrderPlaced #1 for order_id=", ORDER_ID)
    ch.basic_publish(
        exchange=EXCHANGE_ORDER_EVENTS,
        routing_key=ROUTING_KEY_ORDER_PLACED,
        body=body,
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print("Published OrderPlaced #2 (same order_id). Check inventory_service logs for 'Idempotent skip' on second.")
    conn.close()
    print("Done. Inventory should have processed once and skipped the duplicate.")


if __name__ == "__main__":
    main()
