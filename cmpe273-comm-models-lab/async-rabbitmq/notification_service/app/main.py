import os
import time
import json
import logging
import pika

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
EXCHANGE_INVENTORY_EVENTS = "inventory_events"
QUEUE_INVENTORY_RESERVED = "inventory_reserved"
QUEUE_INVENTORY_RESERVED_DLQ = "inventory_reserved_dlq"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_connection_params():
    return pika.URLParameters(RABBITMQ_URL)


def on_message(channel, method, properties, body):
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as e:
        logger.warning("Poison message (invalid JSON): %s", e)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        try:
            channel.basic_publish(
                exchange="",
                routing_key=QUEUE_INVENTORY_RESERVED_DLQ,
                body=body,
                properties=pika.BasicProperties(delivery_mode=2),
            )
        except Exception:
            pass
        return

    order_id = payload.get("order_id")
    status = payload.get("status")
    user_id = payload.get("user_id")

    if status != "reserved":
        channel.basic_ack(delivery_tag=method.delivery_tag)
        return

    # Stub: send confirmation (in real system: email/SMS/push)
    logger.info("Send confirmation for order_id=%s user_id=%s", order_id, user_id)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def run():
    while True:
        try:
            conn = pika.BlockingConnection(get_connection_params())
            channel = conn.channel()
            channel.exchange_declare(exchange=EXCHANGE_INVENTORY_EVENTS, exchange_type="direct", durable=True)
            channel.queue_declare(queue=QUEUE_INVENTORY_RESERVED, durable=True)
            channel.queue_bind(
                queue=QUEUE_INVENTORY_RESERVED,
                exchange=EXCHANGE_INVENTORY_EVENTS,
                routing_key="inventory.reserved",
            )
            channel.queue_declare(queue=QUEUE_INVENTORY_RESERVED_DLQ, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=QUEUE_INVENTORY_RESERVED, on_message_callback=on_message)
            logger.info("NotificationService consuming from %s", QUEUE_INVENTORY_RESERVED)
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
