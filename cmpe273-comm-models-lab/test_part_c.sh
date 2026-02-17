#!/bin/bash
# Part C: Testing script for Streaming Kafka
# This script runs all Kafka streaming tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/streaming-kafka"

echo "================================================================================"
echo " PART C: Streaming Kafka - Test Runner"
echo "================================================================================"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    docker compose down -v
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo "Starting Kafka, Zookeeper, and services..."
docker compose up --build -d

echo ""
echo "Waiting for Kafka to be ready (this takes ~30 seconds)..."
echo ""

# Wait for Kafka with progress indicator
for i in {1..30}; do
    echo -n "."
    sleep 1
done
echo ""

# Check if Kafka is ready
echo "Checking Kafka status..."
if docker compose logs kafka | grep -q "started"; then
    echo "✓ Kafka is ready"
else
    echo "⚠ Kafka might still be starting. Waiting 10 more seconds..."
    sleep 10
fi

echo ""
echo "Services started. Checking status..."
docker compose ps
echo ""

echo "Waiting for consumers to initialize..."
sleep 5

# Send a test order to verify system is working
echo ""
echo "Sending a test order to verify system..."
curl -X POST http://localhost:5001/order \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test_user", "item": "pizza", "quantity": 1}' \
  --silent || echo "Service might not be ready yet"

echo ""
echo "Waiting for event processing..."
sleep 3

# Run comprehensive tests
echo ""
echo "================================================================================"
echo " Running Comprehensive Test Suite"
echo "================================================================================"
echo ""
echo "This will run 4 tests:"
echo "  1. Baseline Latency (100 requests)"
echo "  2. 10K Events Throughput"
echo "  3. Consumer Lag Measurement"
echo "  4. Replay with Offset Reset"
echo ""
read -p "Press Enter to start testing..."

docker compose run --rm tests

echo ""
echo "================================================================================"
echo " Viewing Analytics Metrics"
echo "================================================================================"
echo ""
echo "The analytics consumer computes metrics every 30 seconds."
echo "Let's view the latest metrics..."
echo ""

docker compose logs analytics_consumer | tail -30

# Optional: Send more orders for demonstration
echo ""
echo "================================================================================"
echo " Additional Verification (Optional)"
echo "================================================================================"
echo ""
read -p "Do you want to send 20 more test orders? (y/N): " send_more

if [[ $send_more =~ ^[Yy]$ ]]; then
    echo ""
    echo "Sending 20 orders..."
    for i in {1..20}; do
        curl -X POST http://localhost:5001/order \
          -H "Content-Type: application/json" \
          -d "{\"user_id\": \"user_$i\", \"item\": \"burger\", \"quantity\": $(($RANDOM % 3 + 1))}" \
          --silent > /dev/null
        echo "  Order $i sent"
        sleep 0.5
    done
    echo ""
    echo "Waiting for processing..."
    sleep 5
    echo ""
    echo "Latest analytics:"
    docker compose logs analytics_consumer | tail -20
fi

# Show consumer groups
echo ""
echo "================================================================================"
echo " Kafka Consumer Groups"
echo "================================================================================"
echo ""
echo "Checking consumer group status..."
docker compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe --group analytics-service 2>/dev/null || echo "Consumer group not found or still initializing"

# Show topics
echo ""
echo "Kafka Topics:"
docker compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list

# Offer to show replay demonstration
echo ""
echo "================================================================================"
echo " Manual Replay Demonstration (Optional)"
echo "================================================================================"
echo ""
read -p "Do you want to see a manual replay demonstration? (y/N): " do_replay

if [[ $do_replay =~ ^[Yy]$ ]]; then
    echo ""
    echo "Step 1: Checking current consumer offset..."
    docker compose exec kafka kafka-consumer-groups \
      --bootstrap-server localhost:9092 \
      --describe --group analytics-service

    echo ""
    echo "Step 2: Resetting offset to earliest..."
    docker compose exec kafka kafka-consumer-groups \
      --bootstrap-server localhost:9092 \
      --group analytics-service \
      --topic inventory-events \
      --reset-offsets --to-earliest --execute

    echo ""
    echo "Step 3: Restarting analytics consumer to replay events..."
    docker compose restart analytics_consumer

    echo ""
    echo "Waiting for replay to process..."
    sleep 10

    echo ""
    echo "Replayed metrics:"
    docker compose logs analytics_consumer | tail -30
fi

# Summary
echo ""
echo "================================================================================"
echo " TEST SUMMARY"
echo "================================================================================"
echo ""
echo "✓ Baseline latency test completed"
echo "✓ 10K events throughput test completed"
echo "✓ Consumer lag measurement completed"
echo "✓ Replay test completed"
echo ""
echo "Test report saved to: /tmp/kafka_test_report.txt"
echo "  (Inside the tests container)"
echo ""
echo "Verification:"
echo ""
echo "1. View producer logs:"
echo "   docker compose logs producer_order | tail -50"
echo ""
echo "2. View inventory consumer logs:"
echo "   docker compose logs inventory_consumer | tail -50"
echo ""
echo "3. View analytics consumer logs:"
echo "   docker compose logs analytics_consumer | tail -50"
echo ""
echo "4. Check Kafka topics:"
echo "   docker compose exec kafka kafka-topics --list --bootstrap-server localhost:9092"
echo ""
echo "5. Monitor in real-time:"
echo "   docker compose logs -f analytics_consumer"
echo ""
echo "For submission, include:"
echo "  - Test report output showing all 4 test results"
echo "  - Screenshots of analytics metrics"
echo "  - Evidence of replay (before/after offset reset)"
echo "  - Throughput numbers from 10K events test"
echo ""
echo "================================================================================"
