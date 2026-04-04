"""
Test Runner for Authentication Flow E2E Tests

This script runs all authentication flow tests and generates a comprehensive report.

Usage:
    python run_tests.py [--verbose] [--browser] [--manual]

Options:
    --verbose: Show detailed output
    --browser: Include browser-based tests
    --manual: Run manual test only
"""

import sys
import subprocess
import argparse
from datetime import datetime
import json


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\nChecking dependencies...")

    dependencies = {
        "requests": False,
        "pytest": False,
        "jwt": False,
        "selenium": False,
        "playwright": False,
    }

    for dep in dependencies.keys():
        try:
            if dep == "jwt":
                import PyJWT
            else:
                __import__(dep)
            dependencies[dep] = True
            print(f"  - {dep:12} INSTALLED")
        except ImportError:
            print(f"  - {dep:12} NOT INSTALLED")

    return dependencies


def check_services():
    """Check if backend and frontend services are running."""
    import requests

    print("\nChecking services...")

    services = {
        "Backend": "http://localhost:8000/health",
        "Frontend": "http://localhost:5173",
    }

    status = {}

    for name, url in services.items():
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                status[name] = "RUNNING"
                print(f"  - {name:10} RUNNING")
            else:
                status[name] = "ERROR"
                print(f"  - {name:10} ERROR (status {response.status_code})")
        except requests.exceptions.ConnectionError:
            status[name] = "NOT RUNNING"
            print(f"  - {name:10} NOT RUNNING")
        except Exception as e:
            status[name] = "ERROR"
            print(f"  - {name:10} ERROR ({str(e)})")

    return status


def run_manual_tests():
    """Run manual tests from test_auth_flow.py."""
    print("\n" + "=" * 70)
    print("RUNNING MANUAL TESTS")
    print("=" * 70)

    try:
        from test_auth_flow import run_manual_test
        run_manual_test()
        return True
    except Exception as e:
        print(f"\n ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_pytest_tests(verbose=False, browser=False):
    """Run pytest tests."""
    print("\n" + "=" * 70)
    print("RUNNING PYTEST TESTS")
    print("=" * 70)

    cmd = ["pytest"]

    # Add test files
    cmd.append("test_auth_flow.py")
    if browser:
        cmd.append("test_auth_flow_browser.py")

    # Add options
    if verbose:
        cmd.append("-v")
        cmd.append("-s")  # Show print statements

    cmd.append("--tb=short")  # Short traceback format

    # Run pytest
    try:
        result = subprocess.run(cmd, cwd=".", capture_output=False)
        return result.returncode == 0
    except Exception as e:
        print(f"\n ERROR running pytest: {str(e)}")
        return False


def generate_report(deps, services, test_results):
    """Generate test execution report."""
    print("\n" + "=" * 70)
    print("TEST EXECUTION REPORT")
    print("=" * 70)

    # Timestamp
    print(f"\nExecution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Dependencies
    print("\nDependencies:")
    for dep, installed in deps.items():
        status = "INSTALLED" if installed else "NOT INSTALLED"
        print(f"  - {dep:12} {status}")

    # Services
    print("\nServices:")
    for service, status in services.items():
        print(f"  - {service:10} {status}")

    # Test Results
    print("\nTest Results:")
    for test, result in test_results.items():
        status = "PASSED" if result else "FAILED"
        print(f"  - {test:20} {status}")

    # Recommendations
    print("\nRecommendations:")

    if not deps["pytest"]:
        print("  - Install pytest: pip install pytest")

    if not deps["requests"]:
        print("  - Install requests: pip install requests")

    if not deps["jwt"]:
        print("  - Install PyJWT: pip install PyJWT")

    if services["Backend"] != "RUNNING":
        print("  - Start backend: cd orchestrator-ui/backend && uvicorn main:app --reload")

    if services["Frontend"] != "RUNNING":
        print("  - Start frontend: cd orchestrator-ui/frontend && npm run dev")

    if not deps["selenium"] and not deps["playwright"]:
        print("  - For browser tests, install: pip install selenium playwright")

    # Overall Status
    print("\nOverall Status:")
    all_passed = all(test_results.values())
    services_running = all(s == "RUNNING" for s in services.values())

    if all_passed and services_running:
        print("  ALL TESTS PASSED")
    elif all_passed and not services_running:
        print("  TESTS PASSED (but services not running)")
    else:
        print("  SOME TESTS FAILED")

    print("\n" + "=" * 70)


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run E2E auth flow tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-b", "--browser", action="store_true", help="Include browser tests")
    parser.add_argument("-m", "--manual", action="store_true", help="Run manual tests only")
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("E2E AUTHENTICATION FLOW TEST SUITE")
    print("=" * 70)

    # Check dependencies
    deps = check_dependencies()

    # Check services
    services = check_services()

    # Check if we can run tests
    if not deps["requests"]:
        print("\n ERROR: requests library is required")
        print("Install: pip install requests")
        sys.exit(1)

    if services["Backend"] != "RUNNING":
        print("\n WARNING: Backend service is not running")
        print("Tests may fail. Start backend with:")
        print("  cd orchestrator-ui/backend && uvicorn main:app --reload")

    # Run tests
    test_results = {}

    if args.manual:
        # Run only manual tests
        test_results["Manual Tests"] = run_manual_tests()
    else:
        # Run manual tests first
        test_results["Manual Tests"] = run_manual_tests()

        # Run pytest tests if pytest is available
        if deps["pytest"]:
            test_results["Pytest Tests"] = run_pytest_tests(
                verbose=args.verbose,
                browser=args.browser
            )
        else:
            print("\n WARNING: pytest not installed, skipping pytest tests")
            print("Install: pip install pytest")
            test_results["Pytest Tests"] = None

    # Generate report
    generate_report(deps, services, test_results)


if __name__ == "__main__":
    main()
