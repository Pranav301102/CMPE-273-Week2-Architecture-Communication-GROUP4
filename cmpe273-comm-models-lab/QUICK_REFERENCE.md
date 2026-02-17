# Quick Reference - Test Commands

## One-Line Test Commands

### Run All Parts (Automated)
```bash
cd cmpe273-comm-models-lab && ./run_all_tests.sh
```

---

## Part A: Synchronous REST

### Automated (Recommended)
```bash
cd cmpe273-comm-models-lab && ./test_part_a.sh
```

### Manual - Individual Tests
```bash
cd cmpe273-comm-models-lab/sync-rest

# Baseline test
docker compose up --build -d && sleep 5 && docker compose run --rm tests && docker compose down

# With delay (edit docker-compose.yml: DELAY_SEC=2)
docker compose up --build -d && sleep 5 && docker compose run --rm tests && docker compose down

# Always fail (edit docker-compose.yml: FAIL_MODE=always)
docker compose up --build -d && sleep 5 && docker compose run --rm tests && docker compose down
```

### View Logs
```bash
docker compose logs order_service
docker compose logs inventory_service
```

---

## Part B: Async RabbitMQ

### Automated (Recommended)
```bash
cd cmpe273-comm-models-lab && ./test_part_b.sh
```

### Manual - Individual Tests
```bash
cd cmpe273-comm-models-lab/async-rabbitmq

# Start services
docker compose up --build -d && sleep 15

# Test 1: Idempotency
docker compose run --rm tests python run_idempotency_check.py
docker compose logs inventory_service | grep idempotency

# Test 2: DLQ
docker compose run --rm tests python run_dlq_demo.py
docker compose exec rabbitmq rabbitmqctl list_queues

# Test 3: Backlog (requires manual intervention)
# Terminal 1:
docker compose run --rm tests python run_backlog_recovery.py
# Terminal 2 (after 10s):
docker compose stop inventory_service
# (wait 60s)
docker compose start inventory_service
# Terminal 3:
docker compose logs -f inventory_service

# Cleanup
docker compose down -v
```

### RabbitMQ Management
```bash
# Web UI
open http://localhost:15672
# Login: guest/guest

# CLI
docker compose exec rabbitmq rabbitmqctl list_queues name messages
```

---

## Part C: Streaming Kafka

### Automated (Recommended)
```bash
cd cmpe273-comm-models-lab && ./test_part_c.sh
```

### Manual - Individual Tests
```bash
cd cmpe273-comm-models-lab/streaming-kafka

# Start services
docker compose up --build -d && sleep 30

# Run all tests
docker compose run --rm tests

# Send test order
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "item": "pizza", "quantity": 1}'

# View metrics
docker compose logs -f analytics_consumer

# Cleanup
docker compose down -v
```

### Kafka Commands
```bash
# List topics
docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Describe consumer group
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group analytics-service

# Reset offset
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-service \
  --topic inventory-events \
  --reset-offsets --to-earliest --execute
```

---

## Troubleshooting

### Service not ready
```bash
# Increase wait time
sleep 15  # or more

# Check service health
docker compose ps
docker compose logs service_name
```

### Clean restart
```bash
docker compose down -v
docker compose up --build -d
```

### Check ports
```bash
# Part A
curl http://localhost:8001/health  # Order Service

# Part B
curl http://localhost:15672  # RabbitMQ UI

# Part C
curl http://localhost:5001/health  # Producer
```

### View all logs
```bash
docker compose logs -f
```

---

## Quick Verification

### Part A - Success Criteria
- [ ] Baseline latency < 10ms
- [ ] Delay causes timeout (~1000ms latency)
- [ ] Failures return proper error codes
- [ ] Logs show timeout/error handling

### Part B - Success Criteria
- [ ] Orders accepted during Inventory outage
- [ ] All messages processed after recovery
- [ ] Duplicate messages skipped (idempotency)
- [ ] Poison messages in DLQ

### Part C - Success Criteria
- [ ] 100 baseline requests complete
- [ ] 10K events produced successfully
- [ ] Consumer lag measured
- [ ] Replay produces consistent metrics

---

## Screenshot Checklist

### Part A
- [ ] Baseline test output
- [ ] Delay test output (showing ~1000ms latency)
- [ ] Failure test output (showing errors)
- [ ] Order service logs showing error handling

### Part B
- [ ] Backlog accumulation (orders posting while Inventory down)
- [ ] Backlog recovery (Inventory processing queue)
- [ ] Idempotency logs (showing "Idempotent skip")
- [ ] RabbitMQ UI showing DLQ queue

### Part C
- [ ] Test suite output (all 4 tests)
- [ ] Analytics metrics output
- [ ] Replay evidence (before/after)
- [ ] Throughput numbers from 10K test

---

## Time Estimates

| Part | Setup | Tests | Total |
|------|-------|-------|-------|
| A | 30s | 4 min | ~5 min |
| B | 15s | 4-6 min | ~5-7 min |
| C | 30s | 2 min | ~3 min |
| **All** | - | - | **~15 min** |

---

## Resources

- **Detailed Guide:** `TESTING_GUIDE.md`
- **Test Scripts:** `README_TESTING.md`
- **Assignment:** Main `README.md`

---

## Quick Links

### RabbitMQ
- UI: http://localhost:15672
- Credentials: guest/guest

### Kafka
- Bootstrap: localhost:9092
- Zookeeper: localhost:2181

### Services
- Part A Order: http://localhost:8001
- Part B Order: http://localhost:8001
- Part C Producer: http://localhost:5001

---

## Emergency Reset

```bash
# Stop everything
cd cmpe273-comm-models-lab
docker compose -f sync-rest/docker-compose.yml down -v
docker compose -f async-rabbitmq/docker-compose.yml down -v
docker compose -f streaming-kafka/docker-compose.yml down -v

# Clean Docker
docker system prune -f

# Restart
./run_all_tests.sh
```

---

**Pro Tip:** Run the automated scripts first (`./test_part_*.sh`) to get familiar with the tests, then run individual tests manually for detailed investigation if needed.
