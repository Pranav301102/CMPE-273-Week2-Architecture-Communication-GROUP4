# Testing Summary - CMPE 273 Communication Models Lab

## Overview

Comprehensive test scripts have been created for all three parts of the assignment. This document provides a quick overview and points to detailed resources.

## What's New

### Automated Test Scripts ✨

Three automated shell scripts that handle all testing scenarios:

- **`test_part_a.sh`** - Synchronous REST testing
- **`test_part_b.sh`** - Async RabbitMQ testing
- **`test_part_c.sh`** - Streaming Kafka testing
- **`run_all_tests.sh`** - Master script to run everything

### Enhanced Test Runners 🚀

Python scripts for comprehensive testing:

- **Part A:** `run_all_scenarios.py` - Tests all 4 scenarios automatically
- **Part B:** `run_all_tests.py` - Runs all 3 RabbitMQ tests with guidance
- **Part C:** `run_tests.py` - Complete Kafka test suite (already existed)

### Documentation 📚

- **`TESTING_GUIDE.md`** - Comprehensive step-by-step testing guide
- **`README_TESTING.md`** - Test script documentation and usage
- **`QUICK_REFERENCE.md`** - Quick command reference and cheat sheet

## Quick Start

### Option 1: Run Everything (Recommended for first-time)

```bash
cd cmpe273-comm-models-lab
./run_all_tests.sh
```

This will:
- Run all tests for Parts A, B, and C
- Generate comprehensive reports
- Save results to `test_results/` directory
- Take approximately 15-20 minutes

### Option 2: Run Individual Parts

```bash
# Part A only (~5 minutes)
cd cmpe273-comm-models-lab
./test_part_a.sh

# Part B only (~5-7 minutes)
cd cmpe273-comm-models-lab
./test_part_b.sh

# Part C only (~3 minutes)
cd cmpe273-comm-models-lab
./test_part_c.sh
```

### Option 3: Manual Testing

Follow the detailed instructions in `cmpe273-comm-models-lab/TESTING_GUIDE.md`

## Test Coverage

### Part A: Synchronous REST ✅

**What it tests:**
- Baseline latency measurement (50 requests)
- Impact of 2-second delay injection
- Always-fail mode error handling
- Timeout behavior (2s delay with 1s timeout)

**Expected outputs:**
- Latency comparison table
- Status code distribution
- Error logs from OrderService
- Performance analysis

**Files:**
- Original: `sync-rest/tests/run_latency_tests.py`
- New: `sync-rest/tests/run_all_scenarios.py`
- Automated: `test_part_a.sh`

---

### Part B: Async RabbitMQ ✅

**What it tests:**
1. **Idempotency** - Duplicate message handling
2. **Dead Letter Queue** - Poison message routing
3. **Backlog & Recovery** - Resilience during outages

**Expected outputs:**
- Idempotency logs showing duplicate skip
- DLQ queue with 1 poison message
- Backlog accumulation and recovery evidence
- Message count verification

**Files:**
- `async-rabbitmq/tests/run_idempotency_check.py`
- `async-rabbitmq/tests/run_dlq_demo.py`
- `async-rabbitmq/tests/run_backlog_recovery.py`
- New: `async-rabbitmq/tests/run_all_tests.py`
- Automated: `test_part_b.sh`

---

### Part C: Streaming Kafka ✅

**What it tests:**
1. **Baseline Latency** - 100 order requests
2. **Throughput** - 10,000 event production
3. **Consumer Lag** - Monitoring under load
4. **Replay** - Offset reset and consistency

**Expected outputs:**
- Latency metrics (avg, min, max)
- Throughput measurement (events/sec)
- Consumer lag information
- Replay consistency verification
- Analytics metrics report

**Files:**
- `streaming-kafka/tests/run_tests.py`
- Automated: `test_part_c.sh`

## Test Results Location

All automated tests save results to:

```
cmpe273-comm-models-lab/
  test_results/
    test_results_YYYYMMDD_HHMMSS.txt
```

Individual test reports (inside containers):
- Part A: `/tmp/sync_rest_test_report.txt`
- Part B: `/tmp/rabbitmq_test_report.txt`
- Part C: `/tmp/kafka_test_report.txt`

## Submission Checklist

Use this checklist to ensure you have everything:

### Part A - Synchronous REST
- [ ] Latency table with 4 scenarios (baseline, delay, fail, timeout)
- [ ] Screenshots of test outputs
- [ ] Console logs showing error handling
- [ ] Written explanation of synchronous coupling behavior
- [ ] Analysis of why latency increases with delay

