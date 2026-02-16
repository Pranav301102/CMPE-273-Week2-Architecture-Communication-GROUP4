import os
import json
import logging
from flask import Flask, request, jsonify
from kafka import KafkaProducer
from datetime import datetime
import uuid

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')

# Initialize Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    retries=3
)

@app.route('/order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        order_id = str(uuid.uuid4())
        order_event = {
            'id': order_id,
            'user_id': data.get('user_id'),
            'item': data.get('item'),
            'quantity': data.get('quantity', 1),
            'timestamp': datetime.utcnow().isoformat(),
            'status': 'OrderPlaced'
        }
        
        # Publish to Kafka
        future = producer.send('order-events', value=order_event)
        record_metadata = future.get(timeout=5)
        
        logger.info(f"Order placed: {order_id}")
        return jsonify({
            'order_id': order_id,
            'status': 'OrderPlaced'
        }), 202
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
