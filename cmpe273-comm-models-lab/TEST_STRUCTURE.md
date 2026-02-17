# Test Structure and Organization

## Directory Structure

```
cmpe273-comm-models-lab/
│
├── run_all_tests.sh              ← Master test runner (all parts)
├── test_part_a.sh                ← Automated Part A testing
├── test_part_b.sh                ← Automated Part B testing
├── test_part_c.sh                ← Automated Part C testing
│
├── TESTING_GUIDE.md              ← Comprehensive step-by-step guide
├── README_TESTING.md             ← Test script documentation
├── QUICK_REFERENCE.md            ← Command cheat sheet
├── TEST_STRUCTURE.md             ← This file
│
├── test_results/                 ← Generated test results
│   └── test_results_*.txt
│
├── sync-rest/                    ← Part A: Synchronous REST
│   ├── docker-compose.yml
│   ├── order_service/
│   ├── inventory_service/
│   ├── notification_service/
│   └── tests/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── run_latency_tests.py      ← Original test
│       └── run_all_scenarios.py      ← NEW: Comprehensive test
│
├── async-rabbitmq/               ← Part B: Async RabbitMQ
│   ├── docker-compose.yml
│   ├── order_service/
│   ├── inventory_service/
│   ├── notification_service/
│   ├── common/
│   └── tests/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── run_backlog_recovery.py   ← Backlog test
│       ├── run_idempotency_check.py  ← Idempotency test
│       ├── run_dlq_demo.py           ← DLQ test
│       └── run_all_tests.py          ← NEW: Combined test runner
│
└── streaming-kafka/              ← Part C: Streaming Kafka
    ├── docker-compose.yml
    ├── producer_order/
    ├── inventory_consumer/
    ├── analytics_consumer/
    └── tests/
        ├── Dockerfile
        ├── requirements.txt
        └── run_tests.py              ← Comprehensive Kafka tests
```

## Test Execution Flow

### Master Test Runner (`run_all_tests.sh`)

```
run_all_tests.sh
    |
    ├─→ Part A: test_part_a.sh
    |       ├─→ Scenario 1: Baseline
    |       ├─→ Scenario 2: 2s Delay
    |       ├─→ Scenario 3: Always Fail
    |       └─→ Scenario 4: Timeout
    |
    ├─→ Part B: test_part_b.sh
    |       ├─→ Test 1: Idempotency
    |       ├─→ Test 2: DLQ
    |       └─→ Test 3: Backlog & Recovery
    |
    └─→ Part C: test_part_c.sh
            ├─→ Test 1: Baseline Latency
            ├─→ Test 2: 10K Events
            ├─→ Test 3: Consumer Lag
            └─→ Test 4: Replay
```

## Test Script Hierarchy

### Level 1: Master Runner
```
run_all_tests.sh
├── Orchestrates all three parts
├── Saves combined results
└── Provides final summary
```

### Level 2: Part-Specific Runners
```
test_part_a.sh              test_part_b.sh              test_part_c.sh
├── Automated config        ├── Guides through tests    ├── Waits for Kafka
├── Runs all scenarios      ├── Provides instructions   ├── Runs all tests
└── Resets config           └── Verification commands   └── Shows metrics
```

### Level 3: Test Implementations
```
Part A Tests                Part B Tests                Part C Tests
├── run_latency_tests.py    ├── run_backlog_recovery    └── run_tests.py
└── run_all_scenarios.py    ├── run_idempotency_check       ├── Latency test
                            ├── run_dlq_demo                ├── Throughput test
                            └── run_all_tests.py            ├── Lag test
                                                            └── Replay test
```

## Test Execution Paths

### Path 1: Fully Automated (Recommended for First Run)
```
User → run_all_tests.sh → All tests automatically → Results saved
```
**Pros:** No manual intervention, comprehensive results
**Cons:** Takes 15-20 minutes

### Path 2: Part-by-Part Automated
```
User → test_part_a.sh → Part A results
User → test_part_b.sh → Part B results (some manual steps)
User → test_part_c.sh → Part C results
```
**Pros:** Better control, easier to capture screenshots
**Cons:** Requires more commands

### Path 3: Manual Individual Tests
```
User → cd [part]
User → docker compose up -d
User → docker compose run --rm tests [python script]
User → Capture results
User → docker compose down
```
**Pros:** Full control, detailed investigation
**Cons:** Most time-consuming, easy to miss steps

## Test Configuration Matrix

### Part A: Sync REST

| Scenario | DELAY_SEC | FAIL_MODE | Expected Result |
|----------|-----------|-----------|-----------------|
| Baseline | 0 | none | Low latency, 100% success |
| Delay | 2 | none | ~1000ms latency (timeout) |
| Failure | 0 | always | Fast fail, 0% success |
| Timeout | 2 | none | Timeout after 1s |

### Part B: Async RabbitMQ

| Test | Service State | Expected Behavior |
|------|---------------|-------------------|
| Idempotency | Normal | Duplicate detection |
| DLQ | Normal | Poison msg to DLQ |
| Backlog | Inventory down 60s | Messages queue, then process |

### Part C: Streaming Kafka

| Test | Load | Metric Measured |
|------|------|-----------------|
| Baseline | 100 events | API latency |
| Throughput | 10K events | Events/second |
| Lag | High load | Consumer lag |
| Replay | Offset reset | Metric consistency |

## Docker Compose Services

### Part A Services
```
sync-rest/
├── order_service:8001      (Orchestrator)
├── inventory_service:8002  (Downstream 1)
├── notification_service:8003 (Downstream 2)
└── tests                   (Test container)
```

