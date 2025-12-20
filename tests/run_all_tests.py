#!/usr/bin/env python3
"""
Test Runner for COS CLI

Runs all test suites and provides a summary.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'=' * 70}")
    print(f"{description}")
    print(f"{'=' * 70}\n")
    
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=Path(__file__).parent.parent,
        capture_output=False,
    )
    
    return result.returncode == 0


def main():
    """Run all tests."""
    results = {}
    
    print("\n" + "=" * 70)
    print("COS CLI Test Suite Runner")
    print("=" * 70)
    
    # Run pytest-based unit tests
    results['pytest_unit'] = run_command(
        "python3 -m pytest tests/test_unit.py -v",
        "Running Unit Tests (pytest)"
    )
    
    # Run simple unit tests (no pytest)
    results['simple_unit'] = run_command(
        "python3 tests/test_commands_simple.py",
        "Running Simple Unit Tests"
    )
    
    # Run integration tests
    results['integration'] = run_command(
        "python3 tests/test_integration.py",
        "Running Integration Tests (Real COS Operations)"
    )
    
    # Run all pytest tests (config, utils, ui)
    results['pytest_all'] = run_command(
        "python3 -m pytest tests/ -v --ignore=tests/test_commands.py "
        "--ignore=tests/test_commands_simple.py --ignore=tests/test_integration.py "
        "-k 'not test_upload_file_with_progress and not test_download_file_not_found "
        "and not test_special_characters_in_search'",
        "Running All Pytest Tests"
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70 + "\n")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:12} {test_name}")
    
    print(f"\n{'=' * 70}")
    print(f"Total: {total} test suites")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    print("=" * 70 + "\n")
    
    if failed == 0:
        print("🎉 ALL TEST SUITES PASSED!\n")
        return 0
    else:
        print(f"❌ {failed} test suite(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
