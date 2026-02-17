#!/usr/bin/env python3
"""
Part A: Comprehensive test runner for all Synchronous REST scenarios.
This script runs all test scenarios and generates a comparison report.

Usage: docker compose run --rm tests python run_all_scenarios.py

Note: This script expects to run INSIDE the tests container where it can
call the latency test multiple times. The different scenarios need to be
configured in docker-compose.yml BEFORE starting this script.
"""
import os
import time
import statistics
import requests
import uuid
from datetime import datetime


ORDER_URL = os.getenv("ORDER_URL", "http://order_service:8000")
N = 50


def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def print_section(title):
    """Print a section header"""
    print("\n" + "-" * 80)
    print(f" {title}")
    print("-" * 80 + "\n")


def wait_for_service(url, timeout=30, service_name="service"):
    """Wait for a service to be available"""
    print(f"Waiting for {service_name} at {url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(f"{url}/health", timeout=2)
            if r.status_code == 200:
                print(f"✓ {service_name} is ready")
                return True
        except:
            pass
        time.sleep(1)
    print(f"✗ {service_name} not ready after {timeout}s")
    return False


def do_orders(n: int, test_name="test"):
    """Send N orders and measure latency"""
    print(f"Sending {n} orders for {test_name}...")
    latencies = []
    status_codes = {}
    errors = []

    for i in range(n):
        order_id = str(uuid.uuid4())
        t0 = time.perf_counter()

        try:
            r = requests.post(
                f"{ORDER_URL}/order",
                json={
                    "order_id": order_id,
                    "item_id": "burrito",
                    "qty": 1,
                    "user_id": "u123"
                },
                timeout=5
            )
            dt = (time.perf_counter() - t0) * 1000
            latencies.append(dt)

            # Track status codes
            status_codes[r.status_code] = status_codes.get(r.status_code, 0) + 1

            if r.status_code != 200:
                errors.append(f"Order {i+1}: {r.status_code} - {r.text[:50]}")

        except requests.exceptions.Timeout:
            dt = (time.perf_counter() - t0) * 1000
            latencies.append(dt)
            status_codes['TIMEOUT'] = status_codes.get('TIMEOUT', 0) + 1
            errors.append(f"Order {i+1}: Timeout")
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000
            latencies.append(dt)
            status_codes['ERROR'] = status_codes.get('ERROR', 0) + 1
            errors.append(f"Order {i+1}: {str(e)[:50]}")

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{n} requests sent")

    return latencies, status_codes, errors


def summarize(name, arr, status_codes, errors):
    """Summarize latency results"""
    if not arr:
        return {
            "case": name,
            "n": 0,
            "p50_ms": 0,
            "p95_ms": 0,
            "avg_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "status_codes": status_codes,
            "error_count": len(errors)
        }

    sorted_arr = sorted(arr)
    return {
        "case": name,
        "n": len(arr),
        "p50_ms": round(statistics.median(arr), 2),
        "p95_ms": round(sorted_arr[int(0.95 * len(arr)) - 1], 2) if len(arr) > 1 else round(arr[0], 2),
        "avg_ms": round(statistics.mean(arr), 2),
        "min_ms": round(min(arr), 2),
        "max_ms": round(max(arr), 2),
        "status_codes": status_codes,
        "error_count": len(errors)
    }


def print_results_table(results):
    """Print results in a formatted table"""
    print("\nLATENCY COMPARISON TABLE")
    print("=" * 100)
    print(f"{'Scenario':<25} {'n':>5} {'p50(ms)':>10} {'p95(ms)':>10} {'avg(ms)':>10} {'min(ms)':>10} {'max(ms)':>10}")
    print("-" * 100)

    for result in results:
        print(f"{result['case']:<25} {result['n']:>5} {result['p50_ms']:>10.2f} "
              f"{result['p95_ms']:>10.2f} {result['avg_ms']:>10.2f} "
              f"{result['min_ms']:>10.2f} {result['max_ms']:>10.2f}")

    print("=" * 100)


def print_status_summary(results):
    """Print status code summary"""
    print("\nSTATUS CODE SUMMARY")
    print("=" * 60)

    for result in results:
        print(f"\n{result['case']}:")
        for code, count in result['status_codes'].items():
            print(f"  {code}: {count} requests")
        if result['error_count'] > 0:
            print(f"  Total errors: {result['error_count']}")

    print("=" * 60)


def main():
    print_header("PART A: Synchronous REST - Comprehensive Test Suite")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Order Service URL: {ORDER_URL}")
    print(f"Requests per scenario: {N}")

    # Wait for OrderService to be ready
    if not wait_for_service(ORDER_URL, service_name="OrderService"):
        print("ERROR: OrderService not available")
        return 1

    print("\n" + "=" * 80)
    print(" IMPORTANT: Test Configuration")
    print("=" * 80)
    print("""
This script runs tests with the CURRENT configuration of docker-compose.yml.

For comprehensive testing, you should run this script multiple times with
different configurations:

1. BASELINE (Normal operation):
   inventory_service:
     environment:
       - DELAY_SEC=0
       - FAIL_MODE=none

2. WITH 2s DELAY:
   inventory_service:
     environment:
       - DELAY_SEC=2
       - FAIL_MODE=none

3. ALWAYS FAIL:
   inventory_service:
     environment:
       - DELAY_SEC=0
       - FAIL_MODE=always

4. TIMEOUT SCENARIO:
   inventory_service:
     environment:
       - DELAY_SEC=2
       - FAIL_MODE=none
   order_service:
     environment:
       - INVENTORY_TIMEOUT_SEC=1.0

Current configuration will be used for this test run.
    """)

    input("Press Enter to start testing with current configuration...")

    # Run the test with current configuration
    print_section("Running Test with Current Configuration")
    latencies, status_codes, errors = do_orders(N, "current-config")
    result = summarize("Current Configuration", latencies, status_codes, errors)

    # Print results
    print_section("Test Results")
    print_results_table([result])
    print_status_summary([result])

    # Print sample errors if any
    if errors:
        print_section("Sample Errors (first 5)")
        for error in errors[:5]:
            print(f"  {error}")

    # Generate CSV for easy import
    print_section("CSV Output (for spreadsheet)")
    print("scenario,n,p50_ms,p95_ms,avg_ms,min_ms,max_ms")
    print(f"{result['case']},{result['n']},{result['p50_ms']},{result['p95_ms']},"
          f"{result['avg_ms']},{result['min_ms']},{result['max_ms']}")

    # Analysis
    print_section("Analysis")

    if result['avg_ms'] < 10:
        print("✓ Low latency - services are responding quickly")
        print("  This indicates normal operation with minimal delays")
    elif result['avg_ms'] < 100:
        print("⚠ Moderate latency - some delay in the system")
        print("  Check if downstream services have delays configured")
    elif result['avg_ms'] < 2000:
        print("⚠ High latency - significant delays detected")
        print("  This could indicate:")
        print("  - Inventory service has DELAY_SEC configured")
        print("  - Network latency between services")
        print("  - Service is under load")
    else:
        print("✗ Very high latency - system is struggling")
        print("  This indicates serious performance issues")

    success_rate = result['status_codes'].get(200, 0) / result['n'] * 100 if result['n'] > 0 else 0
    print(f"\nSuccess rate: {success_rate:.1f}%")

    if success_rate == 100:
        print("✓ All requests successful")
    elif success_rate > 90:
        print("⚠ Some failures detected - check error logs")
    else:
        print("✗ High failure rate - indicates system issues")

    # Save report
    report_path = "/tmp/sync_rest_test_report.txt"
    with open(report_path, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PART A: Synchronous REST - Test Report\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Requests: {result['n']}\n\n")
        f.write("Latency Metrics:\n")
        f.write(f"  p50: {result['p50_ms']:.2f}ms\n")
        f.write(f"  p95: {result['p95_ms']:.2f}ms\n")
        f.write(f"  avg: {result['avg_ms']:.2f}ms\n")
        f.write(f"  min: {result['min_ms']:.2f}ms\n")
        f.write(f"  max: {result['max_ms']:.2f}ms\n\n")
        f.write("Status Codes:\n")
        for code, count in result['status_codes'].items():
            f.write(f"  {code}: {count}\n")
        f.write("\n")

    print(f"\n✓ Report saved to: {report_path}")

    print_header("Test Complete!")
    print("""
To run all scenarios, modify docker-compose.yml and run this script again:

1. Test baseline (no delay, no failure)
2. Test with 2s delay (DELAY_SEC=2)
3. Test with failures (FAIL_MODE=always)
4. Test timeout (DELAY_SEC=2 with INVENTORY_TIMEOUT_SEC=1.0)

Then compare the results to see how synchronous coupling affects latency!
    """)

    return 0


if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n\nTest error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
