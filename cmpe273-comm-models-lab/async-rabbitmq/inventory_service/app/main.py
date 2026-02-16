import os
import time
import random
import json
import logging
import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
DELAY_SEC = float(os.getenv("DELAY_SEC", "0"))
FAIL_MODE = os.getenv("FAIL_MODE", "none")
FAIL_PROB = float(os.getenv("FAIL_PROB", "0.0"))

EXCHANGE_ORDER_EVENTS = "order_events"
QUEUE_ORDER_PLACED = "order_placed"
QUEUE_ORDER_PLACED_DLQ = "order_placed_dlq"
EXCHANGE_INVENTORY_EVENTS = "inventory_events"
ROUTING_KEY_RESERVED = "inventory.reserved"
ROUTING_KEY_FAILED = "inventory.failed"
QUEUE_INVENTORY_RESERVED = "inventory_reserved"

# Idempotency: in-memory set of processed order_ids (could use SQLite for persistence)
processed_order_ids = set()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_connection_params():
    return pika.URLParameters(RABBITMQ_URL)


def declare_inventory_artifacts(channel):
    channel.exchange_declare(exchange=EXCHANGE_INVENTORY_EVENTS, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE_INVENTORY_RESERVED, durable=True)
    channel.queue_bind(
        queue=QUEUE_INVENTORY_RESERVED,
        exchange=EXCHANGE_INVENTORY_EVENTS,
        routing_key=ROUTING_KEY_RESERVED,
    )
    channel.queue_declare(queue=QUEUE_ORDER_PLACED_DLQ, durable=True)


def do_reserve(order_id: str, item_id: str, qty: int) -> bool:
    """Simulate reserve. Returns True if reserved, False if failed."""
    if DELAY_SEC > 0:
        time.sleep(DELAY_SEC)
    if FAIL_MODE == "always":
        return False
    if FAIL_MODE == "prob" and random.random() < FAIL_PROB:
        return False
    return True


def on_message(channel, method, properties, body):
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.warning("Poison message (invalid JSON): %s", e)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        # Publish to DLQ
        try:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_ORDER_PLACED_DLQ,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception:
            pass
        return

    order_id = payload.get("order_id")
    item_id = payload.get("item_id")
    qty = payload.get("qty")
    user_id = payload.get("user_id")

    if not order_id:
        logger.warning("Poison message (missing order_id)")
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        try:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_ORDER_PLACED_DLQ,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception:
            pass
        return

    # Idempotency: skip if already processed
    if order_id in processed_order_ids:
        logger.info("Idempotent skip for order_id=%s", order_id)
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    try:
        success = do_reserve(order_id, item_id or "", qty or 0)
    except Exception as e:
        logger.exception("Reserve failed: %s", e)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        try:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_ORDER_PLACED_DLQ,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception:
            pass
        return

    processed_order_ids.add(order_id)

    out_payload = {"order_id": order_id, "status": "reserved" if success else "failed", "user_id": user_id}
    routing = ROUTING_KEY_RESERVED if success else ROUTING_KEY_FAILED
    channel.basic_publish(
        exchange=EXCHANGE_INVENTORY_EVENTS,
        routing_key=routing,
        body=json.dumps(out_payload),
        properties=pika.BasicProperties(delivery_mode=2),
    )
    channel.basic_ack(delivery_tag=method.delivery_tag)
    logger.info("Processed order_id=%s -> %s", order_id, out_payload["status"])


def run():
    while True:
        try:
            conn = pika.BlockingConnection(get_connection_params())
            channel = conn.channel()
            channel.exchange_declare(exchange=EXCHANGE_ORDER_EVENTS, exchange_type="direct", durable=True)
            channel.queue_declare(queue=QUEUE_ORDER_PLACED, durable=True)
            declare_inventory_artifacts(channel)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_ORDER_PLACED, on_message_callback=on_message)
            logger.info("InventoryService consuming from %s", QUEUE_ORDER_PLACED)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logger.warning("RabbitMQ connection failed, retrying: %s", e)
            time.sleep(5)
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.exception("Error: %s", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
