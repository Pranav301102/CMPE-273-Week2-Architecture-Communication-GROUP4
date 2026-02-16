# Part C: Streaming with Kafka

This module implements the campus food ordering workflow using Kafka for event streaming. The architecture includes a producer that generates order events and multiple consumers that process them.

## Architecture

```
┌─────────────────┐
│ Producer Order  │  (HTTP POST /order)
│ (Flask API)     │──→ order-events (Kafka Topic)
└─────────────────┘
                           │
                ┌──────────┼──────────┐
                ↓                     ↓
        ┌──────────────┐      ┌──────────────┐
        │  Inventory   │      │  Analytics   │
        │  Consumer    │      │  Consumer    │
        │ (Processes)  │      │ (Computes    │
        └──────────────┘      │  Metrics)    │
                │             └──────────────┘
                ↓
        inventory-events (Kafka Topic)
```

## Components

### 1. Producer Order Service
- **Port**: 5001
- **Endpoint**: `POST /order`
- **Functionality**: 
  - Accepts order requests via REST API
  - Publishes `OrderPlaced` events to `order-events` topic
  - Request format:
    ```json
    {
      "user_id": "user_123",
      "item": "pizza",
      "quantity": 1
    }
    ```

### 2. Inventory Consumer Service
- **Port**: 5002
- **Functionality**:
  - Consumes `OrderPlaced` events from `order-events` topic
  - Reserves items from simulated inventory
  - Emits `InventoryReserved` or `InventoryFailed` events to `inventory-events` topic
  - Supports `PROCESSING_DELAY` for throttling tests

### 3. Analytics Consumer Service
- **Port**: 5003
- **Functionality**:
  - Consumes `InventoryEvents` from `inventory-events` topic
  - Computes metrics:
    - Total orders processed
    - Success/failure counts
    - Failure rate percentage
    - Orders per minute
  - Prints reports every 30 seconds
  - Supports stream replay

## Building and Running

### Build Images
```bash
cd cmpe273-comm-models-lab/streaming-kafka
docker-compose build
```

### Start Services
```bash
docker-compose up -d
```

Services startup order:
1. Zookeeper (port 2181)
2. Kafka (ports 9092, 29092)
3. Producer Order, Inventory Consumer, Analytics Consumer

### Verify Services
```bash
# Check if Kafka is ready
docker logs kafka

# Check producer health
curl http://localhost:5001/health

# Check container logs
docker logs producer_order
docker logs inventory_consumer
docker logs analytics_consumer
```

## Running Tests

### Option 1: Run Tests in Container
```bash
docker-compose run --rm tests
```

### Option 2: Run Tests Locally
```bash
cd tests
pip install -r requirements.txt
python run_tests.py
```

### Test Configuration
Set environment variables to customize test behavior:
```bash
# Producer URL (if testing externally)
export PRODUCER_URL=http://localhost:5001

# Kafka bootstrap servers
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

## Tests Included

### 1. Baseline Latency Test
- Produces 100 requests
- Measures end-to-end latency for order creation
- Reports average, min, max latency

### 2. 10K Events Test
- Produces 10,000 order events
- Measures throughput (events/second)
- Validates system handles high volume

### 3. Consumer Lag Measurement
- Measures lag in inventory consumer queue
- Demonstrates how queue depth grows under load

### 4. Replay Test
- Resets consumer offset to beginning
- Re-consumes events and verifies metrics consistency
- Demonstrates idempotency of metrics calculation

## Key Features

### Event-Driven Architecture
- Decoupled services communicate via Kafka topics
- Order producer and consumers operate independently
- No direct HTTP calls between services

### Replica Tolerance
- Multiple consumer groups can independently process same events
- Offset management enables replay and recovery

### Scalability
- Event streaming handles high throughput
- Consumers can be scaled horizontally
- Topic partitioning supports parallel processing

### Ordering Semantics
- Single topic partition ensures order preservation
- Consumer group offset tracking enables recovery

## Expected Test Results

### Baseline Latency
- Average latency: 5-10ms (API call overhead)
- Max latency: 50-100ms (network jitter)

### 10K Events Throughput
- Throughput: 500+ events/second
- Processing time: < 30 seconds

### Consumer Lag
- Demonstrates lag increases under load
- Shows lag drains as consumer catches up

### Replay Metrics
- Metrics should be identical before and after replay
- Validates idempotent processing

## Failure Scenarios

### Throttled Consumer
To test consumer lag under throttling:
```bash
docker-compose exec inventory_consumer bash
# Set environment variable before restart
export PROCESSING_DELAY=1  # 1 second delay per message

docker-compose restart inventory_consumer
```

### Consumer Shutdown and Recovery
```bash
# Stop consumer
docker-compose stop inventory_consumer

# Publish events (will queue in Kafka)
# Then restart consumer
docker-compose start inventory_consumer

# Consumer will catch up from its committed offset
```

### Kafka Shutdown
```bash
docker-compose stop kafka

# Services will retry connection
# Events will be queued

docker-compose start kafka
# Services reconnect and resume
```

## Monitoring

### View Kafka Topics
```bash
docker-compose exec kafka kafka-topics --bootstrap-server kafka:29092 --list

docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic order-events \
  --from-beginning
```

### View Consumer Groups
```bash
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:29092 \
  --list

docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:29092 \
  --group inventory-service \
  --describe
```

### View Metrics
Analytics consumer prints metrics every 30 seconds:
```bash
docker logs analytics_consumer

# Output includes:
# - Total orders
# - Successful/failed counts
# - Failure rate
# - Orders per minute
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove all containers and volumes
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## File Structure
```
streaming-kafka/
├── docker-compose.yml          # Service orchestration
├── producer_order/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py             # Order producer service
├── inventory_consumer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py             # Inventory consumer service
├── analytics_consumer/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       └── main.py             # Analytics consumer service
└── tests/
    ├── Dockerfile
    ├── requirements.txt
    └── run_tests.py            # Test suite
```

## Comparison with Other Approaches

### vs Synchronous REST (Part A)
- **Kafka**: Decoupled services, scalable, handles backlog
- **REST**: Direct calls, failure cascades, simpler debugging

### vs Async RabbitMQ (Part B)
- **Kafka**: Stream replay, topic-based, event log
- **RabbitMQ**: Point-to-point, message deletion, work queue


