# Comprehensive Testing Guide
## CMPE 273 - Communication Models Lab Testing

This guide provides detailed instructions for testing all three parts of the lab assignment.

---

## Part A: Synchronous REST Testing

### Prerequisites
```bash
cd cmpe273-comm-models-lab/sync-rest
```

### Test 1: Baseline Latency Test
**What it does:** Measures latency with normal service operation (no delays or failures)

```bash
# 1. Start services with no delays
docker compose up --build -d

# 2. Wait for services to be ready
sleep 5

# 3. Run baseline test
docker compose run --rm tests

# 4. View logs if needed
docker compose logs order_service
```

**Expected Results:**
- p50, p95, avg latencies should be < 10ms
- All 50 requests should return 200 OK

---

### Test 2: Latency Impact with 2s Delay
**What it does:** Injects 2-second delay in Inventory service to show latency inflation

```bash
# 1. Edit docker-compose.yml
# Change inventory_service environment to:
#   - DELAY_SEC=2
#   - FAIL_MODE=none

# 2. Restart services
docker compose up --build -d

# 3. Wait for services
sleep 5

# 4. Run latency test
docker compose run --rm tests

# 5. View detailed logs
docker compose logs -f order_service
```

**Expected Results:**
- Latencies will be around 1000ms (hitting the 1s timeout)
- Many requests will return 503 Service Unavailable
- Shows synchronous dependency cascading effect

---

### Test 3: Inventory Failure - Always Fail Mode
**What it does:** Forces Inventory service to always return errors

```bash
# 1. Edit docker-compose.yml
# Change inventory_service environment to:
#   - DELAY_SEC=0
#   - FAIL_MODE=always

# 2. Restart services
docker compose up --build -d

# 3. Wait for services
sleep 5

# 4. Run test
docker compose run --rm tests

# 5. Check logs for error handling
docker compose logs order_service
```

**Expected Results:**
- All requests should fail gracefully
- OrderService should log "Inventory reservation failed"
- Returns proper error responses (500 or 503)

---

### Test 4: Timeout Test
**What it does:** Sets delay longer than timeout to demonstrate timeout behavior

```bash
# 1. Edit docker-compose.yml
# Change inventory_service environment to:
#   - DELAY_SEC=2
#   - FAIL_MODE=none

# Note: OrderService has INVENTORY_TIMEOUT_SEC=1.0

# 2. Restart services
docker compose up --build -d

# 3. Run test
docker compose run --rm tests
```

**Expected Results:**
- Requests timeout after ~1 second
- OrderService logs "Timeout calling inventory"
- Demonstrates timeout protection in synchronous calls

---

### Cleanup Part A
```bash
docker compose down
```

---

## Part B: Async RabbitMQ Testing

### Prerequisites
```bash
cd cmpe273-comm-models-lab/async-rabbitmq
docker compose up --build -d

# Wait for RabbitMQ to be ready
sleep 10
```

### Test 1: Backlog and Recovery
**What it does:** Demonstrates message queuing resilience during service outages

```bash
# Terminal 1: Start the backlog test (runs for 90 seconds)
docker compose run --rm tests python run_backlog_recovery.py

# Terminal 2: After ~10 seconds, kill inventory service
docker compose stop inventory_service

# Wait 60 seconds while orders accumulate in the queue

# Terminal 2: Restart inventory service
docker compose start inventory_service

# Terminal 3: Watch the backlog drain
docker compose logs -f inventory_service
```

**Expected Results:**
- Orders continue to be accepted even when Inventory is down
- Messages queue in RabbitMQ
- When Inventory restarts, all queued messages are processed
- No messages are lost

**To Verify:**
```bash
# Check RabbitMQ queue status
docker compose exec rabbitmq rabbitmqctl list_queues name messages

# Or use RabbitMQ Management UI
# Open http://localhost:15672 (username: guest, password: guest)
```

---

### Test 2: Idempotency Check
**What it does:** Publishes the same message twice to ensure no double-processing

```bash
# 1. Run idempotency test
docker compose run --rm tests python run_idempotency_check.py

# 2. Check inventory service logs
docker compose logs inventory_service | grep "idempotency-test-order-1"
```

**Expected Results:**
- First message: "Processing order idempotency-test-order-1"
- Second message: "Idempotent skip for idempotency-test-order-1"
- Inventory is reserved only once

**Idempotency Strategy:**
- Each service maintains a set of processed order_ids
- Before processing, checks if order_id already exists
- If exists, skips processing and acknowledges message
- Prevents duplicate inventory reservations

---

### Test 3: Dead Letter Queue (DLQ)
**What it does:** Sends malformed message to demonstrate poison message handling

```bash
# 1. Run DLQ test
docker compose run --rm tests python run_dlq_demo.py

# 2. Check for poison message in DLQ
docker compose exec rabbitmq rabbitmqctl list_queues name messages

# 3. View in RabbitMQ Management UI
# Open http://localhost:15672
# Navigate to Queues tab
# Look for 'order_placed_dlq' queue
```

