import os
import json
import logging
from kafka import KafkaConsumer
from datetime import datetime
from collections import defaultdict
import threading
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')

# Metrics storage
metrics = {
    'total_orders': 0,
    'successful_orders': 0,
    'failed_orders': 0,
    'orders_by_minute': defaultdict(int),
    'last_report_time': None
}

metrics_lock = threading.Lock()

# Initialize Kafka Consumer
consumer = KafkaConsumer(
    'inventory-events',
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    group_id='analytics-service',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    max_poll_records=100
)

def generate_report():
    """Generate a metrics report"""
    with metrics_lock:
        total = metrics['successful_orders'] + metrics['failed_orders']
        failure_rate = 0
        if total > 0:
            failure_rate = (metrics['failed_orders'] / total) * 100
        
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'total_orders': total,
            'successful_orders': metrics['successful_orders'],
            'failed_orders': metrics['failed_orders'],
            'failure_rate': f"{failure_rate:.2f}%",
            'orders_by_minute': dict(metrics['orders_by_minute'])
        }
        return report

def print_report():
    """Print the current metrics report"""
    report = generate_report()
    print("\n" + "="*60)
    print("METRICS REPORT")
    print("="*60)
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Orders: {report['total_orders']}")
    print(f"Successful: {report['successful_orders']}")
    print(f"Failed: {report['failed_orders']}")
    print(f"Failure Rate: {report['failure_rate']}")
    print(f"Orders by Minute: {report['orders_by_minute']}")
    print("="*60 + "\n")

def process_events():
    logger.info("Analytics Consumer started")
    last_report = time.time()
    
    try:
        for message in consumer:
            try:
                inventory_event = message.value
                
                with metrics_lock:
                    metrics['total_orders'] += 1
                    
                    if inventory_event['status'] == 'InventoryReserved':
                        metrics['successful_orders'] += 1
                    else:
                        metrics['failed_orders'] += 1
                    
                    # Record orders by minute
                    timestamp = datetime.fromisoformat(inventory_event['timestamp'])
                    minute_key = timestamp.strftime('%Y-%m-%d %H:%M')
                    metrics['orders_by_minute'][minute_key] += 1
                
                logger.info(f"Processed event for order {inventory_event['order_id']}")
                
                # Print report every 30 seconds
                current_time = time.time()
                if current_time - last_report >= 30:
                    print_report()
                    last_report = current_time
                    
            except Exception as e:
                logger.error(f"Error processing message: {e}")
        
    except KeyboardInterrupt:
        logger.info("Analytics Consumer stopped")
    finally:
        consumer.close()
        print_report()

if __name__ == '__main__':
    process_events()
