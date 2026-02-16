#!/usr/bin/env python3
"""
Part B test: DLQ / poison message handling.
Publish a malformed message to order_placed queue; it should be nack'd and land in order_placed_dlq.

Usage: docker compose run --rm tests python run_dlq_demo.py
Then check RabbitMQ Management UI (http://localhost:15672) queue 'order_placed_dlq' for 1 message,
or run: docker compose exec rabbitmq rabbitmqctl list_queues name messages
"""
import os
import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
EXCHANGE_ORDER_EVENTS = "order_events"
ROUTING_KEY_ORDER_PLACED = "order.placed"
QUEUE_ORDER_PLACED = "order_placed"


def main():
    params = pika.URLParameters(RABBITMQ_URL)
    conn = pika.BlockingConnection(params)
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE_ORDER_EVENTS, exchange_type="direct", durable=True)
    ch.queue_declare(queue=QUEUE_ORDER_PLACED, durable=True)
    ch.queue_bind(queue=QUEUE_ORDER_PLACED, exchange=EXCHANGE_ORDER_EVENTS, routing_key=ROUTING_KEY_ORDER_PLACED)

    # Poison: invalid JSON
    ch.basic_publish(
        exchange=EXCHANGE_ORDER_EVENTS,
        routing_key=ROUTING_KEY_ORDER_PLACED,
        body=b"not valid json {",
        properties=pika.BasicProperties(delivery_mode=2),
    )
    print("Published poison message (invalid JSON) to order_placed.")
    conn.close()
    print("Check queue 'order_placed_dlq' in RabbitMQ Management (http://localhost:15672) for the message.")


if __name__ == "__main__":
    main()
