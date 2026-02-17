#!/bin/bash
# Part B: Testing script for Async RabbitMQ
# This script guides you through all Part B tests

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/async-rabbitmq"

echo "================================================================================"
echo " PART B: Async RabbitMQ - Test Runner"
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

echo "Starting RabbitMQ and services..."
docker compose up --build -d

echo "Waiting for RabbitMQ to be ready..."
sleep 15

echo ""
echo "Services started. Checking status..."
docker compose ps
echo ""

# Test 1: Idempotency
echo ""
echo "================================================================================"
echo " TEST 1: Idempotency Check"
echo "================================================================================"
echo ""
echo "This test publishes the same order twice to verify idempotent processing."
echo ""
read -p "Press Enter to run idempotency test..."

docker compose run --rm tests python run_idempotency_check.py

echo ""
echo "Checking inventory logs for idempotency evidence..."
docker compose logs inventory_service | grep "idempotency-test-order-1" || echo "No logs found (might be processed already)"

echo ""
read -p "Press Enter to continue to next test..."

# Test 2: DLQ
echo ""
echo "================================================================================"
echo " TEST 2: Dead Letter Queue (DLQ)"
echo "================================================================================"
echo ""
echo "This test publishes a malformed message to demonstrate poison message handling."
echo ""
read -p "Press Enter to run DLQ test..."

docker compose run --rm tests python run_dlq_demo.py

echo ""
echo "Checking RabbitMQ queues..."
docker compose exec rabbitmq rabbitmqctl list_queues name messages

echo ""
echo "You can also check the RabbitMQ Management UI:"
echo "  URL: http://localhost:15672"
echo "  Username: guest"
echo "  Password: guest"
echo "  Look for 'order_placed_dlq' queue"
echo ""
read -p "Press Enter to continue to next test..."

# Test 3: Backlog and Recovery
echo ""
echo "================================================================================"
echo " TEST 3: Backlog and Recovery"
echo "================================================================================"
echo ""
echo "This test demonstrates resilience during service outages."
echo ""
echo "IMPORTANT INSTRUCTIONS:"
echo "  1. The test will POST orders every 1 second for 90 seconds"
echo "  2. After ~10 orders, you need to STOP inventory_service:"
echo "       docker compose stop inventory_service"
echo "  3. Wait ~60 seconds while orders accumulate"
echo "  4. RESTART inventory_service:"
echo "       docker compose start inventory_service"
echo "  5. Watch the backlog drain (in another terminal):"
echo "       docker compose logs -f inventory_service"
echo ""
echo "The test will start now. Open another terminal window to control inventory_service."
echo ""
read -p "Press Enter to start backlog test..."

# Run backlog test in background and monitor
echo ""
echo "Starting backlog test (will run for 90 seconds)..."
echo "REMEMBER: Stop inventory_service after ~10 seconds, wait 60s, then restart!"
echo ""

docker compose run --rm tests python run_backlog_recovery.py

echo ""
echo "Backlog test completed!"
echo ""
echo "Verify recovery by checking:"
echo "  1. docker compose logs inventory_service | tail -50"
echo "  2. docker compose exec rabbitmq rabbitmqctl list_queues name messages"
echo "  3. All orders should have been processed (queue should be empty)"
echo ""

# Summary
echo ""
echo "================================================================================"
echo " TEST SUMMARY"
echo "================================================================================"
echo ""
echo "✓ Idempotency test completed"
echo "✓ DLQ test completed"
echo "✓ Backlog and recovery test completed"
echo ""
echo "Verification steps:"
echo ""
echo "1. Idempotency:"
echo "   docker compose logs inventory_service | grep 'Idempotent skip'"
echo ""
echo "2. DLQ:"
echo "   docker compose exec rabbitmq rabbitmqctl list_queues name messages"
echo "   (Look for order_placed_dlq queue)"
echo ""
echo "3. Backlog Recovery:"
echo "   docker compose logs inventory_service | grep 'Processing order'"
echo "   (Should show all queued orders being processed after restart)"
echo ""
echo "RabbitMQ Management UI:"
echo "   http://localhost:15672 (guest/guest)"
echo ""
echo "For submission, capture:"
echo "  - Screenshots of backlog accumulation and recovery"
echo "  - Logs showing idempotent behavior"
echo "  - Evidence of DLQ (queue listing or Management UI screenshot)"
echo ""
echo "================================================================================"