**Expected Results:**
- Malformed message is rejected (nack'd)
- Message is routed to dead letter queue
- Main queue continues processing valid messages
- No service crashes from poison messages

---

### Cleanup Part B
```bash
docker compose down -v
```

---

## Part C: Streaming Kafka Testing

### Prerequisites
```bash
cd cmpe273-comm-models-lab/streaming-kafka
docker compose up --build -d

# Wait for Kafka to be ready (important!)
sleep 30
```

### Test 1: Baseline Latency (100 requests)
**What it does:** Measures API latency for publishing events

```bash
# Run full test suite (includes all 4 tests)
docker compose run --rm tests
```

**Expected Results:**
- Average latency: 5-10ms
- Max latency: < 100ms
- All requests return 202 Accepted

---

### Test 2: 10K Events Throughput
**What it does:** Stress test with 10,000 events

**Included in main test suite above, or run standalone:**

```bash
# Create manual orders for verification
for i in {1..100}; do
  curl -X POST http://localhost:5001/order \
    -H "Content-Type: application/json" \
    -d "{\"user_id\": \"user_$i\", \"item\": \"pizza\", \"quantity\": 1}"
  sleep 0.1
done
```

**Expected Results:**
- Throughput: 500+ events/second
- Processing time: < 30 seconds
- All events successfully published to Kafka

---

### Test 3: Consumer Lag
**What it does:** Monitors lag between producer and consumers

```bash
# Monitor analytics consumer
docker compose logs -f analytics_consumer

# In another terminal, produce events rapidly
docker compose run --rm tests

# Check Kafka consumer groups
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group analytics-service
```

**Expected Results:**
- Shows lag increasing during high load
- Lag drains as consumer catches up
- Demonstrates consumer scalability needs

---

### Test 4: Replay with Offset Reset
**What it does:** Resets consumer offset to replay events

```bash
# 1. Produce some events first
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_1", "item": "pizza", "quantity": 1}'

# 2. Wait for processing
sleep 5

# 3. Check current metrics
docker compose logs analytics_consumer | tail -20

# 4. Reset offset (included in run_tests.py)
# The test script creates a new consumer group and reads from earliest

# 5. Run replay test
docker compose run --rm tests
```

**Expected Results:**
- Metrics are recalculated from beginning
- Before and after metrics should match
- Demonstrates event sourcing capability

**Manual offset reset:**
```bash
# Reset to earliest
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-service \
  --topic inventory-events \
  --reset-offsets --to-earliest --execute

# Restart consumer to pick up reset
docker compose restart analytics_consumer
```

---

### Monitor Real-time Metrics
```bash
# View analytics metrics (updated every 30 seconds)
docker compose logs -f analytics_consumer

# View inventory events
docker compose logs -f inventory_consumer

# View all events
docker compose logs -f
```

---

### Cleanup Part C
```bash
docker compose down -v
```

---

## Quick Test Commands Summary

### Part A - Synchronous REST
```bash
cd cmpe273-comm-models-lab/sync-rest

# Baseline
docker compose up --build -d && sleep 5 && docker compose run --rm tests

# With 2s delay (edit docker-compose.yml first: DELAY_SEC=2)
docker compose up --build -d && sleep 5 && docker compose run --rm tests

# Always fail (edit docker-compose.yml first: FAIL_MODE=always)
docker compose up --build -d && sleep 5 && docker compose run --rm tests

docker compose down
```

### Part B - Async RabbitMQ
```bash
cd cmpe273-comm-models-lab/async-rabbitmq
docker compose up --build -d && sleep 10

# Test 1: Backlog (requires manual intervention)
docker compose run --rm tests python run_backlog_recovery.py
# In another terminal: docker compose stop inventory_service (wait 60s)
# Then: docker compose start inventory_service

# Test 2: Idempotency
docker compose run --rm tests python run_idempotency_check.py
docker compose logs inventory_service | grep idempotency

# Test 3: DLQ
docker compose run --rm tests python run_dlq_demo.py
docker compose exec rabbitmq rabbitmqctl list_queues

docker compose down -v
```

### Part C - Streaming Kafka
```bash
cd cmpe273-comm-models-lab/streaming-kafka
docker compose up --build -d && sleep 30

# Run all tests
docker compose run --rm tests

# Monitor metrics
docker compose logs -f analytics_consumer

docker compose down -v
```

---

## Troubleshooting

### Services won't start
```bash
# Check logs
docker compose logs

# Restart from scratch
docker compose down -v
docker compose up --build -d
```

### Tests timeout
```bash
# Increase wait time before running tests
sleep 15  # or longer for Kafka

# Check service health
docker compose ps
```

### RabbitMQ Management UI not accessible
```bash
# Wait longer for RabbitMQ to start
sleep 15

# Check if port is bound
curl http://localhost:15672
```

### Kafka not ready
```bash
# Kafka takes longer to start (~30 seconds)
docker compose logs kafka | grep "started"

# Verify Kafka is listening
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092
```

---

## Expected Test Outputs

### Part A: Latency Table Format
```
case,n,p50,p95,avg
baseline,50,2.52,2.83,2.61
with_delay,50,1011.56,1014.29,1011.53
```

### Part B: Console Output Examples
```
# Backlog recovery
[1] order_id=a1b2c3d4... -> 202
[2] order_id=e5f6g7h8... -> 202
...
Done. Total orders posted: 90

# Inventory logs after restart
Processing order a1b2c3d4...
Processing order e5f6g7h8...
```

### Part C: Metrics Report
```
BASELINE LATENCY RESULTS
========================
Total Requests: 100
Average Latency: 7.23ms
Min Latency: 3.45ms
Max Latency: 45.67ms

10K EVENTS PRODUCTION RESULTS
==============================
Total Events: 10000
Duration: 18.45s
Throughput: 542.17 events/s
```

---

## Submission Checklist

### Part A
- [ ] Latency table with baseline, delay, and failure cases
- [ ] Screenshots showing different failure modes
- [ ] Brief explanation of synchronous coupling behavior

### Part B
- [ ] Screenshots of backlog accumulation and recovery
- [ ] Logs showing idempotency (duplicate skip)
- [ ] Evidence of DLQ (RabbitMQ Management UI or CLI output)
- [ ] Explanation of idempotency strategy (order_id tracking)

### Part C
- [ ] Test report showing all 4 test results
- [ ] Metrics output (orders/min, failure rate)
- [ ] Evidence of replay (before/after offset reset)
- [ ] Screenshots of analytics consumer logs
