#!/bin/bash
# Master test runner for all three parts
# This script runs all tests sequentially

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "================================================================================"
echo " CMPE 273 - Communication Models Lab"
echo " Master Test Runner"
echo "================================================================================"
echo ""
echo "This script will run ALL tests for all three parts:"
echo "  - Part A: Synchronous REST"
echo "  - Part B: Async RabbitMQ"
echo "  - Part C: Streaming Kafka"
echo ""
echo "Estimated total time: ~15-20 minutes"
echo ""
read -p "Do you want to continue? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "Test run cancelled."
    exit 0
fi

# Create results directory
RESULTS_DIR="$SCRIPT_DIR/test_results"
mkdir -p "$RESULTS_DIR"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_FILE="$RESULTS_DIR/test_results_$TIMESTAMP.txt"

# Function to log results
log_result() {
    echo "$1" | tee -a "$RESULTS_FILE"
}

# Start logging
log_result "================================================================================"
log_result " CMPE 273 - Test Results"
log_result " Date: $(date)"
log_result "================================================================================"
log_result ""

# Part A
echo ""
echo "################################################################################"
echo "# PART A: Synchronous REST"
echo "################################################################################"
echo ""

log_result "PART A: Synchronous REST"
log_result "----------------------------------------"

if ./test_part_a.sh 2>&1 | tee -a "$RESULTS_FILE"; then
    log_result "✓ Part A completed successfully"
    PART_A_SUCCESS=true
else
    log_result "✗ Part A had errors"
    PART_A_SUCCESS=false
fi

log_result ""

# Wait between parts
echo ""
echo "Part A completed. Waiting 5 seconds before Part B..."
sleep 5

# Part B
echo ""
echo "################################################################################"
echo "# PART B: Async RabbitMQ"
echo "################################################################################"
echo ""

log_result "PART B: Async RabbitMQ"
log_result "----------------------------------------"

if ./test_part_b.sh 2>&1 | tee -a "$RESULTS_FILE"; then
    log_result "✓ Part B completed successfully"
    PART_B_SUCCESS=true
else
    log_result "✗ Part B had errors"
    PART_B_SUCCESS=false
fi

log_result ""

# Wait between parts
echo ""
echo "Part B completed. Waiting 5 seconds before Part C..."
sleep 5

# Part C
echo ""
echo "################################################################################"
echo "# PART C: Streaming Kafka"
echo "################################################################################"
echo ""

log_result "PART C: Streaming Kafka"
log_result "----------------------------------------"

if ./test_part_c.sh 2>&1 | tee -a "$RESULTS_FILE"; then
    log_result "✓ Part C completed successfully"
    PART_C_SUCCESS=true
else
    log_result "✗ Part C had errors"
    PART_C_SUCCESS=false
fi

log_result ""

# Final Summary
echo ""
echo "================================================================================"
echo " FINAL TEST SUMMARY"
echo "================================================================================"
echo ""

log_result "================================================================================"
log_result " FINAL TEST SUMMARY"
log_result "================================================================================"
log_result ""

if [ "$PART_A_SUCCESS" = true ]; then
    log_result "✓ Part A: Synchronous REST - PASSED"
else
    log_result "✗ Part A: Synchronous REST - FAILED"
fi

if [ "$PART_B_SUCCESS" = true ]; then
    log_result "✓ Part B: Async RabbitMQ - PASSED"
else
    log_result "✗ Part B: Async RabbitMQ - FAILED"
fi

if [ "$PART_C_SUCCESS" = true ]; then
    log_result "✓ Part C: Streaming Kafka - PASSED"
else
    log_result "✗ Part C: Streaming Kafka - FAILED"
fi

log_result ""
log_result "Test results saved to: $RESULTS_FILE"
log_result "================================================================================"

echo ""
echo "All tests completed!"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""
echo "Next steps for submission:"
echo "  1. Review all test outputs"
echo "  2. Collect screenshots from each part"
echo "  3. Create latency comparison tables (Part A)"
echo "  4. Document idempotency strategy (Part B)"
echo "  5. Include metrics reports (Part C)"
echo ""
echo "For detailed information, see:"
echo "  - README_TESTING.md - Test script documentation"
echo "  - TESTING_GUIDE.md - Comprehensive testing guide"
echo ""
echo "================================================================================"

# Check if all tests passed
if [ "$PART_A_SUCCESS" = true ] && [ "$PART_B_SUCCESS" = true ] && [ "$PART_C_SUCCESS" = true ]; then
    echo "🎉 All tests PASSED! Great job!"
    exit 0
else
    echo "⚠️  Some tests had issues. Please review the results."
    exit 1
fi