### Part B Services
```
async-rabbitmq/
├── rabbitmq:5672, :15672   (Message broker)
├── order_service:8001      (Producer)
├── inventory_service       (Consumer)
├── notification_service    (Consumer)
└── tests                   (Test container)
```

### Part C Services
```
streaming-kafka/
├── zookeeper:2181          (Kafka dependency)
├── kafka:9092, :29092      (Stream platform)
├── producer_order:5001     (Event producer)
├── inventory_consumer:5002 (Event consumer)
├── analytics_consumer:5003 (Metrics consumer)
└── tests                   (Test container)
```

## Test Data Flow

### Part A: Request-Response Chain
```
Test Script
    ↓ POST /order
OrderService
    ↓ POST /reserve
InventoryService
    ↑ Response
OrderService
    ↓ POST /send
NotificationService
    ↑ Response
OrderService
    ↑ Response
Test Script
```

### Part B: Event-Driven Flow
```
Test Script
    ↓ POST /order
OrderService
    ↓ Publish OrderPlaced
RabbitMQ Queue
    ↓ Consume
InventoryService
    ↓ Publish InventoryReserved
RabbitMQ Queue
    ↓ Consume
NotificationService
```

### Part C: Stream Processing
```
Test Script / Producer
    ↓ Publish OrderPlaced
Kafka Topic: order-events
    ↓ Consume
InventoryConsumer
    ↓ Publish InventoryReserved/Failed
Kafka Topic: inventory-events
    ├─→ AnalyticsConsumer (metrics)
    └─→ Test replay consumer
```

## Test Output Artifacts

### Console Output
```
All tests produce formatted output to stdout:
├── Progress indicators
├── Metric tables
├── Status summaries
└── Error logs
```

### Saved Reports
```
Part A: /tmp/sync_rest_test_report.txt
Part B: /tmp/rabbitmq_test_report.txt
Part C: /tmp/kafka_test_report.txt
Master: test_results/test_results_YYYYMMDD_HHMMSS.txt
```

### Screenshots (Manual)
```
User captures:
├── Console outputs
├── Service logs
├── RabbitMQ Management UI
└── Analytics metrics
```

## Dependencies and Prerequisites

### System Requirements
- Docker & Docker Compose
- Bash shell (macOS/Linux)
- curl (for manual testing)
- 4GB+ RAM for Kafka

### Port Requirements
```
Part A:
├── 8001 (Order)
├── 8002 (Inventory)
└── 8003 (Notification)

Part B:
├── 8001 (Order)
├── 5672 (RabbitMQ)
└── 15672 (RabbitMQ UI)

Part C:
├── 2181 (Zookeeper)
├── 9092, 29092 (Kafka)
├── 5001 (Producer)
├── 5002 (Inventory)
└── 5003 (Analytics)
```

## Test Timing

### Initialization Times
- Part A: ~5 seconds
- Part B: ~15 seconds (RabbitMQ)
- Part C: ~30 seconds (Kafka)

### Test Execution Times
- Part A: ~4 minutes (all 4 scenarios)
- Part B: ~5-7 minutes (including manual steps)
- Part C: ~2-3 minutes (all 4 tests)

### Total Time Budget
- Setup: ~1 minute
- Execution: ~15 minutes
- Screenshot capture: ~10 minutes
- **Total: ~25-30 minutes for all testing**

## Error Handling

### Script Error Handling
All scripts include:
- Service health checks
- Timeout protection
- Graceful cleanup on exit
- Error logging

### Test Failures
Tests continue even if:
- Individual requests fail
- Services are slow to start
- Some scenarios fail

### Recovery Procedures
Each script provides:
- Cleanup commands
- Restart instructions
- Verification steps

## Usage Patterns

### First-Time User
```
1. Read TESTING_GUIDE.md
2. Run ./run_all_tests.sh
3. Review outputs
4. Capture screenshots
```

### Experienced User
```
1. Check QUICK_REFERENCE.md
2. Run specific part scripts
3. Use manual commands for details
```

### Debugging
```
1. Run individual test scripts
2. Check service logs
3. Use verification commands
4. Consult TESTING_GUIDE.md
```

## Customization Points

### Modify Test Parameters
```python
# In test scripts:
N = 50              # Number of requests
DURATION = 90       # Test duration (seconds)
INTERVAL = 1.0      # Request interval
```

### Modify Service Behavior
```yaml
# In docker-compose.yml:
environment:
  - DELAY_SEC=2     # Injection delay
  - FAIL_MODE=always # Failure mode
  - FAIL_PROB=0.3   # Failure probability
```

### Modify Timeout Settings
```yaml
# In docker-compose.yml:
environment:
  - INVENTORY_TIMEOUT_SEC=1.0
  - KAFKA_TIMEOUT_MS=5000
```

## Integration Points

### With CI/CD
```bash
# Can be integrated into CI pipeline:
./run_all_tests.sh && submit_results.sh
```

### With Monitoring
```bash
# Can feed into monitoring:
docker compose logs -f | parse_metrics.sh
```

### With Reporting
```bash
# Can generate reports:
./run_all_tests.sh > results.txt
generate_report.sh results.txt
```

## Summary

This test infrastructure provides:

✅ **Complete coverage** - All assignment requirements tested
✅ **Automation** - Minimal manual intervention required
✅ **Flexibility** - Multiple execution paths
✅ **Documentation** - Comprehensive guides
✅ **Validation** - Built-in verification
✅ **Reporting** - Automatic result capture

**The test structure is designed to be:**
- Easy to use (automated scripts)
- Easy to understand (clear documentation)
- Easy to debug (detailed logging)
- Easy to customize (well-commented code)

Choose your path based on your needs:
- **Quick validation:** `./run_all_tests.sh`
- **Detailed investigation:** Individual test scripts
- **Learning:** Manual step-by-step execution
