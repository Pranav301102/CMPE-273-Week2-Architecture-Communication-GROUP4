# Kafka Streaming - Quick Start Guide

## Prerequisites
- Docker and Docker Compose installed
- Ports available: 2181, 9092, 5001, 5002, 5003

## Quick Start (5 minutes)

### 1. Build Docker Images
```bash
cd cmpe273-comm-models-lab/streaming-kafka
docker-compose build
```

### 2. Start Services
```bash
docker-compose up -d
```

Wait for Kafka to be ready, then check:
```bash
docker-compose logs kafka | grep "started"
```

### 3. Create Test Order (Manual)
```bash
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_1", "item": "pizza", "quantity": 1}'
```

Response: `{"order_id": "xxx", "status": "OrderPlaced"}`

### 4. Monitor Metrics
```bash
docker logs -f analytics_consumer
```

You should see metrics printed every 30 seconds showing:
- Total orders
- Successful reservations
- Failed orders
- Failure rate

## Running Full Test Suite

### Full Tests (5-10 minutes)
```bash
docker-compose run --rm tests
```

This will:
1. Test baseline latency (100 requests)
2. Produce 10,000 test events
3. Measure consumer lag
4. Test replay functionality
5. Generate final report

Report is saved to `/tmp/kafka_test_report.txt`

## What to Expect

### Baseline Latency Test Output
```
TEST 1: BASELINE LATENCY
======================================================
Request 1/100 - 5.23ms
Request 2/100 - 4.81ms
...

BASELINE LATENCY RESULTS
======================================================
Total Requests: 100
Average Latency: 6.45ms
Min Latency: 4.21ms
Max Latency: 50.32ms
======================================================
```

### Metrics Display
```
============================================================
METRICS REPORT
============================================================
Timestamp: 2026-02-16T14:30:45.123456
Total Orders: 1050
Successful: 1050
Failed: 0
Failure Rate: 0.00%
Orders by Minute: {'2026-02-16 14:29': 500, '2026-02-16 14:30': 550}
============================================================
```

### 10K Events Results
```
10K EVENTS PRODUCTION RESULTS
======================================================
Total Events: 10000
Duration: 15.34s
Throughput: 651.89 events/s
======================================================
```

### Replay Test Results
```
REPLAY TEST RESULTS
======================================================
Initial Read: 100 events
  - Successful: 100
  - Failed: 0

After Offset Reset: 100 events
  - Successful: 100
  - Failed: 0

Consistent Metrics: True
======================================================
```

## Testing Different Scenarios

### Scenario 1: Normal Operation
Just run the tests as above. All orders should succeed.

### Scenario 2: High Latency (Throttled Consumer)
The inventory consumer processes 1 message per second:
```bash
docker-compose stop inventory_consumer

# Add delay to inventory consumer
# Edit inventory_consumer/app/main.py to set:
# delay = 1.0  # 1 second per message

docker-compose start inventory_consumer

# Run tests - will see higher latency
docker-compose run --rm tests
```

### Scenario 3: Consumer Failure and Recovery
```bash
# In one terminal, watch the consumers
docker logs -f analytics_consumer

# In another terminal, stop the inventory consumer
docker-compose stop inventory_consumer

# Keep publishing orders
for i in {1..50}; do
  curl -X POST http://localhost:5001/order \
    -H "Content-Type: application/json" \
    -d '{"user_id": "user_'$i'", "item": "pizza", "quantity": 1}' &
done

# Watch orders being published but not processed
# Then restart consumer
docker-compose start inventory_consumer

# Watch consumer catch up and process all queued orders
```

### Scenario 4: Replay Events
```bash
# Run tests to process initial events
docker-compose run --rm tests

# Then reset consumer offset to replay
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:29092 \
  --group analytics-service \
  --reset-offsets \
  --to-earliest \
  --execute

# Restart analytics consumer
docker-compose restart analytics_consumer

# It will reprocess all events and recalculate metrics
```

## Key Advantages of Kafka Streaming

1. **Event Log**: Kafka topics act as distributed event logs
2. **Replay**: Reset offset to re-process events
3. **Decoupling**: Producers and consumers work independently
4. **Scalability**: Add consumers in parallel without changing producer
5. **Durability**: Events persist even if consumers go down
6. **Ordering**: Single partition ensures event order

## Comparison with REST (Part A)

| Aspect | Kafka | REST |
|--------|-------|------|
| Latency | Higher (event processing) | Lower (direct call) |
| Coupling | Decoupled | Tightly coupled |
| Scalability | Excellent | Limited |
| Failure handling | Automatic retry | Cascading failures |
| Replay | Built-in | Manual |
| Throughput | Higher | Limited |

## Monitoring Commands

### View Topics
```bash
docker-compose exec kafka kafka-topics \
  --bootstrap-server kafka:29092 \
  --list
```

### View Consumer Groups
```bash
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:29092 \
  --list
```

### Check Consumer Lag
```bash
docker-compose exec kafka kafka-consumer-groups \
  --bootstrap-server kafka:29092 \
  --group inventory-service \
  --describe
```

### Read Messages from Topic
```bash
docker-compose exec kafka kafka-console-consumer \
  --bootstrap-server kafka:29092 \
  --topic order-events \
  --from-beginning \
  --max-messages 10
```

## Troubleshooting

### Services won't start
```bash
# Check Docker daemon is running
docker ps

# Check logs for errors
docker-compose logs kafka
docker-compose logs producer_order

# Clean up and retry
docker-compose down -v
docker-compose up -d
```

### Kafka connection refused
```bash
# Wait for Kafka to fully start
docker logs kafka
# Look for "started SocketServer"

# Check environment in docker-compose.yml
# KAFKA_ADVERTISED_LISTENERS should be correct
```

### Tests timing out
```bash
# Increase timeout or wait longer
# Check if Kafka and services are healthy
curl http://localhost:5001/health

# Check container status
docker-compose ps
```

## File Locations

- Test report: `/tmp/kafka_test_report.txt`
- Service logs: `docker logs <container_name>`
- Kafka data: Docker volume (ephemeral)

## Cleanup

```bash
# Stop services
docker-compose down

# Remove volumes
docker-compose down -v

# Remove images
docker image rm streaming-kafka-producer_order:latest
docker image rm streaming-kafka-inventory_consumer:latest
docker image rm streaming-kafka-analytics_consumer:latest
```

## Next Steps

1. Run the baseline test to see latency metrics
2. Compare with synchronous REST results
3. Test failure scenarios (stop/restart services)
4. Observe replay and idempotency
5. Review generated metrics report

See [README.md](./README.md) for detailed documentation.
