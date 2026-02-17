# Test Scripts Documentation

This directory contains comprehensive test scripts for all three parts of the CMPE 273 Communication Models Lab.

## Quick Start

### Automated Testing (Recommended)

Each part has a shell script that automates the entire testing process:

```bash
# Part A: Synchronous REST
./test_part_a.sh

# Part B: Async RabbitMQ
./test_part_b.sh

# Part C: Streaming Kafka
./test_part_c.sh
```

### Manual Testing

Follow the detailed instructions in `TESTING_GUIDE.md`.

---

## Available Test Scripts

### Part A: Synchronous REST

**Location:** `sync-rest/tests/`

#### Scripts:
1. **`run_latency_tests.py`** - Basic latency test (original)
   ```bash
   docker compose run --rm tests
   ```

2. **`run_all_scenarios.py`** - Comprehensive scenario runner (NEW)
   ```bash
   docker compose run --rm tests python run_all_scenarios.py
   ```

#### Automated Shell Script:
```bash
./test_part_a.sh
```

**What it does:**
- Automatically runs 4 test scenarios
- Changes configuration between tests
- Generates comparison reports
- No manual intervention needed

**Test Scenarios:**
1. Baseline (no delay, no failures)
2. 2-second delay injection
3. Always-fail mode
4. Timeout scenario

**Expected Runtime:** ~5 minutes

---

### Part B: Async RabbitMQ

**Location:** `async-rabbitmq/tests/`

#### Scripts:
1. **`run_backlog_recovery.py`** - Backlog and recovery test
   ```bash
   docker compose run --rm tests python run_backlog_recovery.py
   ```

2. **`run_idempotency_check.py`** - Idempotency verification
   ```bash
   docker compose run --rm tests python run_idempotency_check.py
   ```

3. **`run_dlq_demo.py`** - Dead letter queue demo
   ```bash
   docker compose run --rm tests python run_dlq_demo.py
   ```

4. **`run_all_tests.py`** - Comprehensive test suite (NEW)
   ```bash
   docker compose run --rm tests python run_all_tests.py
   ```

#### Automated Shell Script:
```bash
./test_part_b.sh
```

**What it does:**
- Guides you through all 3 RabbitMQ tests
- Provides clear instructions for manual steps
- Includes verification commands
- Shows RabbitMQ Management UI details

**Test Coverage:**
1. Idempotency (duplicate message handling)
2. DLQ (poison message handling)
3. Backlog & Recovery (resilience during outages)

**Expected Runtime:** ~5 minutes (plus 90s for backlog test)

**Note:** Backlog test requires manual intervention (stopping/starting inventory service)

---

### Part C: Streaming Kafka

**Location:** `streaming-kafka/tests/`

#### Scripts:
1. **`run_tests.py`** - Comprehensive Kafka test suite
   ```bash
   docker compose run --rm tests
   ```

#### Automated Shell Script:
```bash
./test_part_c.sh
```

**What it does:**
- Starts Kafka and all services
- Waits for Kafka to be ready (~30s)
- Runs all 4 test scenarios
- Shows real-time analytics
- Offers optional replay demonstration

**Test Coverage:**
1. Baseline Latency (100 requests)
2. 10K Events Throughput
3. Consumer Lag Measurement
4. Replay with Offset Reset

**Expected Runtime:** ~3 minutes

---

## Test Output Locations

### Part A
- Console output with latency tables
- Report saved to: `/tmp/sync_rest_test_report.txt` (inside container)

### Part B
- Console output with test results
- Report saved to: `/tmp/rabbitmq_test_report.txt` (inside container)
- RabbitMQ UI: http://localhost:15672 (guest/guest)

### Part C
- Console output with all metrics
- Report saved to: `/tmp/kafka_test_report.txt` (inside container)
- Real-time analytics in logs

---

## Troubleshooting

### Services won't start
```bash
# Clean everything and restart
docker compose down -v
docker compose up --build -d
```

### Tests fail with connection errors
```bash
# Increase wait time (edit scripts or add manual sleep)
sleep 15  # before running tests
```

### Kafka not ready
```bash
# Kafka takes ~30 seconds to start
# Check if ready:
docker compose logs kafka | grep "started"
```

### RabbitMQ Management UI not accessible
```bash
# Wait longer for RabbitMQ
sleep 15
# Verify it's running:
curl http://localhost:15672
```

### Port already in use
```bash
# Check what's using the port
lsof -i :8001  # or whichever port
# Stop conflicting services or change ports in docker-compose.yml
```

---

## Submission Requirements

### Part A Deliverables
- ✓ Latency comparison table (baseline vs delay vs failure)
- ✓ Screenshots of test outputs
- ✓ Explanation of synchronous coupling behavior
- ✓ Logs showing timeout/error handling

### Part B Deliverables
- ✓ Screenshots of backlog accumulation and recovery
- ✓ Logs showing idempotent behavior
- ✓ DLQ evidence (RabbitMQ UI or CLI output)
- ✓ Written explanation of idempotency strategy
- ✓ Discussion of async benefits vs synchronous

