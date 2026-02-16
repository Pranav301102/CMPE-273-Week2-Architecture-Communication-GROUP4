import os
import json
import logging
import random
from kafka import KafkaConsumer, KafkaProducer
from datetime import datetime
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')

# Simulated inventory
inventory = {
    'pizza': 100,
    'burger': 100,
    'salad': 100,
    'sandwich': 100,
}

inventory_lock = threading.Lock()

# Initialize Kafka Consumer and Producer
consumer = KafkaConsumer(
    'order-events',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id='inventory-service',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    max_poll_records=10
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    retries=3
)

def reserve_item(item, quantity):
    with inventory_lock:
        if item in inventory and inventory[item] >= quantity:
            inventory[item] -= quantity
            return True, None
        else:
            return False, f"Item {item} not available (available: {inventory.get(item, 0)})"

def process_events():
    logger.info("Inventory Consumer started")
    try:
        for message in consumer:
            try:
                order_event = message.value
                logger.info(f"Processing order: {order_event['id']}")
                
                # Simulate processing delay (configurable for throttling tests)
                delay = float(os.getenv('PROCESSING_DELAY', '0'))
                if delay > 0:
                    time.sleep(delay)
                
                item = order_event.get('item', 'unknown')
                quantity = order_event.get('quantity', 1)
                
                # Try to reserve
                success, error = reserve_item(item, quantity)
                
                if success:
                    status = 'InventoryReserved'
                    logger.info(f"Order {order_event['id']} - Inventory reserved for {quantity} {item}")
                else:
                    status = 'InventoryFailed'
                    logger.warning(f"Order {order_event['id']} - {error}")
                
                # Emit inventory event
                inventory_event = {
                    'order_id': order_event['id'],
                    'user_id': order_event.get('user_id'),
                    'item': item,
                    'quantity': quantity,
                    'status': status,
                    'timestamp': datetime.utcnow().isoformat(),
                    'error': error
                }
                
                producer.send('inventory-events', value=inventory_event)
                
            except Exception as e:
                logger.error(f"Error processing message: {e}")
                
    except KeyboardInterrupt:
        logger.info("Inventory Consumer stopped")
    finally:
        consumer.close()
        producer.close()

if __name__ == '__main__':
    process_events()
