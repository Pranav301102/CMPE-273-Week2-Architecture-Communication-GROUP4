#!/usr/bin/env python3
"""
Part B: Comprehensive test runner for all RabbitMQ async tests.
This script runs all three test scenarios and generates a report.

Usage: docker compose run --rm tests python run_all_tests.py
"""
import os
import sys
import time
import subprocess
from datetime import datetime


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def print_section(title):
    """Print a section header"""
    print("\n" + "-" * 80)
    print(f" {title}")
    print("-" * 80)


def run_test(script_name, description):
    """Run a test script and capture result"""
    print_section(f"Running: {description}")
    print(f"Script: {script_name}\n")

    start_time = time.time()
    try:
        result = subprocess.run(
            ["python", script_name],
            capture_output=False,
            text=True,
            timeout=120
        )
        duration = time.time() - start_time
        success = result.returncode == 0

        print(f"\n✓ Test completed in {duration:.2f}s" if success else f"\n✗ Test failed after {duration:.2f}s")
        return success, duration
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"\n✗ Test timed out after {duration:.2f}s")
        return False, duration
    except Exception as e:
        duration = time.time() - start_time
        print(f"\n✗ Test error: {e}")
        return False, duration


def main():
    print_header("PART B: Async RabbitMQ - Comprehensive Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {}

    # Test 1: Idempotency
    print_header("TEST 1: IDEMPOTENCY CHECK")
    print("""
    This test verifies that duplicate messages are not processed twice.
    It publishes the same OrderPlaced event twice with the same order_id.

    Expected behavior:
    - First message: Inventory reserves the item
    - Second message: Inventory detects duplicate and skips processing
    - Check inventory_service logs for "Idempotent skip" message
    """)

    input("Press Enter to run idempotency test...")
    success, duration = run_test("run_idempotency_check.py", "Idempotency Check")
    results['idempotency'] = {'success': success, 'duration': duration}

    print("\nTo verify idempotency:")
    print("  docker compose logs inventory_service | grep idempotency-test-order-1")
    print("  Look for 'Idempotent skip' message on second delivery")

    time.sleep(3)

    # Test 2: Dead Letter Queue
    print_header("TEST 2: DEAD LETTER QUEUE (DLQ)")
    print("""
    This test demonstrates poison message handling.
    It publishes a malformed (invalid JSON) message to the queue.

    Expected behavior:
    - Message cannot be parsed
    - Inventory service rejects (nack) the message
    - Message is routed to Dead Letter Queue (order_placed_dlq)
    - System continues processing valid messages
    """)

    input("Press Enter to run DLQ test...")
    success, duration = run_test("run_dlq_demo.py", "Dead Letter Queue Demo")
    results['dlq'] = {'success': success, 'duration': duration}

    print("\nTo verify DLQ:")
    print("  docker compose exec rabbitmq rabbitmqctl list_queues name messages")
    print("  Or check RabbitMQ Management UI: http://localhost:15672")
    print("  Look for 'order_placed_dlq' queue with 1 message")

    time.sleep(3)

    # Test 3: Backlog and Recovery
    print_header("TEST 3: BACKLOG AND RECOVERY")
    print("""
    This test demonstrates resilience during service outages.

    IMPORTANT: This test requires manual intervention!

    Steps:
    1. The script will POST orders every 1 second for 90 seconds
    2. After ~10 orders, you need to STOP the inventory service:
       docker compose stop inventory_service
    3. Let orders accumulate for ~60 seconds
    4. RESTART the inventory service:
       docker compose start inventory_service
    5. Watch the backlog drain:
       docker compose logs -f inventory_service

    Expected behavior:
    - Orders continue to be accepted even when Inventory is down
    - Messages queue in RabbitMQ (no message loss)
    - When Inventory restarts, all queued messages are processed
    - OrderService remains available throughout
    """)

    print("\nIMPORTANT INSTRUCTIONS:")
    print("1. After starting this test, wait for ~10 orders")
    print("2. In ANOTHER terminal, run:")
    print("     docker compose stop inventory_service")
    print("3. Wait 60 seconds while orders accumulate")
    print("4. Then run:")
    print("     docker compose start inventory_service")
    print("5. In a THIRD terminal, watch logs:")
    print("     docker compose logs -f inventory_service")
    print("\nThe test will run for 90 seconds total.")

    input("\nPress Enter when ready to start backlog test...")
    success, duration = run_test("run_backlog_recovery.py", "Backlog and Recovery")
    results['backlog'] = {'success': success, 'duration': duration}

    print("\nTo verify backlog recovery:")
    print("  - Check that all orders were eventually processed")
    print("  - No orders should be lost during outage")
    print("  - RabbitMQ queue should be empty after recovery")

    # Generate final report
    print_header("TEST RESULTS SUMMARY")

    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r['success'])

    print(f"Tests Run: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}\n")

    print("Detailed Results:")
    print("-" * 80)

    test_names = {
        'idempotency': 'Idempotency Check',
        'dlq': 'Dead Letter Queue',
        'backlog': 'Backlog & Recovery'
    }

    for key, result in results.items():
        status = "✓ PASSED" if result['success'] else "✗ FAILED"
        print(f"{test_names[key]:<30} {status:>15} ({result['duration']:.2f}s)")

    print("-" * 80)

    # Save report to file
    report_path = "/tmp/rabbitmq_test_report.txt"
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PART B: Async RabbitMQ - Test Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"Tests Run: {total_tests}\n")
        f.write(f"Passed: {passed_tests}\n")
        f.write(f"Failed: {total_tests - passed_tests}\n\n")
        f.write("Detailed Results:\n")
        f.write("-" * 80 + "\n")
        for key, result in results.items():
            status = "PASSED" if result['success'] else "FAILED"
            f.write(f"{test_names[key]:<30} {status:>15} ({result['duration']:.2f}s)\n")
        f.write("-" * 80 + "\n")

    print(f"\nReport saved to: {report_path}")

    # Print submission checklist
    print_header("SUBMISSION CHECKLIST")
    print("""
    For Part B submission, ensure you have:

    ✓ Screenshots or logs showing:
      - Backlog accumulation (orders being posted while Inventory is down)
      - Backlog recovery (Inventory processing queued messages after restart)

    ✓ Logs demonstrating idempotency:
      - Show the same order_id being processed once
      - Show "Idempotent skip" message on duplicate delivery

    ✓ Evidence of DLQ handling:
      - RabbitMQ Management UI screenshot showing order_placed_dlq queue
      - Or output from: docker compose exec rabbitmq rabbitmqctl list_queues

    ✓ Written explanation:
      - How idempotency is implemented (order_id tracking in memory/database)
      - Why async messaging prevents cascading failures
      - Benefits of DLQ for poison message handling
    """)

    print("\nAll tests completed!")
    print("=" * 80)

    return 0 if all(r['success'] for r in results.values()) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\nTest suite interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nTest suite error: {e}")
        sys.exit(1)
