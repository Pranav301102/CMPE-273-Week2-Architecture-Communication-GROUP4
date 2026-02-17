#!/bin/bash
# Part A: Automated testing script for Synchronous REST
# This script runs all test scenarios automatically

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/sync-rest"

echo "================================================================================"
echo " PART A: Synchronous REST - Automated Test Runner"
echo "================================================================================"
echo ""

# Function to update docker-compose.yml
update_config() {
    local delay=$1
    local fail_mode=$2
    echo "Updating configuration: DELAY_SEC=$delay, FAIL_MODE=$fail_mode"

    # Use sed to update the environment variables
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/- DELAY_SEC=.*/- DELAY_SEC=$delay/" docker-compose.yml
        sed -i '' "s/- FAIL_MODE=.*/- FAIL_MODE=$fail_mode/" docker-compose.yml
    else
        # Linux
        sed -i "s/- DELAY_SEC=.*/- DELAY_SEC=$delay/" docker-compose.yml
        sed -i "s/- FAIL_MODE=.*/- FAIL_MODE=$fail_mode/" docker-compose.yml
    fi
}

# Function to restart services
restart_services() {
    echo "Restarting services..."
    docker compose up --build -d
    echo "Waiting for services to be ready..."
    sleep 5
}

# Function to run test
run_test() {
    local test_name=$1
    echo ""
    echo "--------------------------------------------------------------------------------"
    echo " Running: $test_name"
    echo "--------------------------------------------------------------------------------"
    docker compose run --rm tests
    echo ""
    echo "Test completed: $test_name"
    echo ""
}

# Cleanup function
cleanup() {
    echo "Cleaning up..."
    docker compose down
}

# Set trap to cleanup on exit
trap cleanup EXIT

echo "This script will run 4 test scenarios:"
echo "  1. Baseline (no delay, no failures)"
echo "  2. With 2s delay in Inventory"
echo "  3. With always-fail mode in Inventory"
echo "  4. With timeout (2s delay, 1s timeout)"
echo ""
read -p "Press Enter to start testing..."

# Array to store results
declare -a results

# Test 1: Baseline
echo ""
echo "================================================================================"
echo " TEST 1: Baseline (Normal Operation)"
echo "================================================================================"
update_config 0 "none"
restart_services
run_test "Baseline"
results+=("Baseline test completed")

# Test 2: With 2s delay
echo ""
echo "================================================================================"
echo " TEST 2: With 2-second Delay in Inventory"
echo "================================================================================"
update_config 2 "none"
restart_services
run_test "2-second Delay"
results+=("2s delay test completed")

# Test 3: Always fail
echo ""
echo "================================================================================"
echo " TEST 3: Always Fail Mode"
echo "================================================================================"
update_config 0 "always"
restart_services
run_test "Always Fail"
results+=("Always fail test completed")

# Test 4: Timeout scenario
echo ""
echo "================================================================================"
echo " TEST 4: Timeout Scenario (2s delay with 1s timeout)"
echo "================================================================================"
update_config 2 "none"
# Note: OrderService already has INVENTORY_TIMEOUT_SEC=1.0
restart_services
run_test "Timeout Scenario"
results+=("Timeout test completed")

# Reset to baseline
echo ""
echo "Resetting to baseline configuration..."
update_config 0 "none"

# Print summary
echo ""
echo "================================================================================"
echo " TEST SUMMARY"
echo "================================================================================"
for result in "${results[@]}"; do
    echo "  ✓ $result"
done
echo ""
echo "All Part A tests completed!"
echo ""
echo "Next steps:"
echo "  1. Review the test outputs above"
echo "  2. Create a latency comparison table"
echo "  3. Check logs: docker compose logs order_service"
echo "  4. Take screenshots for your submission"
echo ""
echo "To view detailed analysis, check:"
echo "  docker compose run --rm tests python run_all_scenarios.py"
echo ""
echo "================================================================================"