### Part B - Async RabbitMQ
- [ ] Screenshots of backlog test (orders posting during outage)
- [ ] Screenshots of backlog recovery (processing after restart)
- [ ] Logs showing "Idempotent skip" for duplicate messages
- [ ] RabbitMQ UI screenshot or CLI output showing DLQ
- [ ] Written explanation of idempotency strategy
- [ ] Discussion of async benefits vs synchronous

### Part C - Streaming Kafka
- [ ] Complete test report (all 4 tests)
- [ ] Baseline latency metrics
- [ ] 10K events throughput numbers
- [ ] Consumer lag evidence
- [ ] Replay test results (before/after comparison)
- [ ] Analytics consumer log screenshots
- [ ] Written explanation of replay consistency

## Documentation Reference

| Document | Purpose | When to Use |
|----------|---------|-------------|
| `QUICK_REFERENCE.md` | Quick commands | When you know what to do |
| `TESTING_GUIDE.md` | Step-by-step guide | First time testing |
| `README_TESTING.md` | Script documentation | Understanding test scripts |
| This file | Overview | Getting started |

## Common Commands

### Start a part
```bash
cd cmpe273-comm-models-lab/[part-directory]
docker compose up --build -d
```

### Run tests
```bash
# Using automated script
./test_part_a.sh  # or b, c

# Manual
docker compose run --rm tests
```

### View logs
```bash
docker compose logs -f [service_name]
```

### Check status
```bash
docker compose ps
```

### Clean up
```bash
docker compose down -v
```

## Troubleshooting

### Services won't start
```bash
docker compose down -v
docker compose up --build -d --force-recreate
```

### Tests timeout
Increase wait times in the scripts or add manual delays:
```bash
sleep 15  # before running tests
```

### Kafka not ready
Wait longer (Kafka needs ~30 seconds):
```bash
docker compose logs kafka | grep "started"
```

### Port conflicts
Check and kill conflicting processes:
```bash
lsof -i :8001  # or relevant port
```

## Performance Expectations

### Part A Latencies
- Baseline: 2-10ms
- With delay: 1000-1100ms (hitting timeout)
- Failure: Fast failure response

### Part B Metrics
- Message throughput: 10-50 msg/s
- Recovery time: 5-15s for 60 messages
- Idempotency: 100% duplicate detection

### Part C Metrics
- API latency: 5-10ms
- Throughput: 500+ events/s
- 10K events: 15-30s processing

## Tips for Success

1. **Run automated scripts first** - They handle configuration changes automatically
2. **Read the output** - Test scripts provide detailed instructions and verification steps
3. **Take screenshots immediately** - Don't wait until cleanup
4. **Check logs frequently** - Use `docker compose logs -f service_name`
5. **Save outputs** - Copy console output to text files
6. **Use RabbitMQ UI** - Visual verification is easier (http://localhost:15672)
7. **Be patient with Kafka** - It needs 30 seconds to start
8. **Don't skip cleanup** - Use `docker compose down -v` between runs

## Time Management

| Task | Time Required |
|------|---------------|
| Part A setup + tests | 5-7 minutes |
| Part B setup + tests | 5-10 minutes |
| Part C setup + tests | 3-5 minutes |
| Screenshot capture | 10-15 minutes |
| Report writing | 30-45 minutes |
| **Total** | **~60-90 minutes** |

## Getting Help

### Check Documentation
1. Start with `QUICK_REFERENCE.md` for commands
2. Read `TESTING_GUIDE.md` for detailed steps
3. Review `README_TESTING.md` for script details

### Debug Issues
1. Check service logs: `docker compose logs [service]`
2. Verify service health: `docker compose ps`
3. Review error messages carefully
4. Check Docker resources: `docker stats`

### Common Solutions
- **Connection refused** → Service not ready, wait longer
- **Timeout** → Increase wait time or check service health
- **404 errors** → Wrong URL or service not started
- **Port in use** → Another service using the port

## Summary

You now have comprehensive test infrastructure for all three parts:

✅ **Automated testing** - One command to run all tests
✅ **Individual control** - Run specific tests as needed
✅ **Detailed output** - Reports saved automatically
✅ **Verification tools** - Commands to check each requirement
✅ **Complete documentation** - Step-by-step guides

**Recommended Approach:**

1. Run `./run_all_tests.sh` once to see everything work
2. Run individual part scripts to capture screenshots
3. Use manual commands for detailed investigation
4. Refer to guides when you need specific information

Good luck with your testing! 🚀

---

**Questions?** Check the documentation files or review the test script source code - they're heavily commented with explanations.