### Part C Deliverables
- ✓ Test report with all 4 test results
- ✓ Metrics output (orders/min, failure rate)
- ✓ Evidence of replay (before/after)
- ✓ Throughput measurements
- ✓ Screenshots of consumer logs

---

## Verification Commands

### Part A
```bash
cd sync-rest

# View service logs
docker compose logs order_service
docker compose logs inventory_service

# Check service health
docker compose ps

# Run specific test
docker compose run --rm tests
```

### Part B
```bash
cd async-rabbitmq

# Check RabbitMQ queues
docker compose exec rabbitmq rabbitmqctl list_queues name messages

# View service logs
docker compose logs inventory_service | grep "Idempotent skip"
docker compose logs notification_service

# RabbitMQ Management UI
open http://localhost:15672
```

### Part C
```bash
cd streaming-kafka

# Check Kafka topics
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe consumer groups
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group analytics-service

# View analytics in real-time
docker compose logs -f analytics_consumer

# Send manual test order
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "item": "pizza", "quantity": 1}'
```

---

## Advanced Usage

### Custom Test Configurations

#### Part A - Custom latency test
```bash
cd sync-rest

# Edit docker-compose.yml to set:
#   DELAY_SEC: 5
#   FAIL_MODE: prob
#   FAIL_PROB: 0.3  (30% failure rate)

docker compose up --build -d
docker compose run --rm tests python run_all_scenarios.py
```

#### Part B - Custom backlog duration
```bash
cd async-rabbitmq/tests

# Edit run_backlog_recovery.py
# Change: DURATION = 90  to desired seconds
# Change: INTERVAL = 1.0  to desired interval

docker compose run --rm tests python run_backlog_recovery.py
```

#### Part C - Custom event count
```bash
cd streaming-kafka

# Produce custom number of events
docker compose run --rm tests python -c "
from run_tests import KafkaStreamingTest
test = KafkaStreamingTest()
test.wait_for_kafka()
test.test_10k_events()  # Modify run_tests.py to change event count
"
```

---

## Performance Benchmarks

### Expected Results

#### Part A
| Scenario | p50 (ms) | p95 (ms) | Success Rate |
|----------|----------|----------|--------------|
| Baseline | 2-5 | 5-10 | 100% |
| 2s Delay | 1000-1100 | 1100-1200 | 0-10% (timeouts) |
| Always Fail | 2-5 | 5-10 | 0% |

#### Part B
| Test | Metric | Expected |
|------|--------|----------|
| Backlog | Messages queued | 60-90 |
| Backlog | Recovery time | 5-15s |
| Idempotency | Duplicate processing | 0 |
| DLQ | Poison messages | 1 |

#### Part C
| Test | Metric | Expected |
|------|--------|----------|
| Baseline | Avg latency | 5-10ms |
| Throughput | Events/sec | 500+ |
| 10K Events | Duration | 15-30s |
| Replay | Consistency | 100% |

---

## Tips for Success

1. **Always wait for services to be ready**
   - RabbitMQ: ~10-15 seconds
   - Kafka: ~30 seconds
   - General services: ~5 seconds

2. **Check logs frequently**
   ```bash
   docker compose logs -f service_name
   ```

3. **Use RabbitMQ Management UI**
   - Visual queue monitoring
   - Message inspection
   - Consumer tracking

4. **Monitor Docker resources**
   ```bash
   docker stats
   ```

5. **Take screenshots as you go**
   - Capture test outputs immediately
   - Save logs before cleanup
   - Screenshot RabbitMQ UI queues

6. **Read error messages carefully**
   - Connection refused = service not ready yet
   - Timeout = increase wait time
   - 404 = wrong URL or service not started

---

## Additional Resources

- **Detailed Testing Guide:** `TESTING_GUIDE.md`
- **RabbitMQ Documentation:** https://www.rabbitmq.com/documentation.html
- **Kafka Documentation:** https://kafka.apache.org/documentation/
- **Docker Compose Reference:** https://docs.docker.com/compose/

---

## Getting Help

### Common Issues

**Q: Tests are too slow**
A: Reduce the number of requests or event count in the test scripts

**Q: Services keep crashing**
A: Check logs with `docker compose logs`, increase memory limits

**Q: Can't access RabbitMQ/Kafka UI**
A: Ensure ports aren't blocked by firewall, try `localhost` vs `127.0.0.1`

**Q: Tests pass but no output**
A: Check if output is going to container logs: `docker compose logs tests`

### Debug Mode

Enable verbose logging:
```bash
# Set in docker-compose.yml
environment:
  - PYTHONUNBUFFERED=1
  - LOG_LEVEL=DEBUG
```

---

## Conclusion

These test scripts provide comprehensive coverage of all assignment requirements. Use the automated shell scripts for quick testing, or run individual test scripts for detailed investigation.

**Recommended Testing Order:**
1. Part A (quickest, ~5 min)
2. Part C (moderate, ~3 min setup + tests)
3. Part B (longest, ~5-7 min with manual steps)

Good luck with your testing! 🚀
